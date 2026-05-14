from flask import Flask, request, jsonify, send_file
import os
import re
import json
import xml.etree.ElementTree as ET
import stat
import time
import atexit
from io import BytesIO
from datetime import datetime, timedelta
import random
import string
from copy import deepcopy
from threading import Lock
import yaml
from payment_generator import PaymentData, XMLFieldMapper, ACHNachaXMLGenerator
import paramiko
from paramiko import SSHClient, AutoAddPolicy

app = Flask(__name__)

CONNECTION_INFO_FILE = os.path.join(os.path.dirname(__file__), 'connection_info.json')
CONNECTION_PROTOCOLS = ['SFTP', 'SCP', 'FTP', 'WebDAV', 'Amazon S3']
LOGIN_CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'login_credentials.json')
PRESEED_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'file_templates_config.yaml')
WEBSERIES_WIRE_DOM_TEMPLATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'WireDomesticRISKUG.xml'))
WEBSERIES_WIRE_INTL_TEMPLATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'WireInt-Riskug.xml'))
WEBSERIES_WIRE_MAX_BATCHES = 100000
WEBSERIES_WIRE_MAX_PREVIEW_BATCHES = 5000
PAYMENT_FORM_TO_CONFIG_KEY = {
    'ACH NACHA XML': 'ACH_NACHA',
    'ACH CAEFT XML': 'ACH_CAEFT',
    'CHECKS XML': 'CHECKS'
}
DEFAULT_LOGIN_CREDENTIALS = {
    'saasN': {
        'username': '',
        'password': ''
    },
    'saasP': {
        'username': '',
        'password': ''
    }
}
DEFAULT_CONNECTION_INFO = {
    'saasN': {
        'fileProtocol': 'SFTP',
        'hostName': 'pcmqaftp.bottomline.com',
        'portNumber': '2222'
    },
    'saasPNonProd': {
        'fileProtocol': 'SFTP',
        'hostName': 'pcmtestftp.bottomline.com',
        'portNumber': '2222'
    },
    'saasPProd': {
        'fileProtocol': 'SFTP',
        'hostName': 'pcmftp.bottomline.com',
        'portNumber': '2222'
    }
}
_connection_info_lock = Lock()
_sftp_pool_lock = Lock()
_preseed_lock = Lock()
_wire_csv_preview_lock = Lock()
_wire_csv_preview_cache = {}
WIRE_CSV_PREVIEW_TTL_SEC = int(os.environ.get('WIRE_CSV_PREVIEW_TTL_SEC', '600'))
WIRE_CSV_FILE_TYPES = {
    '.CSV Wire Domestic',
    'CSV Wire Domestic',
    '.CSV Wire International',
    'CSV Wire International'
}
_preseed_config_cache = {
    'mtime': None,
    'data': {}
}

# Keep SFTP connections warm for faster directory navigation.
SFTP_SESSION_IDLE_TTL_SEC = int(os.environ.get('SFTP_SESSION_IDLE_TTL_SEC', '180'))
SFTP_DIR_CACHE_TTL_SEC = int(os.environ.get('SFTP_DIR_CACHE_TTL_SEC', '20'))
SFTP_DIR_CACHE_MAX_ENTRIES = int(os.environ.get('SFTP_DIR_CACHE_MAX_ENTRIES', '500'))

_sftp_session_pool = {}
_sftp_directory_cache = {}


def _normalize_remote_path(path_value):
    """Normalize remote SFTP path to stable cache key format."""
    normalized = (path_value or '/').strip()
    if not normalized.startswith('/'):
        normalized = '/' + normalized
    normalized = re.sub(r'/+', '/', normalized)
    return normalized if normalized == '/' else normalized.rstrip('/')


def _sftp_server_key(saas_section, hostname, port, username):
    """Build stable identity for a pooled SFTP session."""
    return f"{saas_section}|{hostname}:{port}|{username}"


def _close_sftp_session_entry(session_entry):
    """Safely close pooled SFTP session resources."""
    if not session_entry:
        return
    sftp_client = session_entry.get('sftp')
    ssh_client = session_entry.get('ssh')
    if sftp_client:
        try:
            sftp_client.close()
        except Exception:
            pass
    if ssh_client:
        try:
            ssh_client.close()
        except Exception:
            pass


def _is_session_alive(session_entry):
    """Validate pooled session health before reuse."""
    if not session_entry:
        return False
    ssh_client = session_entry.get('ssh')
    sftp_client = session_entry.get('sftp')
    if not ssh_client or not sftp_client:
        return False
    transport = ssh_client.get_transport()
    if not transport or not transport.is_active():
        return False
    try:
        channel = sftp_client.get_channel()
        if channel is not None and getattr(channel, 'closed', False):
            return False
    except Exception:
        return False
    return True


def _evict_idle_sftp_sessions(now_ts):
    """Close pooled sessions that have been idle beyond TTL."""
    stale_keys = []
    with _sftp_pool_lock:
        for session_key, session_entry in _sftp_session_pool.items():
            last_used = session_entry.get('last_used', 0)
            if now_ts - last_used > SFTP_SESSION_IDLE_TTL_SEC:
                stale_keys.append(session_key)

        stale_entries = []
        for session_key in stale_keys:
            stale_entries.append(_sftp_session_pool.pop(session_key, None))

    for session_entry in stale_entries:
        _close_sftp_session_entry(session_entry)


def _sweep_directory_cache(now_ts):
    """Drop stale and overflow cache entries."""
    with _sftp_pool_lock:
        stale_keys = [
            cache_key for cache_key, cache_entry in _sftp_directory_cache.items()
            if now_ts - cache_entry.get('ts', 0) > SFTP_DIR_CACHE_TTL_SEC
        ]
        for cache_key in stale_keys:
            _sftp_directory_cache.pop(cache_key, None)

        if len(_sftp_directory_cache) > SFTP_DIR_CACHE_MAX_ENTRIES:
            ordered_items = sorted(_sftp_directory_cache.items(), key=lambda item: item[1].get('ts', 0))
            overflow = len(_sftp_directory_cache) - SFTP_DIR_CACHE_MAX_ENTRIES
            for cache_key, _ in ordered_items[:overflow]:
                _sftp_directory_cache.pop(cache_key, None)


def _read_cached_directory(server_key, remote_path):
    """Return fresh cached directory payload if available."""
    now_ts = time.time()
    cache_key = (server_key, remote_path)
    with _sftp_pool_lock:
        cache_entry = _sftp_directory_cache.get(cache_key)
        if not cache_entry:
            return None
        if now_ts - cache_entry.get('ts', 0) > SFTP_DIR_CACHE_TTL_SEC:
            _sftp_directory_cache.pop(cache_key, None)
            return None
        return cache_entry.get('payload')


def _write_cached_directory(server_key, remote_path, payload):
    """Store directory payload in short-lived cache."""
    with _sftp_pool_lock:
        _sftp_directory_cache[(server_key, remote_path)] = {
            'ts': time.time(),
            'payload': payload
        }


def _mark_session_used(server_key):
    """Refresh last-used timestamp for pooled session."""
    with _sftp_pool_lock:
        session_entry = _sftp_session_pool.get(server_key)
        if session_entry:
            session_entry['last_used'] = time.time()


def _drop_session(server_key):
    """Remove a session from the pool and close it."""
    with _sftp_pool_lock:
        session_entry = _sftp_session_pool.pop(server_key, None)
    _close_sftp_session_entry(session_entry)


def _get_or_create_sftp_session(server_key, hostname, port, username, password):
    """Reuse healthy pooled session or create a new SFTP connection."""
    with _sftp_pool_lock:
        pooled_entry = _sftp_session_pool.get(server_key)
        if _is_session_alive(pooled_entry):
            pooled_entry['last_used'] = time.time()
            return pooled_entry['ssh'], pooled_entry['sftp']
        if pooled_entry:
            _sftp_session_pool.pop(server_key, None)

    if pooled_entry:
        _close_sftp_session_entry(pooled_entry)

    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.connect(hostname, port=port, username=username, password=password, timeout=10)
    sftp_client = ssh_client.open_sftp()
    new_entry = {
        'ssh': ssh_client,
        'sftp': sftp_client,
        'last_used': time.time()
    }

    with _sftp_pool_lock:
        existing_entry = _sftp_session_pool.get(server_key)
        if _is_session_alive(existing_entry):
            _close_sftp_session_entry(new_entry)
            return existing_entry['ssh'], existing_entry['sftp']
        _sftp_session_pool[server_key] = new_entry
        return new_entry['ssh'], new_entry['sftp']


def _resolve_sftp_target(saas_section):
    """Resolve credentials and connection info for requested SaaS section."""
    login_creds = _read_login_credentials()
    creds = login_creds.get(saas_section, {})
    username = creds.get('username', '').strip()
    password = creds.get('password', '').strip()
    if not username or not password:
        raise ValueError(f'No credentials found for {saas_section}')

    connection_info = _read_connection_info()
    conn_info = connection_info.get(saas_section, {})
    hostname = conn_info.get('hostName', '').strip()
    if not hostname:
        raise LookupError(f'No connection info found for {saas_section}')

    port = int(conn_info.get('portNumber', 2222))
    server_key = _sftp_server_key(saas_section, hostname, port, username)
    return server_key, hostname, port, username, password


def _invalidate_sftp_state():
    """Clear all pooled SFTP sessions and cached directory data."""
    with _sftp_pool_lock:
        session_entries = list(_sftp_session_pool.values())
        _sftp_session_pool.clear()
        _sftp_directory_cache.clear()
    for session_entry in session_entries:
        _close_sftp_session_entry(session_entry)


@atexit.register
def _shutdown_sftp_pool():
    """Ensure pooled sessions are closed on process exit."""
    _invalidate_sftp_state()



def _normalize_connection_info(payload):
    """Normalize payload against allowed schema and defaults."""
    normalized = deepcopy(DEFAULT_CONNECTION_INFO)
    if not isinstance(payload, dict):
        return normalized

    for section_key, defaults in DEFAULT_CONNECTION_INFO.items():
        section_payload = payload.get(section_key, {})
        if not isinstance(section_payload, dict):
            continue

        protocol = str(section_payload.get('fileProtocol', defaults['fileProtocol'])).strip()
        if protocol in CONNECTION_PROTOCOLS:
            normalized[section_key]['fileProtocol'] = protocol

        host_name = str(section_payload.get('hostName', defaults['hostName'])).strip()
        normalized[section_key]['hostName'] = host_name or defaults['hostName']

        port_number = re.sub(r'\D', '', str(section_payload.get('portNumber', defaults['portNumber'])))
        normalized[section_key]['portNumber'] = port_number or defaults['portNumber']

    return normalized


def _normalize_login_credentials(payload):
    """Normalize login credentials payload."""
    normalized = deepcopy(DEFAULT_LOGIN_CREDENTIALS)

    if not isinstance(payload, dict):
        return normalized

    saas_p_payload = payload.get('saasP', {})
    if not isinstance(saas_p_payload, dict):
        saas_p_payload = payload.get('saasPNonProd', {})
    if not isinstance(saas_p_payload, dict) or not (saas_p_payload.get('username') or saas_p_payload.get('password')):
        legacy_prod_payload = payload.get('saasPProd', {})
        if isinstance(legacy_prod_payload, dict):
            saas_p_payload = legacy_prod_payload

    section_payloads = {
        'saasN': payload.get('saasN', {}),
        'saasP': saas_p_payload
    }

    for section_key, defaults in DEFAULT_LOGIN_CREDENTIALS.items():
        section_payload = section_payloads.get(section_key, {})
        if not isinstance(section_payload, dict):
            continue

        username = str(section_payload.get('username', defaults['username'])).strip()
        password = str(section_payload.get('password', defaults['password']))
        normalized[section_key]['username'] = username
        normalized[section_key]['password'] = password

    return normalized


def _read_login_credentials():
    """Read login credentials from file, creating empty defaults on first run."""
    with _connection_info_lock:
        if not os.path.exists(LOGIN_CREDENTIALS_FILE):
            login_creds = deepcopy(DEFAULT_LOGIN_CREDENTIALS)
            with open(LOGIN_CREDENTIALS_FILE, 'w', encoding='utf-8') as file_handle:
                json.dump(login_creds, file_handle, indent=2)
            return login_creds

        try:
            with open(LOGIN_CREDENTIALS_FILE, 'r', encoding='utf-8') as file_handle:
                raw_data = json.load(file_handle)
        except (OSError, json.JSONDecodeError):
            raw_data = {}

        normalized_data = _normalize_login_credentials(raw_data)
        if normalized_data != raw_data:
            with open(LOGIN_CREDENTIALS_FILE, 'w', encoding='utf-8') as file_handle:
                json.dump(normalized_data, file_handle, indent=2)
        return normalized_data


def _write_login_credentials(login_creds):
    """Persist normalized login credentials to file."""
    with _connection_info_lock:
        with open(LOGIN_CREDENTIALS_FILE, 'w', encoding='utf-8') as file_handle:
            json.dump(login_creds, file_handle, indent=2)


def _read_connection_info():
    """Read connection settings from file, creating defaults on first run."""
    with _connection_info_lock:
        if not os.path.exists(CONNECTION_INFO_FILE):
            connection_info = deepcopy(DEFAULT_CONNECTION_INFO)
            with open(CONNECTION_INFO_FILE, 'w', encoding='utf-8') as file_handle:
                json.dump(connection_info, file_handle, indent=2)
            return connection_info

        try:
            with open(CONNECTION_INFO_FILE, 'r', encoding='utf-8') as file_handle:
                raw_data = json.load(file_handle)
        except (OSError, json.JSONDecodeError):
            raw_data = {}

        normalized_data = _normalize_connection_info(raw_data)
        return normalized_data


def _write_connection_info(connection_info):
    """Persist normalized connection settings to file."""
    with _connection_info_lock:
        with open(CONNECTION_INFO_FILE, 'w', encoding='utf-8') as file_handle:
            json.dump(connection_info, file_handle, indent=2)


def _read_preseed_config():
    """Read and cache YAML pre-seed configuration."""
    with _preseed_lock:
        try:
            file_mtime = os.path.getmtime(PRESEED_CONFIG_FILE)
        except OSError:
            _preseed_config_cache['mtime'] = None
            _preseed_config_cache['data'] = {}
            return {}

        if _preseed_config_cache['mtime'] == file_mtime:
            return _preseed_config_cache['data']

        try:
            with open(PRESEED_CONFIG_FILE, 'r', encoding='utf-8') as file_handle:
                parsed = yaml.safe_load(file_handle) or {}
        except (OSError, yaml.YAMLError):
            parsed = {}

        if not isinstance(parsed, dict):
            parsed = {}

        _preseed_config_cache['mtime'] = file_mtime
        _preseed_config_cache['data'] = parsed
        return parsed


def _get_preseed_file_map(environment, usergroup, payment_form):
    """Resolve file map for environment/usergroup/payment form from YAML config."""
    config_key = PAYMENT_FORM_TO_CONFIG_KEY.get(payment_form)
    if not config_key:
        raise ValueError('Unsupported payment form')

    config_data = _read_preseed_config()
    environments = config_data.get('environments', {})
    if not isinstance(environments, dict):
        raise LookupError('No pre-seed environments configured')

    env_node = environments.get(environment)
    if not isinstance(env_node, dict):
        raise LookupError(f'Environment {environment} not found')

    usergroup_node = env_node.get(usergroup)
    if not isinstance(usergroup_node, dict):
        raise LookupError(f'Usergroup {usergroup} not found for {environment}')

    file_map = usergroup_node.get(config_key)
    if not isinstance(file_map, dict):
        raise LookupError(f'No pre-seed files found for {payment_form}')

    return file_map

def extract_keywords(text):
    """Extract meaningful keywords from text"""
    # Remove common words
    stop_words = {'what', 'is', 'the', 'a', 'an', 'do', 'does', 'how', 'why', 'when', 'where', 'can', 'you', 'about', 'tell', 'me', 'know', 'understand'}
    words = text.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def find_relevant_knowledge(question, knowledge_text):
    """Find the most relevant parts of knowledge base based on question"""
    question_keywords = extract_keywords(question)
    knowledge_lines = knowledge_text.split('\n')

    scored_lines = []
    for line in knowledge_lines:
        if not line.strip():
            continue
        score = sum(1 for keyword in question_keywords if keyword in line.lower())
        if score > 0:
            scored_lines.append((score, line.strip()))

    # Sort by relevance score
    scored_lines.sort(reverse=True)
    relevant_knowledge = ' '.join([line for _, line in scored_lines[:3]])  # Top 3 relevant lines
    return relevant_knowledge if relevant_knowledge else knowledge_text.strip()

def generate_response(question, knowledge):
    """Generate a natural response based on knowledge"""
    relevant = find_relevant_knowledge(question, knowledge)

    # Simple template-based response generation
    response = f"{relevant}"
    return response

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data['question']
    project = data.get('project', 'general')

    # Check for bug/error/issue related questions
    if 'bug' in question.lower() or 'error' in question.lower() or 'issue' in question.lower():
        answer = f"This seems like a common issue. Please check the logs or restart the service."
    else:
        # Check the knowledge base
        try:
            with open(f'knowledge_{project}.txt', 'r') as f:
                knowledge = f.read().strip()
            if knowledge:
                # Generate a contextual response
                answer = generate_response(question, knowledge)
            else:
                answer = f"I'm sorry, I don't have specific information on that for project {project}. If you can provide more details or knowledge about this topic, it would be greatly appreciated so I can assist better in the future."
        except FileNotFoundError:
            answer = f"I'm sorry, I don't have specific information on that for project {project}. If you can provide more details or knowledge about this topic, it would be greatly appreciated so I can assist better in the future."
    return jsonify({'answer': answer})

@app.route('/submit-knowledge', methods=['POST'])
def submit_knowledge():
    data = request.get_json()
    project = data.get('project', 'general')
    knowledge = data.get('knowledge', '')

    if not knowledge:
        return jsonify({'message': 'No knowledge provided'}), 400

    # Save the knowledge to a local file (appending for simplicity)
    with open(f'knowledge_{project}.txt', 'a') as f:
        f.write(knowledge + '\n')

    return jsonify({'message': 'Knowledge submitted successfully!'})

@app.route('/generate-xml', methods=['POST'])
def generate_xml():
    """Generate payment XML file for single or mix form payloads."""
    try:
        form_data = request.get_json() or {}
        form_list = form_data.get('forms') if isinstance(form_data.get('forms'), list) else None

        if form_list:
            xml_contents = []
            for index, single_form in enumerate(form_list, start=1):
                if not isinstance(single_form, dict):
                    return jsonify({'error': f'Invalid form payload at position {index}'}), 400
                file_type = single_form.get('fileType', 'ACH NACHA XML')
                if file_type not in ('ACH NACHA XML', 'ACH CAEFT XML', 'CHECKS XML'):
                    return jsonify({'error': f'File type {file_type} not yet implemented for Mix File generation'}), 400
                xml_contents.append(_build_xml_content_from_form(single_form))

            combined_xml = _combine_generated_xml(xml_contents)
            xml_io = BytesIO(combined_xml.encode('utf-8'))
            xml_io.seek(0)
            return send_file(
                xml_io,
                mimetype='application/xml',
                as_attachment=True,
                download_name='mixed_payment.xml'
            )

        file_type = form_data.get('fileType', 'ACH NACHA XML')

        if file_type in ('ACH NACHA XML', 'ACH CAEFT XML', 'CHECKS XML'):
            return generate_ach_nacha_xml(form_data)
        if file_type == 'ACH FILE':
            return generate_ach_file(form_data)
        if file_type == 'Check Recon File':
            return generate_check_recon_file(form_data)
        if file_type in ('WebSeries Wire DOM XML', 'WebSeries Wire INTL XML'):
            return generate_webseries_wire_xml_file(form_data)
        if file_type == 'WebSeries BAB':
            return generate_webseries_bab_file(form_data)
        if file_type in WIRE_CSV_FILE_TYPES:
            return generate_csv_wire_domestic_file(form_data)
        else:
            return jsonify({'error': f'File type {file_type} not yet implemented'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/preview-file', methods=['POST'])
def preview_file():
    """Preview generated file content for supported payment file types."""
    try:
        form_data = request.get_json() or {}
        file_type = str(form_data.get('fileType', '')).strip()

        if file_type in ('ACH NACHA XML', 'ACH CAEFT XML', 'CHECKS XML'):
            xml_content = _build_xml_content_from_form(form_data)
            return jsonify({'content': xml_content})

        if file_type in ('WebSeries Wire DOM XML', 'WebSeries Wire INTL XML'):
            requested_batches = _parse_webseries_batches_count(form_data)
            if requested_batches > WEBSERIES_WIRE_MAX_PREVIEW_BATCHES:
                raise ValueError(
                    f'Preview supports up to {WEBSERIES_WIRE_MAX_PREVIEW_BATCHES} batches for WebSeries Wire files. '
                    'Use Generate for larger files.'
                )
            xml_content = _build_webseries_wire_xml_content(form_data)
            return jsonify({'content': xml_content})

        if file_type == 'WebSeries BAB':
            return jsonify({'content': _build_webseries_bab_content(form_data)})

        if file_type not in WIRE_CSV_FILE_TYPES:
            return jsonify({'error': 'Preview is currently supported for ACH NACHA XML, ACH CAEFT XML, CHECKS XML, WebSeries Wire DOM XML, WebSeries Wire INTL XML, WebSeries BAB, and Wire CSV files.'}), 400

        csv_content = _build_csv_wire_domestic_content(form_data)
        preview_token = _random_alphanumeric(24)
        now = time.time()

        with _wire_csv_preview_lock:
            _purge_expired_wire_csv_previews(now)
            _wire_csv_preview_cache[preview_token] = {
                'content': csv_content,
                'created_at': now
            }

        return jsonify({
            'content': csv_content,
            'previewToken': preview_token
        })
    except Exception as e:
        return jsonify({'error': f'Error generating file preview: {str(e)}'}), 400


def _build_xml_content_from_form(form_data):
    """Build generated XML string for a single ACH/CAEFT form payload."""
    file_type = form_data.get('fileType', 'ACH NACHA XML')
    if file_type == 'CHECKS XML':
        return _build_checks_xml_content(form_data)

    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    payment_data = PaymentData.from_form_data(form_data)
    print(f"Payment Data: {payment_data.to_dict()}")
    xml_generator = ACHNachaXMLGenerator(template_dir)
    return xml_generator.generate(payment_data)


def _parse_csv_values(raw_value):
    """Parse comma-separated values from incoming form payload."""
    if isinstance(raw_value, list):
        return [str(value).strip() for value in raw_value if str(value).strip()]
    return [value.strip() for value in str(raw_value or '').split(',') if value.strip()]


def _get_preserved_tag_values(form_data, field_name):
    """Return raw tag values preserved by the frontend payload when available."""
    if not isinstance(form_data, dict):
        return []

    tag_values = form_data.get('__tagValues')
    if not isinstance(tag_values, dict):
        return []

    raw_values = tag_values.get(field_name)
    if isinstance(raw_values, list):
        return [str(value).strip() for value in raw_values if str(value).strip()]

    if isinstance(raw_values, str):
        try:
            parsed_values = json.loads(raw_values)
        except (TypeError, json.JSONDecodeError):
            return [raw_values.strip()] if raw_values.strip() else []
        if isinstance(parsed_values, list):
            return [str(value).strip() for value in parsed_values if str(value).strip()]

    return []


def _get_form_tag_values(form_data, field_name):
    """Return tag values using preserved arrays when present, else fall back to CSV parsing."""
    preserved_values = _get_preserved_tag_values(form_data, field_name)
    if preserved_values:
        return preserved_values
    return _parse_csv_values(form_data.get(field_name, ''))


def _parse_form_tag_values_for_transactions(form_data, field_name, tx_count, field_label):
    """Resolve one shared value or one value per transaction from a form payload field."""
    values = _get_form_tag_values(form_data, field_name)
    if not values:
        return [''] * tx_count
    if len(values) not in (1, tx_count):
        raise ValueError(f'{field_label} must contain either one value or exactly {tx_count} values.')
    return values


def _get_first_form_tag_value(form_data, field_name, fallback=''):
    """Return the first available tag value for a form payload field."""
    values = _get_form_tag_values(form_data, field_name)
    return values[0] if values else fallback


def _left_pad(value, size, pad_char=' '):
    """Mirror Java StringUtils.leftPad behavior for simple fixed-width formatting."""
    text = str(value or '')
    if len(text) >= size:
        return text
    return text.rjust(size, pad_char)


def _right_pad(value, size, pad_char=' '):
    """Mirror Java StringUtils.rightPad behavior for simple fixed-width formatting."""
    text = str(value or '')
    if len(text) >= size:
        return text
    return text.ljust(size, pad_char)


def _future_business_date(days_ahead=1):
    """Return next business date (skip weekends) formatted as yyMMdd."""
    candidate = datetime.now().date()
    remaining = max(0, int(days_ahead or 0))
    while remaining > 0:
        candidate += timedelta(days=1)
        if candidate.weekday() < 5:
            remaining -= 1
    return candidate.strftime('%y%m%d')


def _future_business_date_yyyymmdd(days_ahead=0):
    """Return future business date (skip weekends) formatted as yyyyMMdd."""
    candidate = datetime.now().date()
    remaining = max(0, int(days_ahead or 0))
    while remaining > 0:
        candidate += timedelta(days=1)
        if candidate.weekday() < 5:
            remaining -= 1
    return candidate.strftime('%Y%m%d')


def _random_alphanumeric(length):
    """Return random alphanumeric string similar to RandomStringUtils.randomAlphanumeric."""
    size = max(0, int(length or 0))
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=size))


def _parse_wire_values_for_transactions(raw_value, tx_count, field_label):
    """Parse wire CSV field values allowing one shared value or one per transaction."""
    values = _parse_csv_values(raw_value)
    if not values:
        return [''] * tx_count
    if len(values) not in (1, tx_count):
        raise ValueError(f'{field_label} must contain either one value or exactly {tx_count} values.')
    return values


def _resolve_wire_transactions_count(form_data):
    """Resolve number of wire detail lines from wire-specific or shared transactions count."""
    for key in ('wireDomesticTransactionsCount', 'wireDomesticTransactionCount', 'transactionsCount'):
        raw_value = str(form_data.get(key, '')).strip()
        if raw_value:
            return _parse_positive_int_csv(raw_value, default_value=1)[0]
    return 1


def _parse_webseries_batches_count(form_data):
    """Resolve WebSeries batches count from single-value numeric field."""
    raw_values = _get_form_tag_values(form_data, 'wsBatchesCount')
    if not raw_values:
        # Backward-compatible key retained in the UI.
        raw_values = _get_form_tag_values(form_data, 'wsTransactionsCount')
    if not raw_values:
        return 1

    if len(raw_values) != 1:
        raise ValueError('Batches Count must contain exactly one numeric value greater than 0.')

    batch_count_value = str(raw_values[0] or '').strip()
    if not batch_count_value.isdigit() or int(batch_count_value) <= 0:
        raise ValueError('Batches Count must contain exactly one numeric value greater than 0.')

    parsed_batches = int(batch_count_value)
    if parsed_batches > WEBSERIES_WIRE_MAX_BATCHES:
        raise ValueError(f'Batches Count cannot exceed {WEBSERIES_WIRE_MAX_BATCHES}.')

    return parsed_batches


def _parse_webseries_increment(form_data):
    """Resolve WebSeries account-number increment (single non-negative integer)."""
    raw_values = _get_form_tag_values(form_data, 'wsIncrement')
    if not raw_values:
        return 0
    if len(raw_values) != 1:
        raise ValueError('Increment must contain exactly one non-negative numeric value.')

    increment_value = str(raw_values[0] or '').strip()
    if not increment_value.isdigit():
        raise ValueError('Increment must be a non-negative numeric value (0 or greater).')
    return int(increment_value)


def _parse_webseries_user_id(form_data):
    """Resolve WebSeries user id from a single-value field with default fallback."""
    raw_values = _get_form_tag_values(form_data, 'wsUserId')
    if not raw_values:
        return 'RISK1'
    if len(raw_values) != 1:
        raise ValueError('UserId must contain exactly one value.')
    return str(raw_values[0] or '').strip() or 'RISK1'


def _parse_webseries_originator_name(form_data):
    """Resolve WebSeries Originator Name from a single-value field."""
    raw_values = _get_form_tag_values(form_data, 'wsOriginatorName')
    if not raw_values:
        raise ValueError('Originator Name must contain exactly one value.')
    if len(raw_values) != 1:
        raise ValueError('Originator Name must contain exactly one value.')
    originator_name = str(raw_values[0] or '').strip()
    if not originator_name:
        raise ValueError('Originator Name must contain exactly one value.')
    return originator_name


def _parse_webseries_bab_beneficiary_count(form_data):
    """Resolve WebSeries BAB beneficiary count from a single positive integer value."""
    raw_values = _get_form_tag_values(form_data, 'babBeneficiaryCount')
    if not raw_values:
        return 1
    if len(raw_values) != 1:
        raise ValueError('Beneficiary Count must contain exactly one numeric value greater than 0.')

    beneficiary_count_value = str(raw_values[0] or '').strip()
    if not beneficiary_count_value.isdigit() or int(beneficiary_count_value) <= 0:
        raise ValueError('Beneficiary Count must contain exactly one numeric value greater than 0.')

    return int(beneficiary_count_value)


def _parse_webseries_bab_third_line_count(form_data):
    """Resolve WebSeries BAB third-line count from a single positive integer value."""
    raw_value = str(form_data.get('babThirdLineCount', '')).strip()
    if not raw_value:
        return 1
    if not raw_value.isdigit() or int(raw_value) <= 0:
        raise ValueError('Third Line Count must contain exactly one numeric value greater than 0.')
    return int(raw_value)


def _parse_webseries_bab_notebook_entries(form_data):
    """Parse editable BAB notepad entries and keep only B/A records."""
    raw_entries = form_data.get('babNotebookEntries', '[]')
    if isinstance(raw_entries, str):
        try:
            parsed_entries = json.loads(raw_entries)
        except (TypeError, json.JSONDecodeError):
            parsed_entries = []
    elif isinstance(raw_entries, list):
        parsed_entries = raw_entries
    else:
        parsed_entries = []

    normalized_entries = []
    for entry in parsed_entries:
        text = str(entry or '').strip()
        if text.startswith('B,') or text.startswith('A,'):
            normalized_entries.append(text)
    return normalized_entries


def _parse_optional_single_form_tag_value(form_data, field_name, field_label):
    """Resolve an optional single tag value, accepting a plain field value as fallback."""
    raw_values = _get_form_tag_values(form_data, field_name)
    if raw_values:
        if len(raw_values) != 1:
            raise ValueError(f'{field_label} must contain at most one value.')
        return str(raw_values[0] or '').strip()
    # Fallback: plain form field (e.g. dropdown submitted as plain string)
    raw_plain = str(form_data.get(field_name, '') or '').strip()
    return raw_plain


def _parse_webseries_bab_currency(form_data, payment_type=''):
    """Resolve WebSeries BAB currency based on payment type selection."""
    normalized_payment_type = str(payment_type or '').strip().upper()
    if normalized_payment_type != 'WIRE - INTERNATIONAL':
        return 'USD'

    allowed_currencies = {
        'AUD', 'BRL', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD',
        'INR', 'JPY', 'NZD', 'RUB', 'TRY', 'USD', 'ZAR'
    }
    raw_value = _parse_optional_single_form_tag_value(form_data, 'babCurrency', 'Currency') or str(form_data.get('currency', '') or '')
    currency_value = str(raw_value or '').strip().upper()
    if not currency_value:
        return ''
    return currency_value if currency_value in allowed_currencies else ''


def _parse_webseries_bab_account_type(form_data):
    """Resolve WebSeries BAB account type from supported dropdown values."""
    raw_value = str(form_data.get('babAccountType', '') or form_data.get('accountType', '') or 'Other').strip()
    allowed_values = {'Other', 'IBAN', 'Loans', 'Checking', 'Checkings', 'Savings', 'ABA', 'DDA', 'SWIFT'}
    return raw_value if raw_value in allowed_values else 'Other'


def _map_account_type_to_abbreviation(account_type):
    """Map full account type name to Cash Concentration/Disbursement abbreviation."""
    normalized = str(account_type or '').strip()
    mapping = {
        'Savings': 'SV',
        'Loans': 'CL',
        'Checking': 'DD',
        'Checkings': 'DD'
    }
    return mapping.get(normalized, normalized)


def _normalize_webseries_bab_notebook_entry(entry, payment_type=''):
    """Normalize BAB notebook A-lines for Cash Concentration formatting rules."""
    text = str(entry or '').strip()
    if not text.startswith('A,'):
        return text

    fields = text.split(',')
    normalized_payment_type = str(payment_type or '').strip().upper()
    is_cash = normalized_payment_type == 'CASH CONCENTRATION/DISBURSEMENT'
    if not is_cash and len(fields) > 2:
        is_cash = fields[1] == 'CCD' and fields[2] == 'NACHA'
    if not is_cash:
        return text

    while len(fields) < 16:
        fields.append('')

    fields[12] = _map_account_type_to_abbreviation(fields[12])
    if not str(fields[14] or '').strip():
        fields[14] = 'US-ACH'
    if not str(fields[15] or '').strip():
        fields[15] = '021000018'

    # Cash Concentration must end at BankCode with no trailing commas.
    return ','.join(fields[:16])


def _map_webseries_bab_payment_fields(raw_payment_type):
    """Map UI payment type labels to BAB third-line PaymentType/ClearingSystem values."""
    normalized = str(raw_payment_type or '').strip().upper()
    mapping = {
        'CASH CONCENTRATION/DISBURSEMENT': ('CCD', 'NACHA'),
        'WIRE - DOMESTIC': ('USWIRE', ''),
        'WIRE - INTERNATIONAL': ('INT', '')
    }
    return mapping.get(normalized, (normalized, ''))


def _parse_webseries_migration_rows(form_data):
    """Parse and normalize migration address rows from hidden JSON payload."""
    raw_rows = form_data.get('migrationAddressFields', '[]')
    if isinstance(raw_rows, str):
        try:
            parsed_rows = json.loads(raw_rows)
        except (TypeError, json.JSONDecodeError):
            parsed_rows = []
    elif isinstance(raw_rows, list):
        parsed_rows = raw_rows
    else:
        parsed_rows = []

    normalized_rows = []
    for row in parsed_rows:
        if not isinstance(row, dict):
            continue
        normalized = {
            'BENE_ADDRESS_1': str(row.get('BENE_ADDRESS_1', '') or ''),
            'BENE_ADDRESS_2': str(row.get('BENE_ADDRESS_2', '') or ''),
            'ORIGINATOR_ADDRESS_1': str(row.get('ORIGINATOR_ADDRESS_1', '') or ''),
            'ORIGINATOR_ADDRESS_2': str(row.get('ORIGINATOR_ADDRESS_2', '') or ''),
            'ORIGINATOR_CITY': str(row.get('ORIGINATOR_CITY', '') or '')
        }
        if any(value != '' for value in normalized.values()):
            normalized_rows.append(normalized)

    return normalized_rows


def _get_webseries_wire_template_file(form_data):
    """Select the WebSeries XML template based on the requested payment form."""
    file_type = str((form_data or {}).get('fileType', '')).strip()
    if file_type == 'WebSeries Wire INTL XML':
        return WEBSERIES_WIRE_INTL_TEMPLATE_FILE
    return WEBSERIES_WIRE_DOM_TEMPLATE_FILE


def _sanitize_webseries_migration_value(value):
    """Map NULL/null placeholders to empty string for XML content."""
    normalized = str(value or '')
    return '' if normalized.strip().lower() == 'null' else normalized


def _first_csv_value(raw_value, fallback=''):
    """Return first comma-separated value or fallback when none exists."""
    parsed_values = _parse_csv_values(raw_value)
    return parsed_values[0] if parsed_values else fallback


def _set_xml_text(parent_node, xpath, value):
    """Set XML node text when target exists."""
    target_node = parent_node.find(xpath) if parent_node is not None else None
    if target_node is not None:
        target_node.text = str(value or '')


def _xml_escape_text(value):
    """Escape special XML characters in text node content."""
    text = str(value or '')
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _build_webseries_wire_xml_content(form_data):
    """Build WebSeries Wire XML using a string-template approach for high performance.

    Instead of deepcopy-per-batch which is O(n) in ElementTree objects, we:
      1. Build ONE batch node in ElementTree with placeholder tokens for per-batch fields.
      2. Serialise that node to a string once.
      3. Loop of N batches: only do str.replace() on the ~4 KB template string.
      4. Concatenate the result with the file header/footer.

    Throughput is 50-100× faster than the deepcopy approach for large N.
    """
    template_file = _get_webseries_wire_template_file(form_data)
    is_intl_template = template_file == WEBSERIES_WIRE_INTL_TEMPLATE_FILE
    transaction_node_name = 'INTL' if is_intl_template else 'FedWire'
    if not os.path.exists(template_file):
        raise FileNotFoundError(f'WebSeries template file not found: {template_file}')

    template_tree = ET.parse(template_file)
    root = template_tree.getroot()

    batch_template = root.find('./Batch')
    if batch_template is None:
        raise ValueError('Invalid WebSeries template structure. Expected at least one Batch node.')

    batches_count = _parse_webseries_batches_count(form_data)
    migration_rows = _parse_webseries_migration_rows(form_data)
    if len(migration_rows) == 0:
        raise ValueError('Migration Address Fields must contain at least one row.')

    corr_address_line3_values = _parse_form_tag_values_for_transactions(form_data, 'wsAddressLine3', batches_count, 'AddressLine3')
    corr_state_values = _parse_form_tag_values_for_transactions(form_data, 'wsState', batches_count, 'State')
    corr_bank_id_values = _parse_form_tag_values_for_transactions(form_data, 'wsBankID', batches_count, 'BankID')
    corr_bank_name_values = _parse_form_tag_values_for_transactions(form_data, 'wsBankNameCorr', batches_count, 'BankName')
    corr_routing_aba_values = _parse_form_tag_values_for_transactions(form_data, 'wsBankRoutingABA', batches_count, 'BankRoutingABA')

    payee_bank_account_values = _parse_form_tag_values_for_transactions(form_data, 'wsPayeeBankAccountNumber', batches_count, 'Payee Bank Account Number')
    payee_bank_id_values = _parse_form_tag_values_for_transactions(form_data, 'wsPayeeBankID', batches_count, 'Payee BankID')
    payee_bank_name_values = _parse_form_tag_values_for_transactions(form_data, 'wsPayeeBankName', batches_count, 'Payee Bank Name')
    payee_routing_aba_values = _parse_form_tag_values_for_transactions(form_data, 'wsPayeeBankRoutingABA', batches_count, 'Payee BankRoutingABA')

    account_number_start = _get_first_form_tag_value(form_data, 'wsAccountNumber').strip()
    if not account_number_start.isdigit():
        raise ValueError('Company Bank Info - Account Number must be numeric for batch incrementing.')
    account_number_width = len(account_number_start)
    account_number_start_numeric = int(account_number_start)
    increment_value = _parse_webseries_increment(form_data)
    webseries_user_id = _parse_webseries_user_id(form_data)
    originator_name = _parse_webseries_originator_name(form_data)

    # Build account number range for round-robin when Account Number End is provided
    account_number_end_raw = _get_first_form_tag_value(form_data, 'wsAccountNumberEnd').strip()
    account_range = None
    if account_number_end_raw:
        if not account_number_end_raw.isdigit():
            raise ValueError('Company Bank Info - Account Number End must be numeric.')
        account_number_end_numeric = int(account_number_end_raw)
        if account_number_end_numeric < account_number_start_numeric:
            raise ValueError('Account Number End must be greater than or equal to Account Number (start).')
        if increment_value > 0:
            account_range = []
            current = account_number_start_numeric
            while current <= account_number_end_numeric:
                account_range.append(str(current).zfill(account_number_width))
                current += increment_value
            if not account_range:
                account_range = [account_number_start]
        else:
            account_range = None

    # -------------------------------------------------------------------
    # String-template generation
    # -------------------------------------------------------------------
    # Placeholder tokens: use ASCII SOH/STX/ETX characters that cannot
    # appear in user data or XML angle-bracket content, avoiding any
    # risk of accidental collision with real field values.
    P_ACCT   = '\x01WS_ACCT\x01'
    P_BENE1  = '\x01WS_BENE1\x01'
    P_BENE2  = '\x01WS_BENE2\x01'
    P_ORIG1  = '\x01WS_ORIG1\x01'
    P_ORIG2  = '\x01WS_ORIG2\x01'
    P_ORIGC  = '\x01WS_ORIGC\x01'
    P_CORR3  = '\x01WS_CORR3\x01'
    P_CORRST = '\x01WS_CORRST\x01'
    P_CORRBI = '\x01WS_CORRBI\x01'
    P_CORRBN = '\x01WS_CORRBN\x01'
    P_CORRA  = '\x01WS_CORRA\x01'
    P_PYEACC = '\x01WS_PYEACC\x01'
    P_PYEBI  = '\x01WS_PYEBI\x01'
    P_PYEBN  = '\x01WS_PYEBN\x01'
    P_PYERA  = '\x01WS_PYERA\x01'

    # Build ONE batch node in ElementTree (the only deepcopy in the function).
    batch_node = deepcopy(batch_template)
    batch_info = batch_node.find('./BatchInformation')
    transactions_node = batch_node.find('./Transactions')
    transaction_nodes = list(transactions_node.findall(transaction_node_name)) if transactions_node is not None else []
    if batch_info is None or transactions_node is None or not transaction_nodes:
        raise ValueError(f'Invalid WebSeries template structure. Expected BatchInformation/Transactions/{transaction_node_name} nodes.')

    for extra_transaction in transaction_nodes[1:]:
        transactions_node.remove(extra_transaction)
    transaction_node = transaction_nodes[0]

    # Static fields: set the actual values directly.
    _set_xml_text(batch_info, './CompanyBankInfo/BankName', _get_first_form_tag_value(form_data, 'wsBankNameCompany'))
    _set_xml_text(batch_info, './CompanyBankInfo/BankRouting/ABA', _get_first_form_tag_value(form_data, 'wsAbas'))
    _set_xml_text(batch_info, './WebSeriesUserGroup', _get_first_form_tag_value(form_data, 'wsClientCompany'))
    _set_xml_text(batch_info, './WebSeriesUserID', webseries_user_id)
    _set_xml_text(transaction_node, './OriginatorInformation/OriginatorName', originator_name)
    _set_xml_text(transaction_node, './TranDate', datetime.now().strftime('%Y-%m-%d'))

    # Per-batch-variable fields: set placeholder tokens.
    _set_xml_text(batch_info, './CompanyBankInfo/BankAccount/AccountNumber', P_ACCT)
    _set_xml_text(transaction_node, './CorrBankInfo/BankAddress/AddressLine3', P_CORR3)
    _set_xml_text(transaction_node, './CorrBankInfo/BankAddress/State', P_CORRST)
    _set_xml_text(transaction_node, './CorrBankInfo/BankID', P_CORRBI)
    _set_xml_text(transaction_node, './CorrBankInfo/BankName', P_CORRBN)
    _set_xml_text(transaction_node, './CorrBankInfo/BankRouting/ABA', P_CORRA)
    _set_xml_text(transaction_node, './OriginatorInformation/OriginatorAddress/OriginatorAddressLine1', P_ORIG1)
    _set_xml_text(transaction_node, './OriginatorInformation/OriginatorAddress/OriginatorAddressLine2', P_ORIG2)
    _set_xml_text(transaction_node, './OriginatorInformation/OriginatorAddress/OriginatorAddressLine3', P_ORIGC)
    _set_xml_text(transaction_node, './PayeeBankInfo/BankAccount/AccountNumber', P_PYEACC)
    _set_xml_text(transaction_node, './PayeeBankInfo/BankID', P_PYEBI)
    _set_xml_text(transaction_node, './PayeeBankInfo/BankName', P_PYEBN)
    _set_xml_text(transaction_node, './PayeeBankInfo/BankRouting/ABA', P_PYERA)
    _set_xml_text(transaction_node, './PayeeInformation/PayeeAddress/AddressLine1', P_BENE1)
    _set_xml_text(transaction_node, './PayeeInformation/PayeeAddress/AddressLine2', P_BENE2)

    # Serialise the template batch node to a string ONCE.
    batch_tmpl = ET.tostring(batch_node, encoding='unicode')

    # Pre-compute per-batch account numbers to avoid repeated arithmetic in loop.
    if account_range is not None:
        ar_len = len(account_range)
        account_numbers = [account_range[i % ar_len] for i in range(batches_count)]
    elif increment_value == 0:
        # All batches share the same account number.
        account_numbers = [account_number_start] * batches_count
    else:
        account_numbers = [
            str(account_number_start_numeric + i * increment_value).zfill(account_number_width)
            for i in range(batches_count)
        ]

    # Pre-compute per-batch migration values.
    mig_len = len(migration_rows)
    mig_bene1 = [_xml_escape_text(_sanitize_webseries_migration_value(migration_rows[i % mig_len].get('BENE_ADDRESS_1', ''))) for i in range(batches_count)]
    mig_bene2 = [_xml_escape_text(_sanitize_webseries_migration_value(migration_rows[i % mig_len].get('BENE_ADDRESS_2', ''))) for i in range(batches_count)]
    mig_orig1 = [_xml_escape_text(_sanitize_webseries_migration_value(migration_rows[i % mig_len].get('ORIGINATOR_ADDRESS_1', ''))) for i in range(batches_count)]
    mig_orig2 = [_xml_escape_text(_sanitize_webseries_migration_value(migration_rows[i % mig_len].get('ORIGINATOR_ADDRESS_2', ''))) for i in range(batches_count)]
    mig_origc = [_xml_escape_text(_sanitize_webseries_migration_value(migration_rows[i % mig_len].get('ORIGINATOR_CITY', ''))) for i in range(batches_count)]

    # Pre-compute per-batch bank field values (often single-value, i.e., constant).
    corr3   = [_xml_escape_text(_resolve_batch_value(corr_address_line3_values, i)) for i in range(batches_count)]
    corrst  = [_xml_escape_text(_resolve_batch_value(corr_state_values, i)) for i in range(batches_count)]
    corrbi  = [_xml_escape_text(_resolve_batch_value(corr_bank_id_values, i)) for i in range(batches_count)]
    corrbn  = [_xml_escape_text(_resolve_batch_value(corr_bank_name_values, i)) for i in range(batches_count)]
    corra   = [_xml_escape_text(_resolve_batch_value(corr_routing_aba_values, i)) for i in range(batches_count)]
    pyeacc  = [_xml_escape_text(_resolve_batch_value(payee_bank_account_values, i)) for i in range(batches_count)]
    pyebi   = [_xml_escape_text(_resolve_batch_value(payee_bank_id_values, i)) for i in range(batches_count)]
    pyebn   = [_xml_escape_text(_resolve_batch_value(payee_bank_name_values, i)) for i in range(batches_count)]
    pyera   = [_xml_escape_text(_resolve_batch_value(payee_routing_aba_values, i)) for i in range(batches_count)]

    # Inner loop: pure string operations — no ElementTree, no deepcopy.
    batch_parts = []
    append = batch_parts.append
    for i in range(batches_count):
        s = (batch_tmpl
             .replace(P_ACCT,   account_numbers[i], 1)
             .replace(P_BENE1,  mig_bene1[i], 1)
             .replace(P_BENE2,  mig_bene2[i], 1)
             .replace(P_ORIG1,  mig_orig1[i], 1)
             .replace(P_ORIG2,  mig_orig2[i], 1)
             .replace(P_ORIGC,  mig_origc[i], 1)
             .replace(P_CORR3,  corr3[i], 1)
             .replace(P_CORRST, corrst[i], 1)
             .replace(P_CORRBI, corrbi[i], 1)
             .replace(P_CORRBN, corrbn[i], 1)
             .replace(P_CORRA,  corra[i], 1)
             .replace(P_PYEACC, pyeacc[i], 1)
             .replace(P_PYEBI,  pyebi[i], 1)
             .replace(P_PYEBN,  pyebn[i], 1)
             .replace(P_PYERA,  pyera[i], 1)
             )
        append(s)

    # Reconstruct full XML: root open tag + FileInformation + batches + root close tag.
    # This avoids re-serialising the entire n-batch tree with ET.tostring.
    root_tag = root.tag
    root_attribs = ''.join(f' {k}="{_xml_escape_text(v)}"' for k, v in root.attrib.items())
    non_batch_children = [child for child in list(root) if child.tag != 'Batch']
    header_str = ''.join(ET.tostring(child, encoding='unicode') for child in non_batch_children)

    return f'<{root_tag}{root_attribs}>{header_str}{"".join(batch_parts)}</{root_tag}>'


def _format_webseries_wire_filename(form_data):
    """Build download filename for WebSeries wire XML."""
    client_company = _sanitize_filename_token(form_data.get('wsClientCompany', ''), 'ClientCompany')
    bank_name = _sanitize_filename_token(form_data.get('wsBankNameCompany', ''), 'BankName')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{client_company}_{bank_name}_WEBSERIES_WIRE_{timestamp}.xml'


def generate_webseries_wire_xml_file(form_data):
    """Generate WebSeries Wire DOM XML from template using UI-provided values."""
    try:
        xml_content = _build_webseries_wire_xml_content(form_data)
        xml_io = BytesIO(xml_content.encode('utf-8'))
        xml_io.seek(0)

        return send_file(
            xml_io,
            mimetype='application/xml',
            as_attachment=True,
            download_name=_format_webseries_wire_filename(form_data)
        )
    except Exception as exc:
        return jsonify({'error': f'Error generating WebSeries Wire DOM XML: {str(exc)}'}), 400


def _build_webseries_bab_content(form_data):
    """Build WebSeries BAB content (header + repeated B lines + line 3)."""
    current_date = datetime.now().strftime('%Y%m%d')
    # 10 chars within requested 5-10 range; combines time entropy + random suffix.
    unique_token = f"{datetime.now().strftime('%H%M%S%f')[-6:]}{_random_alphanumeric(4)}"
    header_line = f'H,{current_date},{unique_token}'

    payment_type = str(
        form_data.get('babPaymentType', '') or form_data.get('paymentType', '')
    ).strip().upper()

    notebook_entries = _parse_webseries_bab_notebook_entries(form_data)
    if notebook_entries:
        notebook_entries = [
            _normalize_webseries_bab_notebook_entry(line, payment_type)
            for line in notebook_entries
        ]
        second_lines = [line for line in notebook_entries if line.startswith('B,')]
        third_lines = [line for line in notebook_entries if line.startswith('A,')]
        if not second_lines:
            raise ValueError('At least one second-row B record is required.')
        if not third_lines:
            raise ValueError('At least one third-row A record is required.')
        trailer_line = 'T,,,,,,,,,,,,,,,,,'
        return '\n'.join([header_line, *notebook_entries, trailer_line])

    migration_rows = _parse_webseries_migration_rows(form_data)
    beneficiary_count = _parse_webseries_bab_beneficiary_count(form_data)
    fallback_row = {
        'BENE_ADDRESS_1': '',
        'BENE_ADDRESS_2': ''
    }

    bene_reference = 'BeneReference' if payment_type in ('NACHA', 'BACS') else ''
    second_lines = []
    for beneficiary_index in range(beneficiary_count):
        selected_row = random.choice(migration_rows) if migration_rows else fallback_row
        bene_contact_name = f'Bene Contact {beneficiary_index + 1:02d}'
        second_lines.append(
            'B,,%s,%s,,,%s,%s,%s,AK,province,GB,post code,603-501-5470,888888,mg@bt.com,mg1@bt.com,mg2@bt.com' % (
                bene_contact_name,
                bene_reference,
                _sanitize_webseries_migration_value(selected_row.get('BENE_ADDRESS_1', '')),
                _sanitize_webseries_migration_value(selected_row.get('BENE_ADDRESS_2', '')),
                ''
            )
        )

    # Third line: A,<PaymentType>,<ClearingSystem>,<BeneName>,<BeneReference>,,,,,,,<Currency>,<AccountType>,<AccountNumber>,<BankCodeType>,<BankCode>
    third_line_payment_type, third_line_clearing = _map_webseries_bab_payment_fields(payment_type)
    third_line_count = _parse_webseries_bab_third_line_count(form_data)
    currency = _parse_webseries_bab_currency(form_data, payment_type)
    account_type = _parse_webseries_bab_account_type(form_data)
    account_number = _parse_optional_single_form_tag_value(form_data, 'babAccountNumber', 'Account Number')
    bank_code_type = re.sub(r'[^A-Za-z\-]', '', _parse_optional_single_form_tag_value(form_data, 'babBankCodeType', 'Bank Code Type'))
    bank_code = _parse_optional_single_form_tag_value(form_data, 'babBankCode', 'Bank Code')
    
    # Special handling for Cash Concentration/Disbursement
    if payment_type == 'CASH CONCENTRATION/DISBURSEMENT':
        # Map account type name to abbreviation (Savings->SV, Loans->CL, Checking/Checkings->DD)
        account_type = _map_account_type_to_abbreviation(account_type)
        # Set defaults for bank code type and code
        if not bank_code_type:
            bank_code_type = 'US-ACH'
        if not bank_code:
            bank_code = '021000018'

    third_lines = []
    for _ in range(third_line_count):
        bene_name = f"BeneName{random.randint(100000, 999999)}"
        third_lines.append('A,%s,%s,%s,%s,,,,,,,%s,%s,%s,%s,%s' % (
            third_line_payment_type,
            third_line_clearing,
            bene_name,
            bene_reference,
            currency,
            account_type,
            account_number,
            bank_code_type,
            bank_code
        ))

    trailer_line = 'T,,,,,,,,,,,,,,,,,'
    return '\n'.join([header_line, *second_lines, *third_lines, trailer_line])


def _format_webseries_bab_filename():
    """Build download filename for WebSeries BAB output."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'BAB_{timestamp}.txt'


def generate_webseries_bab_file(form_data):
    """Generate WebSeries BAB file (header line only for now)."""
    try:
        content = _build_webseries_bab_content(form_data)
        output_io = BytesIO(content.encode('utf-8'))
        output_io.seek(0)
        return send_file(
            output_io,
            mimetype='text/plain',
            as_attachment=True,
            download_name=_format_webseries_bab_filename()
        )
    except Exception as exc:
        return jsonify({'error': f'Error generating WebSeries BAB: {str(exc)}'}), 400


def _build_csv_wire_domestic_content(form_data):
    """Build .CSV Wire content supporting domestic, international, or both payment types.

    Amount and BeneName are generated fresh (unique) for every row.
    All other per-row values (FutureBusinessDate, OriginatorAccountNumber,
    BeneAccountNumber, BeneBankId/BeneABA) remain constant across rows of the same type.

    When both types are selected, all domestic rows come first, then all international rows.

    Wire-domestic row %s mapping (6 slots):
      1 – FutureBusinessDate     (yyyyMMdd)
      2 – AmountFormatted        (unique random 10.00–10000.00 per row)
      3 – OriginatorAccountNumber
      4 – BeneName               ('Wire Dom ' + 5 random chars, unique per row)
      5 – BeneAccountNumber
      6 – BeneBankId             (default '053000196')

    Wire-international row %s mapping (7 slots, USD hardcoded):
      1 – FutureBusinessDate
      2 – AmountFormatted        (unique random per row)
      3 – OriginatorAccountNumber
      4 – BeneName               ('Wire Int ' + 5 random chars, unique per row)
      5 – BeneAccountNumber
      6 – BeneName               (same value as slot 4)
      7 – BeneABA                (default '053000196')
    """
    current_date_yyyymmdd = datetime.now().strftime('%Y%m%d')
    file_header_template = 'H,%s,%s,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
    first_line = file_header_template % (current_date_yyyymmdd, _random_alphanumeric(32))

    # FutureBusinessDate: accept either a yyyyMMdd date string from the UI
    # or a small integer representing days-ahead.  Default to 1 business day ahead.
    raw_fbd = str(form_data.get('futureBusinessDate', '') or '').strip()
    if len(raw_fbd) == 8 and raw_fbd.isdigit():
        # Already a formatted yyyyMMdd date – use it directly.
        future_business_date_str = raw_fbd
    elif raw_fbd.isdigit() and int(raw_fbd) < 10000:
        # Small number treated as days-ahead (0 = today, 1 = next business day, etc.)
        future_business_date_str = _future_business_date_yyyymmdd(int(raw_fbd))
    else:
        # No value supplied or unrecognised format – default to next business day.
        future_business_date_str = _future_business_date_yyyymmdd(1)

    # Determine which payment type(s) to include.
    wire_payment_type = str(
        form_data.get('wirePaymentType', '') or form_data.get('paymentType', '')
    ).strip().lower()

    include_domestic = (
        'domestic' in wire_payment_type
        or wire_payment_type in ('', 'uswire', 'dom', 'both')
        or (not wire_payment_type)
    )
    include_international = (
        'international' in wire_payment_type
        or wire_payment_type in ('int', 'international', 'both')
    )
    # If both keywords present (e.g. "domestic,international" or "both"), enable both.
    if 'both' in wire_payment_type or ('domestic' in wire_payment_type and 'international' in wire_payment_type):
        include_domestic = True
        include_international = True
    # Safety: default to domestic only if nothing was resolved.
    if not include_domestic and not include_international:
        include_domestic = True

    # Shared constant fields (same value reused across all rows of the same type).
    originator_accounts_raw = form_data.get('originatorAccountNumber', '')
    bene_accounts_raw = form_data.get('beneAccountNumber', '')

    detail_lines = []

    # ── Wire-Domestic rows (all domestic first) ─────────────────────────────
    if include_domestic:
        dom_tx_count = 1
        for key in ('wireDomesticTransactionsCount', 'wireDomesticTransactionCount', 'transactionsCount'):
            raw_value = str(form_data.get(key, '')).strip()
            if raw_value:
                dom_tx_count = _parse_positive_int_csv(raw_value, default_value=1)[0]
                break

        dom_originator_accounts = _parse_wire_values_for_transactions(
            originator_accounts_raw, dom_tx_count, 'OriginatorAccountNumber'
        )
        dom_bene_accounts = _parse_wire_values_for_transactions(
            bene_accounts_raw, dom_tx_count, 'BeneAccountNumber'
        )
        bene_bank_ids = _parse_wire_values_for_transactions(
            form_data.get('beneBankId', '053000196') or '053000196',
            dom_tx_count, 'BeneBankId'
        )

        dom_line_template = (
            'USWIRE,%s,%s,CUSTREF,%s,%s,ABA,%s,BRIGHTWATER HEIGHTS,HORESHOE,HENDERSONVILLE,12131,US,'
            'BONY,ABA,%s,LINE1,,,US,BEN,DETAILS1,details2,detail3,detail4,,,,,,,,comments,banktobank1,'
            'banktobank2,banktobank3,banktobank4'
        )
        for tx_index in range(dom_tx_count):
            # Amount and BeneName are unique per row; all other values are constant.
            amount_formatted = f"{10 + random.random() * (10000 - 10):.2f}"
            bene_name = 'Wire Dom ' + _random_alphanumeric(5)
            detail_lines.append(dom_line_template % (
                future_business_date_str,                                        # %s 1 – constant
                amount_formatted,                                                # %s 2 – unique per row
                _resolve_batch_value(dom_originator_accounts, tx_index),        # %s 3 – constant
                bene_name,                                                       # %s 4 – unique per row
                _resolve_batch_value(dom_bene_accounts, tx_index),              # %s 5 – constant
                _resolve_batch_value(bene_bank_ids, tx_index)                   # %s 6 – constant
            ))

    # ── Wire-International rows (all international after domestic) ───────────
    if include_international:
        int_tx_count = 1
        for key in ('wireInternationalTransactionsCount', 'wireInternationalTransactionCount', 'transactionsCount'):
            raw_value = str(form_data.get(key, '')).strip()
            if raw_value:
                int_tx_count = _parse_positive_int_csv(raw_value, default_value=1)[0]
                break

        int_originator_accounts = _parse_wire_values_for_transactions(
            form_data.get('intlOriginatorAccountNumber', '') or originator_accounts_raw,
            int_tx_count, 'OriginatorAccountNumber'
        )
        int_bene_accounts = _parse_wire_values_for_transactions(
            form_data.get('intlBeneAccountNumber', '') or bene_accounts_raw,
            int_tx_count, 'BeneAccountNumber'
        )
        bene_abas = _parse_wire_values_for_transactions(
            form_data.get('beneABA', '053000196') or '053000196',
            int_tx_count, 'BeneABA'
        )

        # Template with 8 dynamic %s placeholders for wire international payments
        int_line_template = (
            'INT,%s,%s,Cust Ref,%s,%s,,,,%s,Other,%s,beneaddline1,beneaddline2,beneCity,23456,US,'
            '%s,ABA,%s,benebankadd1,benebankadd2,benebankCity,US,OUR,OBIText1,OBIText2,OBIText3,'
            'OBIText4,,ABA,,intermeadd1,intermeadd2,intermeCity,US,SpecialInstructions,'
            'InstructionsToBeneBank1,InstructionsToBeneBank2,InstructionsToBeneBank3,'
            'InstructionsToBeneBank4'
        )
        for tx_index in range(int_tx_count):
            # Amount and BeneName are unique per row; all other values are constant.
            amount_formatted = f"{10 + random.random() * (10000 - 10):.2f}"
            bene_name = 'Wire Int ' + _random_alphanumeric(5)
            detail_lines.append(int_line_template % (
                future_business_date_str,                                        # %s 1 – futureBusinessDate (yyyyMMdd)
                amount_formatted,                                                # %s 2 – amountFormatted
                'USD',                                                           # %s 3 – PaymentCurrency (hardcoded)
                _resolve_batch_value(int_originator_accounts, tx_index),        # %s 4 – OriginatorAccountNumber
                bene_name,                                                       # %s 5 – beneName
                _resolve_batch_value(int_bene_accounts, tx_index),              # %s 6 – BeneAccountNumber
                bene_name,                                                       # %s 7 – beneName (same as slot 5)
                _resolve_batch_value(bene_abas, tx_index)                       # %s 8 – BeneABA
            ))

    # Add trailer line once at the end of all payment records
    detail_lines.append('T,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,')

    return '\n'.join([first_line] + detail_lines) + '\n'


def _build_ach_file_content(form_data):
    """Build .ACH content with file header once, per-batch rows, and file control once."""
    immediate_destination = str(form_data.get('immediateDestination', '')).strip()
    immediate_origin = str(form_data.get('immediateOrigin', '')).strip()
    immediate_destination_name = str(form_data.get('immediateDestinationName', '')).strip()
    immediate_origin_name = str(form_data.get('immediateOriginName', '')).strip()

    first_line = '101%s%s11072811554094101%s%s' % (
        _left_pad(immediate_destination, 10, ' '),
        _left_pad(immediate_origin, 10, ' '),
        _right_pad(immediate_destination_name, 23, ' '),
        _right_pad(immediate_origin_name, 31, ' ')
    )

    ach_company_names = _parse_csv_values(form_data.get('achCompNames', ''))
    ach_company_ids = _parse_csv_values(form_data.get('achCompIds', ''))
    payment_type = str(form_data.get('type', '')).strip()
    type_description = str(form_data.get('typeDescription', '')).strip()
    originating_dfi_identification = str(form_data.get('originatingDfiIdentification', '')).strip()

    # Align with provided Java logic: yyMMdd from getFutureBusinessDate(1).
    future_business_date = _future_business_date(1)

    batches_values = _parse_positive_int_csv(form_data.get('batchesQuantity', '1'), default_value=1)
    batch_count = batches_values[0] if batches_values else 1
    if batch_count <= 0:
        batch_count = 1

    transaction_code = str(form_data.get('transactionCode', '')).strip()
    receiving_dfi_identification = str(form_data.get('receivingDfiIdentification', '')).strip()
    dfi_account_number = str(form_data.get('dfiAccountNumber', '')).strip()
    identification_number = str(form_data.get('identificationNumber', '')).strip()

    # Payments per batch: either one shared value or one value for each batch.
    transactions_values = _parse_positive_int_csv(form_data.get('transactionsCount', '1'), default_value=1)
    if len(transactions_values) not in (1, batch_count):
        raise ValueError('Transactions Quantity must contain either one value for all batches or exactly one value per batch.')

    lines = [first_line]

    for batch_index in range(batch_count):
        ach_company_name = _resolve_batch_value(ach_company_names, batch_index)
        ach_company_id = _resolve_batch_value(ach_company_ids, batch_index)
        current_batch_sequence = batch_index + 1
        payments_size_for_batch = transactions_values[0] if len(transactions_values) == 1 else transactions_values[batch_index]

        second_line = '5200%sDAILY SETTLEMENT    %s%s%s042000%s   1%s%s' % (
            _right_pad(ach_company_name, 16, ' '),
            _right_pad(ach_company_id, 10, ' '),
            _left_pad(payment_type, 3, ' '),
            _right_pad(type_description, 10, ' '),
            future_business_date,
            _left_pad(originating_dfi_identification, 8, ' '),
            _left_pad(str(current_batch_sequence), 7, '0')
        )
        lines.append(second_line)

        for _ in range(payments_size_for_batch):
            amount_formatted = f"{10 + random.random() * (10000 - 10):.2f}"
            amount_numeric = amount_formatted.replace('.', '')
            receiving_company_name = 'ACH NACHA ' + ''.join(random.choices(string.ascii_letters + string.digits, k=5))

            third_line = '6%s%s%s%s%s%sGL0124000050000001' % (
                _left_pad(transaction_code, 2, ' '),
                _left_pad(receiving_dfi_identification, 8, ' '),
                _left_pad(dfi_account_number, 17, ' '),
                _left_pad(amount_numeric, 10, '0'),
                _right_pad(identification_number, 15, ' '),
                _right_pad(receiving_company_name, 22, ' ')
            )
            lines.append(third_line)

        fourth_line = '8200%s0006300006000000110000000000000000110220330                          12400005%s' % (
            _left_pad(str(payments_size_for_batch), 6, '0'),
            _left_pad(str(current_batch_sequence), 7, '0')
        )
        lines.append(fourth_line)

    fifth_line = '9%s000005000000080014700014000000110000000001320000' % (
        _left_pad(str(batch_count), 7, '0')
    )
    lines.append(fifth_line)

    return '\n'.join(lines) + '\n'


def _sanitize_filename_token(value, fallback='UNKNOWN'):
    """Normalize filename parts to safe token characters."""
    cleaned = re.sub(r'[^A-Za-z0-9_-]+', '', str(value or '').strip())
    return cleaned or fallback


def _parse_positive_int_csv(raw_value, default_value=1):
    """Parse comma-separated positive integers with fallback default."""
    parsed = []
    for value in _parse_csv_values(raw_value):
        if not value.isdigit():
            raise ValueError('Transactions Count accepts only numeric values greater than 0.')
        numeric_value = int(value)
        if numeric_value <= 0:
            raise ValueError('Transactions Count accepts only numeric values greater than 0.')
        parsed.append(numeric_value)
    return parsed or [default_value]


def _resolve_batch_value(values, index, fallback=''):
    """Resolve one value for current batch using single/shared or per-batch mapping."""
    if not values:
        return fallback
    if len(values) == 1:
        return values[0]
    if index < len(values):
        return values[index]
    return values[-1]


def _build_checks_xml_content(form_data):
    """Generate CHECKS XML using current form payload."""
    batches_values = _parse_positive_int_csv(form_data.get('batchesQuantity', '1'), default_value=1)
    batches_quantity = batches_values[0] if batches_values else 1
    if batches_quantity <= 0:
        batches_quantity = 1

    transactions_count = _parse_positive_int_csv(form_data.get('transactionsCount', '1'), default_value=1)
    if len(transactions_count) not in (1, batches_quantity):
        raise ValueError('Transactions Count must contain either one value for all batches or exactly one value per batch.')

    check_app_type = str(form_data.get('checkAppType', 'Name')).strip() or 'Name'
    check_apps = _parse_csv_values(form_data.get('checkAppValue', ''))
    check_profiles = _parse_csv_values(form_data.get('checkProfiles', ''))
    client_company = str(form_data.get('clientCompany', '')).strip()

    root = ET.Element('File')
    file_information = ET.SubElement(root, 'FileInformation')
    ET.SubElement(file_information, 'FileCreateDate').text = datetime.now().strftime('%Y-%m-%d')
    ET.SubElement(file_information, 'FileDescription').text = f"PAC T1 {datetime.now().strftime('%Y-%m-%d')}"
    ET.SubElement(file_information, 'FileVersion').text = 'XMLv1.1 CSv6.7.2'

    for batch_index in range(batches_quantity):
        batch = ET.SubElement(root, 'Batch')
        batch_info = ET.SubElement(batch, 'BatchInformation')
        ET.SubElement(batch_info, 'BatchDescription').text = f"Batch {''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        ET.SubElement(batch_info, 'EffectiveDate').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(batch_info, 'BatchStatus').text = 'AP'
        ET.SubElement(batch_info, 'BatchUserGroup').text = client_company

        app_value = _resolve_batch_value(check_apps, batch_index)
        if app_value:
            app_tag = 'ApplicationID' if check_app_type.upper() == 'ID' else 'ApplicationName'
            ET.SubElement(batch_info, app_tag).text = app_value

        transactions = ET.SubElement(batch, 'Transactions')
        tx_count = transactions_count[batch_index] if len(transactions_count) > 1 else transactions_count[0]
        profile_key = _resolve_batch_value(check_profiles, batch_index)

        for tx_index in range(tx_count):
            check = ET.SubElement(transactions, 'Check')
            if profile_key:
                ET.SubElement(check, 'ProfileKey').text = profile_key
            ET.SubElement(check, 'PayeeID').text = f"PayeeID-{batch_index + 1}-{tx_index + 1}"
            ET.SubElement(check, 'PayeeName1').text = f"PayeeName-{batch_index + 1}-{tx_index + 1}"
            ET.SubElement(check, 'TranAmount').text = f"{random.randint(1000, 50000) / 100:.2f}"

    ET.indent(root, space='    ')
    return ET.tostring(root, encoding='unicode')


def _normalize_check_recon_status(raw_status):
    """Return canonical Check Recon status code (P/S/V/X/Y) or empty string."""
    normalized = str(raw_status or '').strip().upper()
    legacy_to_code = {
        'OPEN': '',
        'PAID': 'P',
        'STOP': 'S',
        'VOID': 'V',
        'PDEX': 'X',
        'PDWN': 'Y'
    }
    code = legacy_to_code.get(normalized, normalized)
    return code if code in {'P', 'S', 'V', 'X', 'Y'} else ''


def _build_check_recon_content(form_data):
     """Build Check Recon CSV content from provided records."""
     # Parse checkReconRecords JSON string from form data
     records_json = form_data.get('checkReconRecords', '[]')
     if isinstance(records_json, str):
         try:
             records = json.loads(records_json)
         except (json.JSONDecodeError, TypeError):
             records = []
     else:
         records = records_json if isinstance(records_json, list) else []

     if not isinstance(records, list):
         records = []

     # Build CSV content with headers
     lines = ['AccountNumber,CheckNumber,Amount,PaymentDate,Status,PayeeName']

     for record in records:
         if not isinstance(record, dict):
             continue

         account_number = str(record.get('accountNumber', '')).strip()
         check_number = str(record.get('checkNumber', '')).strip()
         transaction_amount = str(record.get('transactionAmount', '')).strip().replace(',', '')
         payment_date = str(record.get('paymentDate', '')).strip()
         status = _normalize_check_recon_status(record.get('status', ''))
         payee_name = str(record.get('payeeName', '')).strip()

         # Format the row (sanitize values for CSV)
         row = f'{account_number},{check_number},{transaction_amount},{payment_date},{status},{payee_name}'
         lines.append(row)

     return '\n'.join(lines) + '\n'


def _format_check_recon_filename(form_data):
     """Generate filename for Check Recon file."""
     client_company = _sanitize_filename_token(form_data.get('clientCompany', ''), 'ClientCompany')
     bank_name = _sanitize_filename_token(form_data.get('bankName', ''), 'BankName')
     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
     return f'{client_company}_{bank_name}_CHECK_RECON_{timestamp}.txt'


def generate_check_recon_file(form_data):
     """Generate Check Recon text file from form payload."""
     try:
         csv_content = _build_check_recon_content(form_data)
         csv_io = BytesIO(csv_content.encode('utf-8'))
         csv_io.seek(0)

         download_name = _format_check_recon_filename(form_data)

         return send_file(
             csv_io,
             mimetype='text/plain',
             as_attachment=True,
             download_name=download_name
         )
     except Exception as e:
         return jsonify({'error': f'Error generating Check Recon file: {str(e)}'}), 400


def generate_ach_file(form_data):
     """Generate .ACH file content from ACH FILE form payload."""
     try:
         ach_content = _build_ach_file_content(form_data)
         ach_io = BytesIO(ach_content.encode('utf-8'))
         ach_io.seek(0)

         client_company = _sanitize_filename_token(form_data.get('clientCompany', ''), 'ClientCompany')
         bank_name = _sanitize_filename_token(form_data.get('bankName', ''), 'BankName')
         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
         download_name = f'{client_company}_{bank_name}_ACH_{timestamp}.ACH'

         return send_file(
             ach_io,
             mimetype='application/octet-stream',
             as_attachment=True,
             download_name=download_name
         )
     except Exception as e:
         return jsonify({'error': f'Error generating ACH file: {str(e)}'}), 400


def _purge_expired_wire_csv_previews(now_ts=None):
    now_ts = now_ts if now_ts is not None else time.time()
    expired_tokens = [
        token for token, entry in _wire_csv_preview_cache.items()
        if now_ts - float(entry.get('created_at', 0)) > WIRE_CSV_PREVIEW_TTL_SEC
    ]
    for token in expired_tokens:
        _wire_csv_preview_cache.pop(token, None)


def _consume_wire_csv_preview_content(preview_token):
    token = str(preview_token or '').strip()
    if not token:
        return None

    with _wire_csv_preview_lock:
        _purge_expired_wire_csv_previews()
        cached = _wire_csv_preview_cache.pop(token, None)

    if not cached:
        return None
    return cached.get('content')


def generate_csv_wire_domestic_file(form_data):
    """Generate .CSV Wire Domestic file content from form payload."""
    try:
        csv_content = _consume_wire_csv_preview_content(form_data.get('wireCsvPreviewToken'))
        if not csv_content:
            csv_content = _build_csv_wire_domestic_content(form_data)

        csv_io = BytesIO(csv_content.encode('utf-8'))
        csv_io.seek(0)

        client_company = _sanitize_filename_token(
            form_data.get('clientCompany') or form_data.get('csvClientCompany', ''),
            'ClientCompany'
        )
        bank_name = _sanitize_filename_token(
            form_data.get('bankName') or form_data.get('csvBankName', ''),
            'BankName'
        )
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f'{client_company}_{bank_name}_WIRE_{timestamp}.csv'

        return send_file(
            csv_io,
            mimetype='text/csv',
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        return jsonify({'error': f'Error generating CSV Wire Domestic file: {str(e)}'}), 400


def _combine_generated_xml(xml_contents):
    """Merge multiple generated XML documents into one <File> with combined <Batch> nodes."""
    if not xml_contents:
        raise ValueError('No form data found for Mix File generation')

    merged_root = ET.Element('File')
    file_information_added = False

    for xml_content in xml_contents:
        root = ET.fromstring(xml_content)
        if root.tag != 'File':
            raise ValueError('Generated XML root must be <File>')

        file_information = root.find('FileInformation')
        if file_information is not None and not file_information_added:
            merged_root.append(deepcopy(file_information))
            file_information_added = True

        for batch in root.findall('Batch'):
            merged_root.append(deepcopy(batch))

    if not file_information_added:
        file_info = ET.SubElement(merged_root, 'FileInformation')
        ET.SubElement(file_info, 'FileCreateDate').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(file_info, 'FileDescription').text = f'PAC T1 {datetime.now().strftime("%Y-%m-%d")}'
        ET.SubElement(file_info, 'FileVersion').text = 'XMLv1.1 CSv6.7.2'

    ET.indent(merged_root, space='    ')
    return ET.tostring(merged_root, encoding='unicode')

def generate_ach_nacha_xml(form_data):
    """
    Generate ACH NACHA payment file XML

    Process:
    1. Extract and structure form data into PaymentData object
    2. Map fields to XML template placeholders
    3. Generate complete XML content
    4. Return as downloadable file
    """
    try:
        xml_content = _build_xml_content_from_form(form_data)
        file_type = form_data.get('fileType', 'ACH NACHA XML')
        # Convert to bytes
        xml_bytes = xml_content.encode('utf-8')
        xml_io = BytesIO(xml_bytes)
        xml_io.seek(0)

        return send_file(
            xml_io,
            mimetype='application/xml',
            as_attachment=True,
            download_name='checks_payment.xml' if file_type == 'CHECKS XML' else (
                'ach_caeft_payment.xml' if file_type == 'ACH CAEFT XML' else 'ach_nacha_payment.xml'
            )
        )

    except FileNotFoundError as e:
        return jsonify({'error': f'Template file not found: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error generating XML: {str(e)}'}), 400

def _users_root_path():
    """Return the root Users folder to scope directory browsing."""
    if os.name == 'nt':
        system_drive = os.environ.get('SystemDrive', 'C:')
        drive_root = f"{system_drive}{os.sep}"
        return os.path.abspath(os.path.join(drive_root, 'Users'))
    return os.path.abspath(os.path.expanduser('~'))


def _is_within_root(path_value, root_path):
    """Check that path_value is inside root_path."""
    try:
        normalized_path = os.path.normcase(os.path.abspath(path_value))
        normalized_root = os.path.normcase(os.path.abspath(root_path))
        return os.path.commonpath([normalized_path, normalized_root]) == normalized_root
    except ValueError:
        return False


def _safe_abs_path(path_value):
    """Normalize a requested path and ensure it points to a valid scoped directory."""
    users_root = _users_root_path()

    if not path_value:
        path_value = users_root

    abs_path = os.path.abspath(path_value)
    if not os.path.isdir(abs_path):
        raise ValueError('Invalid directory path')

    if not _is_within_root(abs_path, users_root):
        raise ValueError('Only directories inside Users are allowed')

    return abs_path


def _directory_entries(dir_path):
    """Return one-level child directories and files."""
    entries = []
    with os.scandir(dir_path) as scandir_iter:
        for item in scandir_iter:
            try:
                is_dir = item.is_dir(follow_symlinks=False)
            except OSError:
                continue

            entries.append({
                'name': item.name,
                'path': item.path,
                'entryType': 'directory' if is_dir else 'file'
            })

    entries.sort(key=lambda e: (e['entryType'] != 'directory', e['name'].lower()))
    return entries


@app.route('/api/directory-tree', methods=['GET'])
def directory_tree():
    """Expose a read-only Users-scoped directory listing for the Drop File modal."""
    try:
        users_root = _users_root_path()
        requested_path = request.args.get('path', '')
        dir_path = _safe_abs_path(requested_path)
        entries = _directory_entries(dir_path)

        parent_path = os.path.dirname(dir_path)
        if not parent_path or not _is_within_root(parent_path, users_root) or parent_path == dir_path:
            parent_path = None

        return jsonify({
            'path': dir_path,
            'rootPath': users_root,
            'parentPath': parent_path,
            'entries': entries
        })
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except PermissionError:
        return jsonify({'error': 'Permission denied for this directory'}), 403
    except OSError as exc:
        return jsonify({'error': f'Unable to read directory: {str(exc)}'}), 400


@app.route('/api/connection-info', methods=['GET'])
def get_connection_info():
    """Return persisted connection information for all connection sections."""
    connection_info = _read_connection_info()
    return jsonify(connection_info)


@app.route('/api/preseed-files', methods=['GET'])
def get_preseed_files():
    """Return available pre-seed file names for selected environment/usergroup/payment form."""
    environment = (request.args.get('environment') or '').strip()
    usergroup = (request.args.get('usergroup') or '').strip()
    payment_form = (request.args.get('paymentForm') or '').strip()

    if not environment or not usergroup or not payment_form:
        return jsonify({'error': 'environment, usergroup, and paymentForm are required'}), 400

    try:
        file_map = _get_preseed_file_map(environment, usergroup, payment_form)
        return jsonify({'files': list(file_map.keys())})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except LookupError as exc:
        return jsonify({'error': str(exc)}), 404


@app.route('/api/preseed-values', methods=['GET'])
def get_preseed_values():
    """Return pre-seed values for selected environment/usergroup/payment form/file."""
    environment = (request.args.get('environment') or '').strip()
    usergroup = (request.args.get('usergroup') or '').strip()
    payment_form = (request.args.get('paymentForm') or '').strip()
    file_name = (request.args.get('fileName') or '').strip()

    if not environment or not usergroup or not payment_form or not file_name:
        return jsonify({'error': 'environment, usergroup, paymentForm, and fileName are required'}), 400

    try:
        file_map = _get_preseed_file_map(environment, usergroup, payment_form)
        values = file_map.get(file_name)
        if not isinstance(values, dict):
            return jsonify({'error': f'File {file_name} not found'}), 404
        return jsonify({'values': values})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except LookupError as exc:
        return jsonify({'error': str(exc)}), 404


@app.route('/api/preseed-environments', methods=['GET'])
def get_preseed_environments():
    """Return list of available environments from YAML config."""
    config_data = _read_preseed_config()
    environments = config_data.get('environments', {})
    if not isinstance(environments, dict):
        return jsonify({'environments': []})
    return jsonify({'environments': sorted(list(environments.keys()))})


@app.route('/api/preseed-usergroups', methods=['GET'])
def get_preseed_usergroups():
    """Return list of usergroups for a given environment from YAML config."""
    environment = (request.args.get('environment') or '').strip()
    if not environment:
        return jsonify({'error': 'environment is required'}), 400

    config_data = _read_preseed_config()
    environments = config_data.get('environments', {})
    env_node = environments.get(environment)
    if not isinstance(env_node, dict):
        return jsonify({'usergroups': []})

    return jsonify({'usergroups': sorted(list(env_node.keys()))})

@app.route('/api/connection-info', methods=['POST'])
def update_connection_info():
    """Update and persist connection information for all connection sections."""
    payload = request.get_json(silent=True) or {}
    normalized_data = _normalize_connection_info(payload)
    _write_connection_info(normalized_data)
    _invalidate_sftp_state()
    return jsonify(normalized_data)


@app.route('/api/login-credentials', methods=['GET'])
def get_login_credentials():
    """Return persisted login credentials."""
    login_creds = _read_login_credentials()
    return jsonify(login_creds)


@app.route('/api/login-credentials', methods=['POST'])
def update_login_credentials():
    """Update and persist login credentials."""
    payload = request.get_json(silent=True) or {}
    normalized_data = _normalize_login_credentials(payload)
    _write_login_credentials(normalized_data)
    _invalidate_sftp_state()
    return jsonify(normalized_data)


@app.route('/api/sftp-directory', methods=['GET'])
def sftp_directory():
    """Connect to SFTP server and list remote directory structure."""
    try:
        saas_section = request.args.get('saas', 'saasN')
        remote_path = _normalize_remote_path(request.args.get('path', '/') or '/')

        now_ts = time.time()
        _evict_idle_sftp_sessions(now_ts)
        _sweep_directory_cache(now_ts)

        try:
            server_key, hostname, port, username, password = _resolve_sftp_target(saas_section)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 401
        except LookupError as exc:
            return jsonify({'error': str(exc)}), 400

        cached_payload = _read_cached_directory(server_key, remote_path)
        if cached_payload:
            return jsonify(cached_payload)

        try:
            _, sftp = _get_or_create_sftp_session(server_key, hostname, port, username, password)

            # List directory contents
            entries = []
            try:
                dir_list = sftp.listdir_attr(remote_path)

                for item in dir_list:
                    # Check if it's a directory using stat
                    is_dir = stat.S_ISDIR(item.st_mode)

                    entries.append({
                        'name': item.filename,
                        'path': remote_path.rstrip('/') + '/' + item.filename if remote_path != '/' else '/' + item.filename,
                        'entryType': 'directory' if is_dir else 'file',
                        'size': item.st_size,
                        'modified': item.st_mtime
                    })

                # Sort: directories first, then by name
                entries.sort(key=lambda e: (e['entryType'] != 'directory', e['name'].lower()))

            except IOError as e:
                return jsonify({'error': f'Permission denied for this directory'}), 403

            # Get parent path
            parent_path = None
            if remote_path != '/':
                parent_path = '/'.join(remote_path.rstrip('/').split('/')[:-1]) or '/'

            payload = {
                'path': remote_path,
                'parentPath': parent_path,
                'entries': entries
            }
            _write_cached_directory(server_key, remote_path, payload)
            _mark_session_used(server_key)
            return jsonify(payload)

        except paramiko.ssh_exception.AuthenticationException:
            _drop_session(server_key)
            return jsonify({'error': 'Authentication failed. Invalid credentials.'}), 401
        except paramiko.ssh_exception.SSHException as e:
            _drop_session(server_key)
            return jsonify({'error': f'SSH connection failed: {str(e)}'}), 500
        except Exception as e:
            _drop_session(server_key)
            return jsonify({'error': f'Connection error: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Error connecting to SFTP: {str(e)}'}), 400


@app.route('/api/sftp-upload-local', methods=['POST'])
def sftp_upload_local():
    """Read a file from the local server filesystem and upload it to SFTP (left→right panel transfer)."""
    try:
        payload     = request.get_json(silent=True) or {}
        saas_section = payload.get('saas', 'saasN')
        local_path   = payload.get('localPath', '').strip()
        remote_dir   = _normalize_remote_path(payload.get('remotePath', '/') or '/')

        if not local_path:
            return jsonify({'error': 'No local path provided'}), 400

        # Safety: path must exist and be a file
        if not os.path.isfile(local_path):
            return jsonify({'error': f'Local file not found: {local_path}'}), 404

        filename    = os.path.basename(local_path)
        remote_path = (remote_dir.rstrip('/') + '/' + filename) if remote_dir != '/' else '/' + filename

        try:
            server_key, hostname, port, username, password = _resolve_sftp_target(saas_section)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 401
        except LookupError as exc:
            return jsonify({'error': str(exc)}), 400

        try:
            _, sftp = _get_or_create_sftp_session(server_key, hostname, port, username, password)
            with open(local_path, 'rb') as local_file:
                sftp.putfo(local_file, remote_path)
            _mark_session_used(server_key)
            # Invalidate directory cache so listing refreshes
            with _sftp_pool_lock:
                _sftp_directory_cache.pop((server_key, remote_dir), None)
            return jsonify({'status': 'uploaded', 'filename': filename, 'remotePath': remote_path})
        except IOError as exc:
            return jsonify({'error': f'Permission denied uploading to {remote_path}'}), 403
        except paramiko.ssh_exception.AuthenticationException:
            _drop_session(server_key)
            return jsonify({'error': 'Authentication failed. Invalid credentials.'}), 401
        except paramiko.ssh_exception.SSHException as exc:
            _drop_session(server_key)
            return jsonify({'error': f'SSH error: {str(exc)}'}), 500
        except Exception as exc:
            _drop_session(server_key)
            return jsonify({'error': f'Upload error: {str(exc)}'}), 500

    except Exception as exc:
        return jsonify({'error': f'Error uploading file: {str(exc)}'}), 400


@app.route('/api/sftp-connect', methods=['POST'])
def sftp_connect():
    """Warm pooled SFTP session for faster first directory listing."""
    try:
        payload = request.get_json(silent=True) or {}
        saas_section = payload.get('saas', 'saasN')

        now_ts = time.time()
        _evict_idle_sftp_sessions(now_ts)
        _sweep_directory_cache(now_ts)

        try:
            server_key, hostname, port, username, password = _resolve_sftp_target(saas_section)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 401
        except LookupError as exc:
            return jsonify({'error': str(exc)}), 400

        try:
            _get_or_create_sftp_session(server_key, hostname, port, username, password)
            _mark_session_used(server_key)
            return jsonify({'status': 'connected', 'saas': saas_section})
        except paramiko.ssh_exception.AuthenticationException:
            _drop_session(server_key)
            return jsonify({'error': 'Authentication failed. Invalid credentials.'}), 401
        except paramiko.ssh_exception.SSHException as exc:
            _drop_session(server_key)
            return jsonify({'error': f'SSH connection failed: {str(exc)}'}), 500
        except Exception as exc:
            _drop_session(server_key)
            return jsonify({'error': f'Connection error: {str(exc)}'}), 500
    except Exception as exc:
        return jsonify({'error': f'Error connecting to SFTP: {str(exc)}'}), 400


@app.route('/api/sftp-upload', methods=['POST'])
def sftp_upload():
    """Upload a file from the client to the active SFTP server at the given remote path."""
    try:
        saas_section = request.form.get('saas', 'saasN')
        remote_dir = request.form.get('remotePath', '/') or '/'
        remote_dir = _normalize_remote_path(remote_dir)

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        uploaded_file = request.files['file']
        if not uploaded_file.filename:
            return jsonify({'error': 'Empty filename'}), 400

        filename = os.path.basename(uploaded_file.filename)
        remote_path = (remote_dir.rstrip('/') + '/' + filename) if remote_dir != '/' else '/' + filename

        try:
            server_key, hostname, port, username, password = _resolve_sftp_target(saas_section)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 401
        except LookupError as exc:
            return jsonify({'error': str(exc)}), 400

        try:
            _, sftp = _get_or_create_sftp_session(server_key, hostname, port, username, password)
            file_bytes = uploaded_file.read()
            with sftp.open(remote_path, 'wb') as remote_file:
                remote_file.write(file_bytes)
            _mark_session_used(server_key)
            # Invalidate cache for the destination directory so refresh shows new file
            with _sftp_pool_lock:
                _sftp_directory_cache.pop((server_key, remote_dir), None)
            return jsonify({
                'status': 'uploaded',
                'filename': filename,
                'remotePath': remote_path
            })
        except IOError as exc:
            return jsonify({'error': f'Permission denied uploading to {remote_path}'}), 403
        except paramiko.ssh_exception.AuthenticationException:
            _drop_session(server_key)
            return jsonify({'error': 'Authentication failed. Invalid credentials.'}), 401
        except paramiko.ssh_exception.SSHException as exc:
            _drop_session(server_key)
            return jsonify({'error': f'SSH error: {str(exc)}'}), 500
        except Exception as exc:
            _drop_session(server_key)
            return jsonify({'error': f'Upload error: {str(exc)}'}), 500

    except Exception as exc:
        return jsonify({'error': f'Error uploading file: {str(exc)}'}), 400


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', '5001')))

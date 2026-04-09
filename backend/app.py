from flask import Flask, request, jsonify, send_file
import os
import re
import json
import xml.etree.ElementTree as ET
import stat
import time
import atexit
from io import BytesIO
from datetime import datetime
import random
import string
from copy import deepcopy
from threading import Lock
from payment_generator import PaymentData, XMLFieldMapper, ACHNachaXMLGenerator
import paramiko
from paramiko import SSHClient, AutoAddPolicy

app = Flask(__name__)

CONNECTION_INFO_FILE = os.path.join(os.path.dirname(__file__), 'connection_info.json')
CONNECTION_PROTOCOLS = ['SFTP', 'SCP', 'FTP', 'WebDAV', 'Amazon S3']
LOGIN_CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'login_credentials.json')
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
    """Generate ACH NACHA payment XML file"""
    try:
        form_data = request.get_json()
        file_type = form_data.get('fileType', 'ACH NACHA XML')

        if file_type == 'ACH NACHA XML':
            return generate_ach_nacha_xml(form_data)
        else:
            return jsonify({'error': f'File type {file_type} not yet implemented'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
        # Get template directory
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')

        # Step 1: Convert form data to structured PaymentData object
        payment_data = PaymentData.from_form_data(form_data)

        # Log the structured data (for debugging)
        print(f"Payment Data: {payment_data.to_dict()}")

        # Step 2: Initialize XML generator with template directory
        xml_generator = ACHNachaXMLGenerator(template_dir)

        # Step 3: Generate complete XML content
        xml_content = xml_generator.generate(payment_data)



        # Convert to bytes
        xml_bytes = xml_content.encode('utf-8')
        xml_io = BytesIO(xml_bytes)
        xml_io.seek(0)

        return send_file(
            xml_io,
            mimetype='application/xml',
            as_attachment=True,
            download_name='ach_nacha_payment.xml'
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
    app.run(debug=True)

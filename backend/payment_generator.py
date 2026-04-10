"""
Payment File Generator Module
Handles structured data extraction from UI form and mapping to XML templates
"""

from datetime import datetime
import os
import random
import string
from typing import Dict, List, Any


class PaymentData:
    """Structured data class for payment file generation"""

    def __init__(self):
        # Basic Information
        self.file_type: str = ''

        # Batch Information
        self.batches_quantity: int = 1
        self.transactions_count: int = 1

        # ACH Company Information
        self.comp_ids: str = ''
        self.comp_names: str = ''
        self.client_company: str = ''

        # Bank Information
        self.abas: List[str] = []
        self.bank_name: str = ''

        # Payment Type Information
        self.payment_type: str = 'CCD'  # CCD, CTX, PPD, IAT
        self.options: str = 'ACH'  # ACH, ACH & ESend, ESend_Only

        # Payee Information (Optional - BAB)
        self.payee_ids: str = ''
        self.payee_lookup_type: str = 'No Flag'  # No Flag, DB, FILE, NONE
        self.payee_lookup_elements: List[str] = []

        # ESend Information (Optional)
        self.esend_app_type: str = 'Name'  # Name or ID
        self.esend_app_value: str = ''
        self.esend_profile_keys: str = ''
        self.payee_emails: str = ''

        # CAEFT-specific Information
        self.funding_account_number: str = ''
        self.return_account_number: str = ''
        self.account_number: str = ''
        self.batch_credit_debit: str = 'Credit'
        self.transaction_credit_debit: str = 'Credit'

        # Metadata
        self.creation_date: str = datetime.now().strftime('%Y-%m-%d')

    @classmethod
    def from_form_data(cls, form_data: Dict[str, Any]) -> 'PaymentData':
        """
        Create PaymentData instance from UI form data

        Args:
            form_data: Dictionary containing form field values

        Returns:
            PaymentData instance with populated values
        """
        data = cls()

        # Basic Information
        data.file_type = form_data.get('fileType', 'ACH NACHA XML')

        # Parse quantities
        try:
            data.batches_quantity = int(form_data.get('batchesQuantity', 1))
        except (ValueError, TypeError):
            data.batches_quantity = 1

        try:
            data.transactions_count = int(form_data.get('transactionsCount', 1))
        except (ValueError, TypeError):
            data.transactions_count = 1

        # ACH Company Information
        data.comp_ids = form_data.get('achCompIds', '').strip()
        data.comp_names = form_data.get('achCompNames', '').strip()
        data.client_company = form_data.get('clientCompany', '').strip()

        # Bank Information
        abas_str = form_data.get('abas', '').strip()
        data.abas = [aba.strip() for aba in abas_str.split(',') if aba.strip()]
        data.bank_name = form_data.get('bankName', '').strip()

        # Payment Type Information
        data.payment_type = form_data.get('type', 'CCD')
        data.options = form_data.get('options', 'ACH')

        # Payee Information (Optional)
        data.payee_ids = form_data.get('payeeIds', '').strip()
        data.payee_lookup_type = form_data.get('payeeLookupType', 'No Flag')
        payee_elements_str = form_data.get('payeeLookupElements', '').strip()
        data.payee_lookup_elements = [elem.strip() for elem in payee_elements_str.split(',') if elem.strip()]

        # ESend Information (Optional)
        data.esend_app_type = form_data.get('esendAppType', 'Name')
        data.esend_app_value = form_data.get('esendAppValue', '').strip()
        data.esend_profile_keys = form_data.get('esendProfileKeys', '').strip()
        data.payee_emails = form_data.get('payeeEmails', '').strip()

        # CAEFT-specific Information
        data.funding_account_number = form_data.get('fundingAccountNumber', '').strip()
        data.return_account_number = form_data.get('returnAccountNumber', '').strip()
        data.account_number = form_data.get('accountNumber', '').strip()
        batch_credit_debit = form_data.get('batchCreditDebit', 'Credit')
        data.batch_credit_debit = batch_credit_debit if batch_credit_debit in ('Credit', 'Debit') else 'Credit'
        transaction_credit_debit = form_data.get('transactionCreditDebit', 'Credit')
        data.transaction_credit_debit = transaction_credit_debit if transaction_credit_debit in ('Credit', 'Debit') else 'Credit'

        return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert PaymentData to dictionary for logging/debugging"""
        return {
            'file_type': self.file_type,
            'batches_quantity': self.batches_quantity,
            'transactions_count': self.transactions_count,
            'comp_ids': self.comp_ids,
            'comp_names': self.comp_names,
            'client_company': self.client_company,
            'abas': self.abas,
            'bank_name': self.bank_name,
            'payment_type': self.payment_type,
            'options': self.options,
            'payee_ids': self.payee_ids,
            'payee_lookup_type': self.payee_lookup_type,
            'payee_lookup_elements': self.payee_lookup_elements,
            'esend_app_type': self.esend_app_type,
            'esend_app_value': self.esend_app_value,
            'esend_profile_keys': self.esend_profile_keys,
            'payee_emails': self.payee_emails,
            'funding_account_number': self.funding_account_number,
            'return_account_number': self.return_account_number,
            'account_number': self.account_number,
            'batch_credit_debit': self.batch_credit_debit,
            'transaction_credit_debit': self.transaction_credit_debit,
            'creation_date': self.creation_date
        }


class XMLFieldMapper:
    """Maps PaymentData fields to XML template placeholders"""

    @staticmethod
    def get_batch_values(payment_data: PaymentData, batch_index: int = 0) -> Dict[str, str]:
        """
        Get values for batch XML template

        Mapping:
        - BatchDescription: "Batch" + random text
        - CompanyID: achCompIds field value
        - CompanyName: achCompNames field value
        - EffectiveDate: today's date in YYYY-MM-DD format
        - BatchStatus: "AP"
        - BatchUserGroup: clientCompany field value
        """
        return {
            'batch_description': f"Batch {XMLFieldMapper.generate_random_string(4)}",
            'company_id': payment_data.comp_ids,
            'company_name': payment_data.comp_names,
            'effective_date': payment_data.creation_date,
            'batch_status': 'AP',
            'batch_user_group': payment_data.client_company
        }

    @staticmethod
    def get_payment_values(payment_data: PaymentData,
                          transaction_index: int = 0,
                          batch_index: int = 0) -> Dict[str, str]:
        """
        Get values for payment XML template

        Mapping:
        - AccountNumber: random 6-8 digit number
        - ABA: ABAs field value (cycle through list if multiple)
        - PayeeEntity: "PayeeEntity-" + random number
        - PayeeID: "PayeeID-" + random number
        - PayeeName1: "PayeeName1-" + random number
        - TranAmount: random amount with decimal (e.g., 100.00)
        - TranDescription: "Payment"
        - NachaTranType: payment_type field value
        - TranDate: today's date in YYYY-MM-DD format
        """

        # Get ABA - cycle through list if multiple ABAs provided
        if payment_data.abas:
            aba = payment_data.abas[transaction_index % len(payment_data.abas)]
        else:
            aba = XMLFieldMapper.generate_random_number(100000000, 999999999)

        payee_ids = XMLFieldMapper._split_csv_values(payment_data.payee_ids)
        payee_id = payee_ids[transaction_index % len(payee_ids)] if payee_ids else f"PayeeID-{XMLFieldMapper.generate_random_number(1000, 9999)}"

        payee_emails = XMLFieldMapper._split_csv_values(payment_data.payee_emails)
        payee_email = (
            payee_emails[transaction_index % len(payee_emails)]
            if payee_emails else f"payee{XMLFieldMapper.generate_random_number(1000, 9999)}@example.com"
        )

        profile_keys = XMLFieldMapper._split_csv_values(payment_data.esend_profile_keys)
        profile_key = (
            profile_keys[transaction_index % len(profile_keys)]
            if profile_keys else f"Profile-{XMLFieldMapper.generate_random_number(1000, 9999)}"
        )

        app_name_value = payment_data.esend_app_value.strip() if payment_data.esend_app_value else ''
        app_name = app_name_value or f"ESendApp-{XMLFieldMapper.generate_random_number(100, 999)}"

        return {
            'nacha_type': payment_data.payment_type,
            'account_number': payment_data.account_number or XMLFieldMapper.generate_random_number(100000, 999999),
            'funding_account_number': payment_data.funding_account_number or XMLFieldMapper.generate_random_number(100000, 999999),
            'return_account_number': payment_data.return_account_number or XMLFieldMapper.generate_random_number(100000, 999999),
            'aba': aba,
            'payee_entity': f"PayeeEntity-{XMLFieldMapper.generate_random_number(1000, 9999)}",
            'payee_id': payee_id,
            'payee_name1': f"PayeeName1-{XMLFieldMapper.generate_random_number(1000, 9999)}",
            'payee_email': payee_email,
            'profile_key': profile_key,
            'esend_app_name': app_name,
            'originator_full_name': payment_data.comp_names or payment_data.client_company or 'Originator Full Name',
            'originator_short_name': payment_data.client_company or payment_data.comp_names or 'Originator',
            'batch_credit_debit': payment_data.batch_credit_debit,
            'transaction_credit_debit': payment_data.transaction_credit_debit,
            'tran_amount': XMLFieldMapper.generate_random_amount(),
            'tran_date': payment_data.creation_date,
            'tran_description': 'Payment'
        }

    @staticmethod
    def _split_csv_values(raw_value: str) -> List[str]:
        """Split comma-separated UI values into cleaned items."""
        if not raw_value:
            return []
        return [item.strip() for item in raw_value.split(',') if item.strip()]

    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """Generate a random string of given length"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    @staticmethod
    def generate_random_number(min_val: int, max_val: int) -> str:
        """Generate a random number between min and max"""
        return str(random.randint(min_val, max_val))

    @staticmethod
    def generate_random_amount() -> str:
        """Generate a random amount with two decimal places"""
        amount = random.randint(10000, 1000000)  # Amount in cents
        return f"{amount / 100:.2f}"


class ACHNachaXMLGenerator:
    """Generates ACH NACHA XML files from structured payment data"""

    def __init__(self, template_dir: str):
        """
        Initialize generator with template directory

        Args:
            template_dir: Directory containing XML template files
        """
        self.template_dir = template_dir
        self.file_header_template = self._load_template_file(['ach_nacha_file_header.xml'])
        self._template_cache = {}

    def _load_template_file(self, file_names: List[str]) -> str:
        """Load first existing template file from provided names."""
        for file_name in file_names:
            template_path = os.path.join(self.template_dir, file_name)
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as template_file:
                    return template_file.read().strip()
        raise FileNotFoundError(f"Template file not found. Tried: {', '.join(file_names)}")

    def _resolve_template_files(self, payment_data: PaymentData):
        """Select batch/payment templates based on type and options."""
        file_type = (payment_data.file_type or '').strip()
        payment_type = (payment_data.payment_type or '').strip().upper()
        options_value = (payment_data.options or '').strip().lower()
        is_iat = payment_type == 'IAT'
        has_esend = 'esend' in options_value and options_value != 'ach'

        if file_type == 'ACH CAEFT XML':
            if has_esend:
                return 'caeft_esend', 'batch_caeft_esend.xml', 'payment_caeft_esend.xml'
            return 'caeft', 'batch_caeft.xml', 'payment_caeft.xml'

        if is_iat and has_esend:
            return 'iat_esend', 'batch_iat_esend.xml', 'payment_iat_esend.xml'
        if is_iat:
            return 'iat', 'batch_iat.xml', 'payment_iat.xml'
        if has_esend:
            return 'esend', 'batch_esend.xml', 'payment_esend.xml'
        return 'standard', 'batch.xml', 'payment.xml'

    def _load_templates_for_mode(self, mode: str, batch_file: str, payment_file: str):
        """Load and cache templates for a given generation mode."""
        cache_key = (mode, batch_file, payment_file)
        cached = self._template_cache.get(cache_key)
        if cached:
            return cached

        batch_names = [batch_file]
        payment_names = [payment_file]
        if mode == 'standard':
            # Backward compatibility with existing template names.
            batch_names.append('ach_nacha_batch.xml')
            payment_names.append('ach_nacha_payment.xml')

        templates = (
            self._load_template_file(batch_names),
            self._load_template_file(payment_names)
        )
        self._template_cache[cache_key] = templates
        return templates

    def _format_payment_xml(self, mode: str, payment_template: str, payment_values: Dict[str, str]) -> str:
        """Format payment XML for selected mode-specific template."""
        if mode == 'standard':
            return payment_template % (
                payment_values['nacha_type'],
                payment_values['account_number'],
                payment_values['aba'],
                payment_values['payee_entity'],
                payment_values['payee_id'],
                payment_values['payee_name1'],
                payment_values['tran_amount'],
                payment_values['tran_date'],
                payment_values['tran_description'],
                payment_values['nacha_type']
            )

        if mode == 'esend':
            return payment_template % (
                payment_values['nacha_type'],
                payment_values['account_number'],
                payment_values['aba'],
                payment_values['payee_email'],
                payment_values['payee_id'],
                payment_values['payee_name1'],
                payment_values['tran_amount'],
                payment_values['tran_date'],
                payment_values['tran_description'],
                payment_values['profile_key'],
                payment_values['nacha_type']
            )

        if mode == 'iat':
            return payment_template % (
                payment_values['nacha_type'],
                payment_values['account_number'],
                payment_values['payee_id'],
                payment_values['payee_name1'],
                payment_values['tran_amount'],
                payment_values['tran_date'],
                payment_values['tran_description'],
                payment_values['nacha_type']
            )

        if mode == 'caeft':
            return payment_template % (
                payment_values['originator_full_name'],
                payment_values['originator_short_name'],
                payment_values['return_account_number'],
                payment_values['account_number'],
                payment_values['aba'],
                payment_values['payee_id'],
                payment_values['payee_name1'],
                payment_values['tran_amount'],
                payment_values['transaction_credit_debit']
            )

        if mode == 'caeft_esend':
            return payment_template % (
                payment_values['originator_full_name'],
                payment_values['originator_short_name'],
                payment_values['return_account_number'],
                payment_values['account_number'],
                payment_values['aba'],
                payment_values['payee_email'],
                payment_values['payee_id'],
                payment_values['payee_name1'],
                payment_values['tran_amount'],
                payment_values['transaction_credit_debit']
            )

        return payment_template % (
            payment_values['nacha_type'],
            payment_values['account_number'],
            payment_values['payee_id'],
            payment_values['payee_name1'],
            payment_values['payee_email'],
            payment_values['tran_amount'],
            payment_values['tran_date'],
            payment_values['tran_description'],
            payment_values['profile_key'],
            payment_values['nacha_type']
        )

    def _format_batch_xml(self,
                          mode: str,
                          batch_template: str,
                          batch_values: Dict[str, str],
                          payment_values: Dict[str, str],
                          transactions_xml: str) -> str:
        """Format batch XML and keep transaction wrapping consistent."""
        if mode == 'standard':
            return batch_template % (
                batch_values['batch_description'],
                batch_values['company_id'],
                batch_values['company_name'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group'],
                transactions_xml
            )

        if mode == 'esend':
            batch_info = batch_template % (
                payment_values['esend_app_name'],
                batch_values['batch_description'],
                payment_values['aba'],
                batch_values['company_id'],
                batch_values['company_name'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group']
            )
        elif mode == 'iat':
            batch_info = batch_template % (
                batch_values['batch_description'],
                batch_values['company_id'],
                batch_values['company_name'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group']
            )
        elif mode == 'caeft':
            batch_info = batch_template % (
                batch_values['batch_description'],
                batch_values['company_id'],
                batch_values['company_name'],
                payment_values['batch_credit_debit'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group'],
                payment_values['funding_account_number']
            )
        elif mode == 'caeft_esend':
            batch_info = batch_template % (
                payment_values['esend_app_name'],
                batch_values['batch_description'],
                batch_values['company_id'],
                batch_values['company_name'],
                payment_values['batch_credit_debit'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group'],
                payment_values['funding_account_number']
            )
        else:
            batch_info = batch_template % (
                payment_values['esend_app_name'],
                batch_values['batch_description'],
                batch_values['company_id'],
                batch_values['company_name'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group']
            )

        indented_batch_info = batch_info.replace('\n', '\n    ')
        indented_transactions = transactions_xml.replace('\n', '\n        ')

        return (
            '<Batch>\n'
            f'    {indented_batch_info}\n'
            '    <Transactions>\n'
            f'        {indented_transactions}\n'
            '    </Transactions>\n'
            '</Batch>'
        )

    def generate(self, payment_data: PaymentData) -> str:
        """
        Generate complete XML content

        Args:
            payment_data: PaymentData instance with form values

        Returns:
            Complete XML string ready to be written to file
        """
        mode, batch_file, payment_file = self._resolve_template_files(payment_data)
        batch_template, payment_template = self._load_templates_for_mode(mode, batch_file, payment_file)
        xml_parts = []

        # Add file header
        if self.file_header_template.count('%s') == 1:
            xml_parts.append(self.file_header_template % payment_data.creation_date)
        else:
            xml_parts.append(self.file_header_template)

        # Generate batches with their transactions
        for batch_index in range(payment_data.batches_quantity):
            batch_values = XMLFieldMapper.get_batch_values(payment_data, batch_index)

            # Generate payment transactions for this batch
            payment_transactions = []
            first_payment_values = None
            for trans_index in range(payment_data.transactions_count):
                payment_values = XMLFieldMapper.get_payment_values(
                    payment_data,
                    trans_index,
                    batch_index
                )
                if first_payment_values is None:
                    first_payment_values = payment_values

                # Format payment XML
                payment_xml = self._format_payment_xml(mode, payment_template, payment_values)
                payment_transactions.append(payment_xml)

            # Join all transactions with proper indentation
            transactions_xml = '\n        '.join(payment_transactions)

            # Format batch XML with transactions
            batch_xml = self._format_batch_xml(
                mode,
                batch_template,
                batch_values,
                first_payment_values or XMLFieldMapper.get_payment_values(payment_data),
                transactions_xml
            )
            xml_parts.append(batch_xml)

        # Add closing tag
        xml_parts.append('</File>')

        return '\n'.join(xml_parts)


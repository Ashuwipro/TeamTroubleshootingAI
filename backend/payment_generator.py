"""
Payment File Generator Module
Handles structured data extraction from UI form and mapping to XML templates
"""

from datetime import datetime
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

        return {
            'nacha_type': payment_data.payment_type,
            'account_number': XMLFieldMapper.generate_random_number(100000, 999999),
            'aba': aba,
            'payee_entity': f"PayeeEntity-{XMLFieldMapper.generate_random_number(1000, 9999)}",
            'payee_id': f"PayeeID-{XMLFieldMapper.generate_random_number(1000, 9999)}",
            'payee_name1': f"PayeeName1-{XMLFieldMapper.generate_random_number(1000, 9999)}",
            'tran_amount': XMLFieldMapper.generate_random_amount(),
            'tran_date': payment_data.creation_date,
            'tran_description': 'Payment'
        }

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
        self.file_header_template = None
        self.batch_template = None
        self.payment_template = None
        self._load_templates()

    def _load_templates(self):
        """Load XML template files"""
        import os

        try:
            with open(os.path.join(self.template_dir, 'ach_nacha_file_header.xml'), 'r') as f:
                self.file_header_template = f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError('ach_nacha_file_header.xml template not found')

        try:
            with open(os.path.join(self.template_dir, 'ach_nacha_batch.xml'), 'r') as f:
                self.batch_template = f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError('ach_nacha_batch.xml template not found')

        try:
            with open(os.path.join(self.template_dir, 'ach_nacha_payment.xml'), 'r') as f:
                self.payment_template = f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError('ach_nacha_payment.xml template not found')

    def generate(self, payment_data: PaymentData) -> str:
        """
        Generate complete XML content

        Args:
            payment_data: PaymentData instance with form values

        Returns:
            Complete XML string ready to be written to file
        """
        xml_parts = []

        # Add file header
        xml_parts.append(self.file_header_template)

        # Generate batches with their transactions
        for batch_index in range(payment_data.batches_quantity):
            batch_values = XMLFieldMapper.get_batch_values(payment_data, batch_index)

            # Generate payment transactions for this batch
            payment_transactions = []
            for trans_index in range(payment_data.transactions_count):
                payment_values = XMLFieldMapper.get_payment_values(
                    payment_data,
                    trans_index,
                    batch_index
                )

                # Format payment XML
                payment_xml = self.payment_template % (
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
                payment_transactions.append(payment_xml)

            # Join all transactions with proper indentation
            transactions_xml = '\n        '.join(payment_transactions)

            # Format batch XML with transactions
            batch_xml = self.batch_template % (
                batch_values['batch_description'],
                batch_values['company_id'],
                batch_values['company_name'],
                batch_values['effective_date'],
                batch_values['batch_status'],
                batch_values['batch_user_group'],
                transactions_xml
            )
            xml_parts.append(batch_xml)

        # Add closing tag
        xml_parts.append('</File>')

        return '\n'.join(xml_parts)


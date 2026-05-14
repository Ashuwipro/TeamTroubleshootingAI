#!/usr/bin/env python3
"""Regression tests for WebSeries BAB generation/preview header format."""
import json
import re
import sys
import unittest
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

app_spec = importlib.util.spec_from_file_location('team_troubleshooting_backend_app', BACKEND_DIR / 'app.py')
backend_app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(backend_app_module)
app = backend_app_module.app


class WebSeriesBabRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def _build_payload(
        payment_type='',
        beneficiary_count=1,
        third_line_count=1,
        currency='',
        account_type='',
        account_number='',
        bank_code_type='',
        bank_code='',
        notebook_entries=None
    ):
        migration_rows = [
            {'BENE_ADDRESS_1': '123 Main Street', 'BENE_ADDRESS_2': 'NULL'},
            {'BENE_ADDRESS_1': 'NULL', 'BENE_ADDRESS_2': 'Apartment 21'},
            {'BENE_ADDRESS_1': 'MG Road', 'BENE_ADDRESS_2': ' '},
            {'BENE_ADDRESS_1': 'Björkgatan', 'BENE_ADDRESS_2': 'Åpt 5'}
        ]
        payload = {
            'fileType': 'WebSeries BAB',
            'migrationAddressFields': json.dumps(migration_rows),
            'babBeneficiaryCount': str(beneficiary_count),
            'babThirdLineCount': str(third_line_count)
        }
        if payment_type:
            payload['paymentType'] = payment_type
        if currency:
            payload['babCurrency'] = currency
        if account_type:
            payload['babAccountType'] = account_type
        if account_number:
            payload['babAccountNumber'] = account_number
        if bank_code_type:
            payload['babBankCodeType'] = bank_code_type
        if bank_code:
            payload['babBankCode'] = bank_code
        if notebook_entries is not None:
            payload['babNotebookEntries'] = json.dumps(notebook_entries)
        return payload

    @staticmethod
    def _is_valid_bab_header(text):
        # H,YYYYMMDD,<5-10 alphanumeric chars>
        return bool(re.fullmatch(r'H,\d{8},[A-Za-z0-9]{5,10}', text.strip()))

    @staticmethod
    def _parse_bab_content(text):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 4:
            raise AssertionError(f'Expected at least 4 lines (H, B, A, T), got {len(lines)}: {lines}')
        header_line = lines[0]
        trailer_line = lines[-1]
        second_lines = [line.split(',') for line in lines[1:] if line.startswith('B,')]
        third_lines = [line.split(',') for line in lines[1:] if line.startswith('A,')]
        if len(second_lines) == 0:
            raise AssertionError(f'Expected at least one B line, got: {lines}')
        if len(third_lines) < 1:
            raise AssertionError(f'Expected at least one A line, got: {lines}')
        if not trailer_line.startswith('T,'):
            raise AssertionError(f'Expected last line to be T (trailer), got: {trailer_line}')
        return header_line, second_lines, third_lines[0]

    def test_preview_returns_valid_bab_header(self):
        response = self.client.post('/preview-file', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertIn('content', payload)
        header_line, second_lines, third_line = self._parse_bab_content(payload['content'])
        second_line = second_lines[0]
        self.assertTrue(self._is_valid_bab_header(header_line))
        self.assertEqual(second_line[0], 'B')
        self.assertEqual(second_line[1], '')
        self.assertEqual(second_line[2], 'Bene Contact 01')
        self.assertEqual(second_line[8], '')
        self.assertEqual(second_line[9], 'AK')
        # Third line validations
        self.assertEqual(third_line[0], 'A')
        self.assertRegex(third_line[3], r'^BeneName\d+$')
        self.assertEqual(third_line[11], 'USD')
        self.assertEqual(third_line[12], 'Other')
        self.assertEqual(third_line[13], '')
        self.assertEqual(third_line[14], '')
        self.assertEqual(third_line[15], '')

    def test_generate_returns_valid_bab_header_and_changes_between_calls(self):
        response_one = self.client.post('/generate-xml', json=self._build_payload())
        response_two = self.client.post('/generate-xml', json=self._build_payload())

        self.assertEqual(response_one.status_code, 200, response_one.get_data(as_text=True))
        self.assertEqual(response_two.status_code, 200, response_two.get_data(as_text=True))

        content_one = response_one.get_data(as_text=True).strip()
        content_two = response_two.get_data(as_text=True).strip()

        header_one, line_two_one, line_three_one = self._parse_bab_content(content_one)
        header_two, line_two_two, line_three_two = self._parse_bab_content(content_two)
        first_b_line_one = line_two_one[0]
        first_b_line_two = line_two_two[0]

        self.assertTrue(self._is_valid_bab_header(header_one))
        self.assertTrue(self._is_valid_bab_header(header_two))
        self.assertNotEqual(content_one, content_two)
        self.assertEqual(first_b_line_one[2], 'Bene Contact 01')
        self.assertEqual(first_b_line_two[2], 'Bene Contact 01')

        valid_address_pairs = {
            ('123 Main Street', ''),
            ('', 'Apartment 21'),
            ('MG Road', ' '),
            ('Björkgatan', 'Åpt 5')
        }
        self.assertIn((first_b_line_one[6], first_b_line_one[7]), valid_address_pairs)
        self.assertIn((first_b_line_two[6], first_b_line_two[7]), valid_address_pairs)
        self.assertEqual(first_b_line_one[8], '')
        self.assertEqual(first_b_line_two[8], '')
        # Third line: A record validations
        self.assertEqual(line_three_one[0], 'A')
        self.assertEqual(line_three_two[0], 'A')
        self.assertEqual(line_three_one[11], 'USD')
        self.assertEqual(line_three_two[11], 'USD')
        self.assertEqual(line_three_one[12], 'Other')
        self.assertEqual(line_three_two[12], 'Other')

    def test_generate_uses_beneficiary_count_for_number_of_b_lines(self):
        response = self.client.post('/generate-xml', json=self._build_payload(beneficiary_count=3))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, second_lines, third_line = self._parse_bab_content(response.get_data(as_text=True))

        self.assertEqual(len(second_lines), 3)
        self.assertEqual(
            [line[2] for line in second_lines],
            ['Bene Contact 01', 'Bene Contact 02', 'Bene Contact 03']
        )
        self.assertEqual(third_line[0], 'A')

    def test_generate_sets_bene_reference_for_nacha_or_bacs(self):
        response = self.client.post('/generate-xml', json=self._build_payload(payment_type='NACHA'))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, second_lines, third_line = self._parse_bab_content(response.get_data(as_text=True))
        self.assertEqual(second_lines[0][3], 'BeneReference')
        # Third line col index 4 is BeneReference for NACHA
        self.assertEqual(third_line[4], 'BeneReference')

    def test_generate_sets_custom_bab_third_line_account_details(self):
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Wire - International',
            currency='eur',
            account_type='IBAN',
            account_number='AB1234567890',
            bank_code_type='swift123',
            bank_code='BOFAUS3N12'
        ))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        self.assertEqual(third_line[1], 'INT')
        self.assertEqual(third_line[2], '')
        self.assertEqual(third_line[11], 'EUR')
        self.assertEqual(third_line[12], 'IBAN')
        self.assertEqual(third_line[13], 'AB1234567890')
        self.assertEqual(third_line[14], 'swift')
        self.assertEqual(third_line[15], 'BOFAUS3N12')

    def test_generate_maps_payment_type_fields_for_cash_concentration(self):
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Cash Concentration/Disbursement'
        ))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        self.assertEqual(third_line[1], 'CCD')
        self.assertEqual(third_line[2], 'NACHA')

    def test_generate_accepts_cash_concentration_account_type_values(self):
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Cash Concentration/Disbursement',
            account_type='Savings'
        ))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        # For Cash Concentration, Savings account type maps to 'SV'
        self.assertEqual(third_line[12], 'SV')

    def test_generate_cash_concentration_default_bank_code_values(self):
        """Test that Cash Concentration defaults to US-ACH bank code type and 021000018 bank code."""
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Cash Concentration/Disbursement',
            account_type='Savings',
            account_number='12345'
        ))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        # Verify position 14 is bank code type (US-ACH) and 15 is bank code (021000018)
        self.assertEqual(third_line[14], 'US-ACH')
        self.assertEqual(third_line[15], '021000018')
        # Verify account type mapping for Savings -> SV
        self.assertEqual(third_line[12], 'SV')
        # Verify account number is 12345
        self.assertEqual(third_line[13], '12345')

    def test_generate_cash_concentration_account_type_mappings(self):
        """Test all account type mappings for Cash Concentration/Disbursement."""
        test_cases = [
            ('Savings', 'SV'),
            ('Loans', 'CL'),
            ('Checking', 'DD'),
            ('Checkings', 'DD')
        ]
        
        for account_type, expected_abbr in test_cases:
            with self.subTest(account_type=account_type):
                response = self.client.post('/generate-xml', json=self._build_payload(
                    payment_type='Cash Concentration/Disbursement',
                    account_type=account_type,
                    account_number='12345'
                ))
                self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
                _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
                # Verify account type is mapped to abbreviation
                self.assertEqual(third_line[12], expected_abbr)

    def test_generate_maps_payment_type_fields_for_wire_domestic(self):
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Wire - Domestic'
        ))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        self.assertEqual(third_line[1], 'USWIRE')
        self.assertEqual(third_line[2], '')

    def test_generate_accepts_wire_domestic_account_type_values(self):
        for acct_type in ('ABA', 'DDA', 'Other', 'SWIFT'):
            with self.subTest(account_type=acct_type):
                response = self.client.post('/generate-xml', json=self._build_payload(
                    payment_type='Wire - Domestic',
                    account_type=acct_type
                ))
                self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
                _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
                self.assertEqual(third_line[12], acct_type)

    def test_generate_wire_domestic_default_bank_code_type_and_code(self):
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Wire - Domestic',
            bank_code_type='ABA',
            bank_code='021000018'
        ))
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        self.assertEqual(third_line[1], 'USWIRE')
        self.assertEqual(third_line[14], 'ABA')
        self.assertEqual(third_line[15], '021000018')

    def test_generate_wire_international_default_values(self):
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Wire - International',
            currency='GBP',
            account_type='IBAN',
            account_number='GB29NWBK60161331926819',
            bank_code_type='SWIFT',
            bank_code='AACSDE33XXX'
        ))
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        _, _, third_line = self._parse_bab_content(response.get_data(as_text=True))
        self.assertEqual(third_line[1], 'INT')
        self.assertEqual(third_line[2], '')
        self.assertEqual(third_line[11], 'GBP')
        self.assertEqual(third_line[12], 'IBAN')
        self.assertEqual(third_line[13], 'GB29NWBK60161331926819')
        self.assertEqual(third_line[14], 'SWIFT')
        self.assertEqual(third_line[15], 'AACSDE33XXX')

    def test_generate_includes_trailer_row_and_correct_filename(self):
        response = self.client.post('/generate-xml', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        lines = [line.strip() for line in response.get_data(as_text=True).splitlines() if line.strip()]
        # Last line must be the T trailer
        self.assertTrue(lines[-1].startswith('T,'), f'Expected trailer T line, got: {lines[-1]}')
        # Filename must match BAB_YYYYMMDD_HHMMSS.txt
        content_disposition = response.headers.get('Content-Disposition', '')
        self.assertRegex(content_disposition, r'BAB_\d{8}_\d{6}\.txt')

    def test_preview_includes_trailer_row(self):
        response = self.client.post('/preview-file', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        content = response.get_json()['content']
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertTrue(lines[-1].startswith('T,'), f'Expected trailer T line, got: {lines[-1]}')
        self.assertTrue(lines[0].startswith('H,'), f'Expected header H line, got: {lines[0]}')

    def test_generate_uses_third_line_count_for_number_of_a_lines(self):
        response = self.client.post('/generate-xml', json=self._build_payload(third_line_count=3))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        lines = [line.strip() for line in response.get_data(as_text=True).splitlines() if line.strip()]
        a_lines = [line for line in lines if line.startswith('A,')]
        self.assertEqual(len(a_lines), 3)

    def test_generate_normalizes_cash_notebook_a_line_account_type_and_trailing_commas(self):
        notebook_entries = [
            'B,,Bene Contact 01,,,,addr1,addr2,,AK,province,GB,post code,603-501-5470,888888,mg@bt.com,mg1@bt.com,mg2@bt.com',
            'A,CCD,NACHA,BeneName000003,,,,,,,,USD,Savings,12345,US-ACH,021000018,,'
        ]
        response = self.client.post('/generate-xml', json=self._build_payload(
            payment_type='Cash Concentration/Disbursement',
            notebook_entries=notebook_entries
        ))

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        lines = [line.strip() for line in response.get_data(as_text=True).splitlines() if line.strip()]
        a_line = next(line for line in lines if line.startswith('A,'))
        self.assertFalse(a_line.endswith(','), f'Cash A line must not end with trailing comma: {a_line}')
        a_fields = a_line.split(',')
        self.assertEqual(a_fields[12], 'SV')
        self.assertEqual(a_fields[15], '021000018')


if __name__ == '__main__':
    unittest.main()


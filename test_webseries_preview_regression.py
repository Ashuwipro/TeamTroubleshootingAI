#!/usr/bin/env python3
"""Regression tests for WebSeries Wire DOM XML preview/generate payload handling."""
import json
import sys
import unittest
import importlib.util
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

app_spec = importlib.util.spec_from_file_location('team_troubleshooting_backend_app', BACKEND_DIR / 'app.py')
backend_app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(backend_app_module)
app = backend_app_module.app
WEBSERIES_WIRE_MAX_BATCHES = backend_app_module.WEBSERIES_WIRE_MAX_BATCHES
WEBSERIES_WIRE_MAX_PREVIEW_BATCHES = backend_app_module.WEBSERIES_WIRE_MAX_PREVIEW_BATCHES


class WebSeriesPreviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def _build_payload(file_type='WebSeries Wire DOM XML', include_corr_bank_info=True):
        tag_values = {
            'wsTransactionsCount': ['1'],
            'wsAccountNumber': ['11223344'],
            'wsIncrement': ['0'],
            'wsOriginatorName': ['Originator Name 123'],
            'wsUserId': ['RISK1'],
            'wsBankNameCompany': ['BOA'],
            'wsAbas': ['021000018'],
            'wsClientCompany': ['RISKUG'],
            'wsPayeeBankAccountNumber': ['1234567890'],
            'wsPayeeBankID': ['021000018'],
            'wsPayeeBankName': ['WACHOVIA BANK,  NA'],
            'wsPayeeBankRoutingABA': ['011101024']
        }
        if include_corr_bank_info:
            tag_values.update({
                'wsAddressLine3': ['BOSTON'],
                'wsState': ['MA'],
                'wsBankID': ['011000015'],
                'wsBankNameCorr': ['FEDERAL RESERVE BANK OF BOSTON'],
                'wsBankRoutingABA': ['021000018']
            })
        payload = {
            'fileType': file_type,
            'migrationAddressFields': json.dumps([
                {
                    'BENE_ADDRESS_1': 'Bene Line 1',
                    'BENE_ADDRESS_2': 'Bene Line 2',
                    'ORIGINATOR_ADDRESS_1': 'Originator Line 1',
                    'ORIGINATOR_ADDRESS_2': 'Originator Line 2',
                    'ORIGINATOR_CITY': 'Boston'
                }
            ]),
            '__tagValues': tag_values
        }
        payload.update({key: ','.join(values) for key, values in tag_values.items()})
        return payload

    def test_preview_accepts_preserved_tag_values_with_commas(self):
        response = self.client.post('/preview-file', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertIn('WACHOVIA BANK,  NA', payload['content'])
        self.assertIn('<WebSeriesUserGroup>RISKUG</WebSeriesUserGroup>', payload['content'])
        self.assertIn('<WebSeriesUserID>RISK1</WebSeriesUserID>', payload['content'])
        self.assertIn('<OriginatorName>Originator Name 123</OriginatorName>', payload['content'])

    def test_generate_accepts_preserved_tag_values_with_commas(self):
        response = self.client.post('/generate-xml', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        xml_content = response.get_data(as_text=True)
        self.assertIn('WACHOVIA BANK,  NA', xml_content)
        self.assertIn('<AccountNumber>1234567890</AccountNumber>', xml_content)
        self.assertIn('<WebSeriesUserID>RISK1</WebSeriesUserID>', xml_content)
        self.assertIn('<OriginatorName>Originator Name 123</OriginatorName>', xml_content)

        root = ET.fromstring(xml_content)
        batches = root.findall('./Batch')
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0].findall('./Transactions/FedWire')), 1)

    def test_generate_treats_null_migration_values_as_blank_tags(self):
        payload = self._build_payload()
        payload['wsTransactionsCount'] = '2'
        payload['__tagValues']['wsTransactionsCount'] = ['2']
        payload['wsIncrement'] = '5'
        payload['__tagValues']['wsIncrement'] = ['5']
        payload['migrationAddressFields'] = json.dumps([
            {
                'BENE_ADDRESS_1': '123 Main St',
                'BENE_ADDRESS_2': 'Suite 12',
                'ORIGINATOR_ADDRESS_1': '45 Wall Street',
                'ORIGINATOR_ADDRESS_2': 'Apt 908',
                'ORIGINATOR_CITY': 'New York NY 10001'
            },
            {
                'BENE_ADDRESS_1': 'NULL',
                'BENE_ADDRESS_2': 'null',
                'ORIGINATOR_ADDRESS_1': 'NULL',
                'ORIGINATOR_ADDRESS_2': 'null',
                'ORIGINATOR_CITY': 'NULL'
            }
        ])

        response = self.client.post('/generate-xml', json=payload)

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        xml_content = response.get_data(as_text=True)
        self.assertNotIn('>NULL<', xml_content)
        self.assertNotIn('>null<', xml_content)

        root = ET.fromstring(xml_content)
        batches = root.findall('./Batch')
        self.assertEqual(len(batches), 2)
        self.assertEqual(
            [batch.findtext('./BatchInformation/CompanyBankInfo/BankAccount/AccountNumber') for batch in batches],
            ['11223344', '11223349']
        )

        second_rows = batches[1].findall('./Transactions/FedWire')
        self.assertEqual(len(second_rows), 1)
        second = second_rows[0]
        self.assertEqual(second.findtext('./PayeeInformation/PayeeAddress/AddressLine1') or '', '')
        self.assertEqual(second.findtext('./PayeeInformation/PayeeAddress/AddressLine2') or '', '')
        self.assertEqual(second.findtext('./OriginatorInformation/OriginatorAddress/OriginatorAddressLine1') or '', '')
        self.assertEqual(second.findtext('./OriginatorInformation/OriginatorAddress/OriginatorAddressLine2') or '', '')
        self.assertEqual(second.findtext('./OriginatorInformation/OriginatorAddress/OriginatorAddressLine3') or '', '')

    def test_generate_keeps_company_account_same_when_increment_is_zero(self):
        payload = self._build_payload()
        payload['wsTransactionsCount'] = '3'
        payload['__tagValues']['wsTransactionsCount'] = ['3']
        payload['wsIncrement'] = '0'
        payload['__tagValues']['wsIncrement'] = ['0']
        payload['migrationAddressFields'] = json.dumps([
            {
                'BENE_ADDRESS_1': 'Line 1',
                'BENE_ADDRESS_2': 'Line 2',
                'ORIGINATOR_ADDRESS_1': 'Originator 1',
                'ORIGINATOR_ADDRESS_2': 'Originator 2',
                'ORIGINATOR_CITY': 'City 1'
            },
            {
                'BENE_ADDRESS_1': 'Line 3',
                'BENE_ADDRESS_2': 'Line 4',
                'ORIGINATOR_ADDRESS_1': 'Originator 3',
                'ORIGINATOR_ADDRESS_2': 'Originator 4',
                'ORIGINATOR_CITY': 'City 2'
            },
            {
                'BENE_ADDRESS_1': 'Line 5',
                'BENE_ADDRESS_2': 'Line 6',
                'ORIGINATOR_ADDRESS_1': 'Originator 5',
                'ORIGINATOR_ADDRESS_2': 'Originator 6',
                'ORIGINATOR_CITY': 'City 3'
            }
        ])

        response = self.client.post('/generate-xml', json=payload)

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        root = ET.fromstring(response.get_data(as_text=True))
        batches = root.findall('./Batch')
        self.assertEqual(len(batches), 3)
        account_numbers = [batch.findtext('./BatchInformation/CompanyBankInfo/BankAccount/AccountNumber') for batch in batches]
        self.assertEqual(account_numbers, ['11223344', '11223344', '11223344'])
        self.assertTrue(all(len(batch.findall('./Transactions/FedWire')) == 1 for batch in batches))

    def test_generate_defaults_webseries_user_id_when_field_not_sent(self):
        payload = self._build_payload()
        payload.pop('wsUserId', None)
        payload['__tagValues'].pop('wsUserId', None)

        response = self.client.post('/generate-xml', json=payload)

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        root = ET.fromstring(response.get_data(as_text=True))
        batch = root.find('./Batch')
        self.assertIsNotNone(batch)
        self.assertEqual(batch.findtext('./BatchInformation/WebSeriesUserID'), 'RISK1')

    def test_intl_preview_and_generate_use_same_webseries_fields(self):
        payload = self._build_payload('WebSeries Wire INTL XML', include_corr_bank_info=False)
        payload['wsPayeeBankID'] = 'AACSDE33XXX'
        payload['__tagValues']['wsPayeeBankID'] = ['AACSDE33XXX']
        payload['wsPayeeBankName'] = 'SPARKASSE AACHEN'
        payload['__tagValues']['wsPayeeBankName'] = ['SPARKASSE AACHEN']
        payload['wsPayeeBankRoutingABA'] = '021000018'
        payload['__tagValues']['wsPayeeBankRoutingABA'] = ['021000018']

        preview_response = self.client.post('/preview-file', json=payload)
        self.assertEqual(preview_response.status_code, 200, preview_response.get_data(as_text=True))
        preview_payload = preview_response.get_json()
        self.assertIn('SPARKASSE AACHEN', preview_payload['content'])
        self.assertIn('<BankID>AACSDE33XXX</BankID>', preview_payload['content'])
        self.assertIn('<BankRouting>', preview_payload['content'])
        self.assertIn('<WebSeriesUserID>RISK1</WebSeriesUserID>', preview_payload['content'])
        self.assertIn('<TranDate>', preview_payload['content'])
        self.assertNotIn('<CorrBankInfo>', preview_payload['content'])

        generate_response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(generate_response.status_code, 200, generate_response.get_data(as_text=True))
        xml_content = generate_response.get_data(as_text=True)
        root = ET.fromstring(xml_content)
        batch = root.find('./Batch')
        self.assertIsNotNone(batch)
        self.assertEqual(batch.findtext('./BatchInformation/CompanyBankInfo/BankAccount/AccountNumber'), '11223344')
        self.assertEqual(batch.findtext('./BatchInformation/WebSeriesUserID'), 'RISK1')
        self.assertEqual(batch.findtext('./Transactions/INTL/OriginatorInformation/OriginatorName'), 'Originator Name 123')
        self.assertEqual(batch.findtext('./Transactions/INTL/PayeeBankInfo/BankAccountType'), 'IBAN')
        self.assertEqual(batch.findtext('./Transactions/INTL/PayeeBankInfo/BankID'), 'AACSDE33XXX')
        self.assertEqual(batch.findtext('./Transactions/INTL/PayeeBankInfo/BankIDType'), 'SWIFT')
        self.assertEqual(batch.findtext('./Transactions/INTL/PayeeBankInfo/BankName'), 'SPARKASSE AACHEN')
        self.assertEqual(batch.findtext('./Transactions/INTL/PayeeBankInfo/BankRouting/ABA'), '021000018')
        self.assertEqual(batch.findtext('./Transactions/INTL/PayeeInformation/PayeeAddress/AddressLine1'), 'Bene Line 1')
        self.assertEqual(batch.findtext('./Transactions/INTL/OriginatorInformation/OriginatorAddress/OriginatorAddressLine3'), 'Boston')
        self.assertEqual(batch.findtext('./Transactions/INTL/TranDate'), datetime.now().strftime('%Y-%m-%d'))
        self.assertIsNone(batch.find('./Transactions/INTL/CorrBankInfo'))


    def test_generate_round_robins_account_numbers_when_batches_exceed_range(self):
        # Range: 11223344, 11223354, 11223364 (step 10) -> 3 values
        # Batches: 5 -> indices 0,1,2,3,4 → range[0,1,2,0,1]
        payload = self._build_payload()
        payload['wsTransactionsCount'] = '5'
        payload['__tagValues']['wsTransactionsCount'] = ['5']
        payload['wsAccountNumber'] = '11223344'
        payload['__tagValues']['wsAccountNumber'] = ['11223344']
        payload['wsIncrement'] = '10'
        payload['__tagValues']['wsIncrement'] = ['10']
        payload['wsAccountNumberEnd'] = '11223364'
        payload['__tagValues']['wsAccountNumberEnd'] = ['11223364']
        payload['migrationAddressFields'] = json.dumps([
            {'BENE_ADDRESS_1': f'L{i}', 'BENE_ADDRESS_2': '', 'ORIGINATOR_ADDRESS_1': '',
             'ORIGINATOR_ADDRESS_2': '', 'ORIGINATOR_CITY': ''} for i in range(5)
        ])

        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        root = ET.fromstring(response.get_data(as_text=True))
        batches = root.findall('./Batch')
        self.assertEqual(len(batches), 5)
        account_numbers = [b.findtext('./BatchInformation/CompanyBankInfo/BankAccount/AccountNumber') for b in batches]
        # range has 3 values; 5 batches → round-robin
        self.assertEqual(account_numbers, ['11223344', '11223354', '11223364', '11223344', '11223354'])

    def test_generate_intl_round_robins_account_numbers_when_batches_exceed_range(self):
        # Range 11200, 11210, 11220 (3 values); 4 batches → [11200,11210,11220,11200]
        payload = self._build_payload('WebSeries Wire INTL XML', include_corr_bank_info=False)
        payload['wsTransactionsCount'] = '4'
        payload['__tagValues']['wsTransactionsCount'] = ['4']
        payload['wsAccountNumber'] = '11200'
        payload['__tagValues']['wsAccountNumber'] = ['11200']
        payload['wsIncrement'] = '10'
        payload['__tagValues']['wsIncrement'] = ['10']
        payload['wsAccountNumberEnd'] = '11220'
        payload['__tagValues']['wsAccountNumberEnd'] = ['11220']
        payload['migrationAddressFields'] = json.dumps([
            {'BENE_ADDRESS_1': f'B{i}', 'BENE_ADDRESS_2': '', 'ORIGINATOR_ADDRESS_1': '',
             'ORIGINATOR_ADDRESS_2': '', 'ORIGINATOR_CITY': ''} for i in range(4)
        ])

        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        root = ET.fromstring(response.get_data(as_text=True))
        batches = root.findall('./Batch')
        self.assertEqual(len(batches), 4)
        account_numbers = [b.findtext('./BatchInformation/CompanyBankInfo/BankAccount/AccountNumber') for b in batches]
        self.assertEqual(account_numbers, ['11200', '11210', '11220', '11200'])

    def test_generate_reuses_migration_rows_when_batches_exceed_rows(self):
        payload = self._build_payload()
        payload['wsTransactionsCount'] = '3'
        payload['__tagValues']['wsTransactionsCount'] = ['3']
        payload['migrationAddressFields'] = json.dumps([
            {
                'BENE_ADDRESS_1': 'One',
                'BENE_ADDRESS_2': 'Two',
                'ORIGINATOR_ADDRESS_1': 'Orig1',
                'ORIGINATOR_ADDRESS_2': 'Orig2',
                'ORIGINATOR_CITY': 'City1'
            }
        ])

        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        root = ET.fromstring(response.get_data(as_text=True))
        batches = root.findall('./Batch')
        self.assertEqual(len(batches), 3)
        for batch in batches:
            tx = batch.find('./Transactions/FedWire')
            self.assertEqual(tx.findtext('./PayeeInformation/PayeeAddress/AddressLine1'), 'One')
            self.assertEqual(tx.findtext('./PayeeInformation/PayeeAddress/AddressLine2'), 'Two')

    def test_generate_rejects_webseries_batch_count_above_max(self):
        payload = self._build_payload()
        over_limit = WEBSERIES_WIRE_MAX_BATCHES + 1
        payload['wsTransactionsCount'] = str(over_limit)
        payload['__tagValues']['wsTransactionsCount'] = [str(over_limit)]

        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f'Batches Count cannot exceed {WEBSERIES_WIRE_MAX_BATCHES}.',
            response.get_data(as_text=True)
        )

    def test_preview_rejects_webseries_batch_count_above_preview_max(self):
        payload = self._build_payload()
        over_preview_limit = WEBSERIES_WIRE_MAX_PREVIEW_BATCHES + 1
        payload['wsTransactionsCount'] = str(over_preview_limit)
        payload['__tagValues']['wsTransactionsCount'] = [str(over_preview_limit)]

        response = self.client.post('/preview-file', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f'Preview supports up to {WEBSERIES_WIRE_MAX_PREVIEW_BATCHES} batches for WebSeries Wire files.',
            response.get_data(as_text=True)
        )


if __name__ == '__main__':
    unittest.main()



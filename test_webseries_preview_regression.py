#!/usr/bin/env python3
"""Regression tests for WebSeries Wire XML preview/generate payload handling."""
import json
import sys
import unittest
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

app_spec = importlib.util.spec_from_file_location('team_troubleshooting_backend_app', BACKEND_DIR / 'app.py')
backend_app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(backend_app_module)
app = backend_app_module.app


class WebSeriesPreviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def _build_payload():
        tag_values = {
            'wsTransactionsCount': ['1'],
            'wsAccountNumber': ['11223344'],
            'wsIncrement': ['0'],
            'wsUserId': ['RISK1'],
            'wsBankNameCompany': ['BOA'],
            'wsAbas': ['021000018'],
            'wsClientCompany': ['RISKUG'],
            'wsAddressLine3': ['BOSTON'],
            'wsState': ['MA'],
            'wsBankID': ['011000015'],
            'wsBankNameCorr': ['FEDERAL RESERVE BANK OF BOSTON'],
            'wsBankRoutingABA': ['021000018'],
            'wsPayeeBankAccountNumber': ['1234567890'],
            'wsPayeeBankID': ['021000018'],
            'wsPayeeBankName': ['WACHOVIA BANK,  NA'],
            'wsPayeeBankRoutingABA': ['011101024']
        }
        payload = {
            'fileType': 'WebSeries Wire XML',
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

    def test_generate_accepts_preserved_tag_values_with_commas(self):
        response = self.client.post('/generate-xml', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        xml_content = response.get_data(as_text=True)
        self.assertIn('WACHOVIA BANK,  NA', xml_content)
        self.assertIn('<AccountNumber>1234567890</AccountNumber>', xml_content)
        self.assertIn('<WebSeriesUserID>RISK1</WebSeriesUserID>', xml_content)

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


if __name__ == '__main__':
    unittest.main()



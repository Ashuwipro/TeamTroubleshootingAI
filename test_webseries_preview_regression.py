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

    def test_generate_accepts_preserved_tag_values_with_commas(self):
        response = self.client.post('/generate-xml', json=self._build_payload())

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        xml_content = response.get_data(as_text=True)
        self.assertIn('WACHOVIA BANK,  NA', xml_content)
        self.assertIn('<AccountNumber>1234567890</AccountNumber>', xml_content)

    def test_generate_treats_null_migration_values_as_blank_tags(self):
        payload = self._build_payload()
        payload['wsTransactionsCount'] = '2'
        payload['__tagValues']['wsTransactionsCount'] = ['2']
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
        rows = root.findall('./Batch/Transactions/FedWire')
        self.assertEqual(len(rows), 2)

        second = rows[1]
        self.assertEqual(second.findtext('./PayeeInformation/PayeeAddress/AddressLine1') or '', '')
        self.assertEqual(second.findtext('./PayeeInformation/PayeeAddress/AddressLine2') or '', '')
        self.assertEqual(second.findtext('./OriginatorInformation/OriginatorAddress/OriginatorAddressLine1') or '', '')
        self.assertEqual(second.findtext('./OriginatorInformation/OriginatorAddress/OriginatorAddressLine2') or '', '')
        self.assertEqual(second.findtext('./OriginatorInformation/OriginatorAddress/OriginatorAddressLine3') or '', '')


if __name__ == '__main__':
    unittest.main()



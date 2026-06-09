#!/usr/bin/env python3
"""Regression tests for the extracted PCM ACH CAEFT XML frontend module and backend flows."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

app_spec = importlib.util.spec_from_file_location('team_troubleshooting_backend_app', BACKEND_DIR / 'app.py')
assert app_spec is not None and app_spec.loader is not None
backend_app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(backend_app_module)
app = backend_app_module.app


class AchCaeftXmlModularizationTests(unittest.TestCase):
    """Validate ACH CAEFT XML module asset serving and generation behavior."""

    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def build_payload():
        return {
            'fileType': 'ACH CAEFT XML',
            'batchesQuantity': '2',
            'transactionsCount': '1,1',
            'achCompIds': 'CAEFTC1,CAEFTC2',
            'achCompNames': 'CAEFT One,CAEFT Two',
            'clientCompany': 'RISKUG',
            'bankName': 'BOFA',
            'abas': '999999999',
            'options': 'ACH & ESend',
            'esendAppType': 'Name',
            'esendAppValue': 'CAEFTApp1,CAEFTApp2',
            'esendProfileKeys': 'CAEFTKey1',
            'payeeEmails': 'test@example.com',
            'fundingAccountNumber': '111111',
            'returnAccountNumber': '222222',
            'accountNumber': '333333',
            'batchCreditDebit': 'Credit',
            'transactionCreditDebit': 'Debit',
            '__tagValues': {
                'batchesQuantity': ['2'],
                'transactionsCount': ['1', '1'],
                'achCompIds': ['CAEFTC1', 'CAEFTC2'],
                'achCompNames': ['CAEFT One', 'CAEFT Two'],
                'clientCompany': ['RISKUG'],
                'bankName': ['BOFA'],
                'abas': ['999999999'],
                'esendAppValue': ['CAEFTApp1', 'CAEFTApp2'],
                'esendProfileKeys': ['CAEFTKey1'],
                'payeeEmails': ['test@example.com'],
                'fundingAccountNumber': ['111111'],
                'returnAccountNumber': ['222222'],
                'accountNumber': ['333333']
            }
        }

    def test_pcm_ach_caeft_module_assets_are_served(self):
        for filename, expected_marker in (
            ('ui.js', 'PcmAchCaeftXmlUI'),
            ('actions.js', 'PcmAchCaeftXmlActions'),
        ):
            response = self.client.get(f'/payment-screens/pcm/ach_caeft_xml/{filename}')
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
            self.assertIn(expected_marker, response.get_data(as_text=True))
            response.close()

    def test_ach_caeft_preview_returns_xml_content(self):
        response = self.client.post('/preview-file', json=self.build_payload())
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        data = response.get_json()
        self.assertIn('<File', data.get('content', ''))
        self.assertIn('<Batch', data.get('content', ''))

    def test_ach_caeft_generate_downloads_xml(self):
        response = self.client.post('/generate-xml', json=self.build_payload())
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.mimetype, 'application/xml')
        self.assertIn('.xml', response.headers.get('Content-Disposition', '').lower())
        generated_content = response.get_data(as_text=True)
        self.assertIn('<File', generated_content)


if __name__ == '__main__':
    unittest.main()


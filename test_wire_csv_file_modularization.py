#!/usr/bin/env python3
"""Regression tests for the extracted PCM wire CSV frontend module and backend flows."""
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


class WireCsvFileModularizationTests(unittest.TestCase):
    """Validate the extracted wire CSV module assets and generation behavior."""

    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def build_payload(wire_payment_type='both'):
        return {
            'fileType': '.CSV Wire Domestic',
            'futureBusinessDate': '20260522',
            'wirePaymentType': wire_payment_type,
            'wireFirstColSameForBoth': 'false',
            'wireSecondColSameForBoth': 'false',
            '__tagValues': {
                'wireDomesticTransactionsCount': ['2'],
                'wireInternationalTransactionsCount': ['1'],
                'originatorAccountNumber': ['11223344'],
                'beneAccountNumber': ['123456789012'],
                'beneBankId': ['053000196'],
                'intlOriginatorAccountNumber': ['99887766'],
                'intlBeneAccountNumber': ['GB29NWBK60161331926819'],
                'beneABA': ['021000021'],
                'clientCompany': ['RISKUG'],
                'bankName': ['BOFA']
            },
            'wireDomesticTransactionsCount': '2',
            'wireInternationalTransactionsCount': '1',
            'originatorAccountNumber': '11223344',
            'beneAccountNumber': '123456789012',
            'beneBankId': '053000196',
            'intlOriginatorAccountNumber': '99887766',
            'intlBeneAccountNumber': 'GB29NWBK60161331926819',
            'beneABA': '021000021',
            'clientCompany': 'RISKUG',
            'bankName': 'BOFA'
        }

    def test_pcm_wire_csv_module_assets_are_served(self):
        for filename, expected_marker in (
            ('ui.js', 'PcmWireCsvFileUI'),
            ('actions.js', 'PcmWireCsvFileActions'),
        ):
            response = self.client.get(f'/payment-screens/pcm/wire_csv_file/{filename}')
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
            self.assertIn(expected_marker, response.get_data(as_text=True))
            response.close()

    def test_wire_csv_preview_returns_token_and_combined_content(self):
        payload = self.build_payload('both')
        response = self.client.post('/preview-file', json=payload)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        data = response.get_json()
        self.assertTrue(data.get('previewToken'))
        self.assertIn('USWIRE', data.get('content', ''))
        self.assertIn('INT', data.get('content', ''))
        self.assertTrue(data['content'].endswith('T,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n'))

    def test_wire_csv_generate_uses_preview_token_and_downloads_csv(self):
        payload = self.build_payload('domestic')
        preview_response = self.client.post('/preview-file', json=payload)
        self.assertEqual(preview_response.status_code, 200, preview_response.get_data(as_text=True))
        preview_data = preview_response.get_json()

        payload['wireCsvPreviewToken'] = preview_data['previewToken']
        generate_response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(generate_response.status_code, 200, generate_response.get_data(as_text=True))
        self.assertEqual(generate_response.mimetype, 'text/csv')
        self.assertIn('.csv', generate_response.headers.get('Content-Disposition', '').lower())
        generated_content = generate_response.get_data(as_text=True)
        self.assertIn('USWIRE', generated_content)
        self.assertNotIn('\nINT,', generated_content)


if __name__ == '__main__':
    unittest.main()



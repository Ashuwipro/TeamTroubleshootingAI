#!/usr/bin/env python3
"""Integration test for WebSeries Wire DOM/INTL button functionality."""
import json
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


class WebSeriesWireButtonIntegrationTests(unittest.TestCase):
    """Test that Preview and Generate buttons work for WebSeries Wire forms."""

    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def build_minimal_payload(file_type='WebSeries Wire DOM XML'):
        """Build minimal but valid payload for WebSeries Wire forms."""
        migration_rows = [
            {'BENE_ADDRESS_1': 'Address 1', 'BENE_ADDRESS_2': 'Address 2'},
            {'BENE_ADDRESS_1': 'Address 3', 'BENE_ADDRESS_2': 'Address 4'},
        ]
        return {
            'fileType': file_type,
            'migrationAddressFields': json.dumps(migration_rows),
            '__tagValues': {
                'wsTransactionsCount': ['1'],
                'wsAccountNumber': ['11223344'],
                'wsIncrement': ['0'],
                'wsOriginatorName': ['Test Org'],
                'wsBankNameCompany': ['TEST BANK'],
                'wsAbas': ['021000018'],
                'wsClientCompany': ['CLIENT'],
                'wsUserId': ['USER1'],
                'wsPayeeBankAccountNumber': ['9876543210'],
                'wsPayeeBankID': ['123456789'],
                'wsPayeeBankName': ['PAYEE BANK'],
                'wsPayeeBankRoutingABA': ['011101024'],
                'wsAddressLine3': ['ADDR3'],
                'wsState': ['CA'],
                'wsBankID': ['011000015'],
                'wsBankNameCorr': ['CORR BANK'],
                'wsBankRoutingABA': ['021000018']
            }
        }

    def test_preview_button_webserieswire_dom_with_minimal_fields(self):
        """Test Preview button works for WebSeries Wire DOM with minimal form data."""
        payload = self.build_minimal_payload('WebSeries Wire DOM XML')
        # Preview endpoint should work
        response = self.client.post('/preview-file', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('content', data)
        self.assertGreater(len(data['content']), 0)
        # Should contain XML structure
        self.assertIn('<File>', data['content'])

    def test_generate_button_webserieswire_dom_with_minimal_fields(self):
        """Test Generate button works for WebSeries Wire DOM with minimal form data."""
        payload = self.build_minimal_payload('WebSeries Wire DOM XML')
        # Generate endpoint should work
        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertGreater(len(content), 0)
        # Should contain XML structure
        self.assertIn('<File>', content)

    def test_preview_button_webserieswire_intl_with_minimal_fields(self):
        """Test Preview button works for WebSeries Wire INTL with minimal form data."""
        payload = self.build_minimal_payload('WebSeries Wire INTL XML')
        response = self.client.post('/preview-file', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('content', data)
        self.assertGreater(len(data['content']), 0)
        self.assertIn('<File>', data['content'])

    def test_generate_button_webserieswire_intl_with_minimal_fields(self):
        """Test Generate button works for WebSeries Wire INTL with minimal form data."""
        payload = self.build_minimal_payload('WebSeries Wire INTL XML')
        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertGreater(len(content), 0)
        self.assertIn('<File>', content)

    def test_multiple_button_clicks_same_form_dom(self):
        """Test that clicking Preview/Generate multiple times works for Web Series Wire DOM."""
        payload = self.build_minimal_payload('WebSeries Wire DOM XML')

        # First click: Preview
        preview_response = self.client.post('/preview-file', json=payload)
        self.assertEqual(preview_response.status_code, 200)

        # Second click: Generate
        generate_response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(generate_response.status_code, 200)

        # Third click: Preview again
        preview_response2 = self.client.post('/preview-file', json=payload)
        self.assertEqual(preview_response2.status_code, 200)

    def test_multiple_button_clicks_same_form_intl(self):
        """Test that clicking Preview/Generate multiple times works for WebSeries Wire INTL."""
        payload = self.build_minimal_payload('WebSeries Wire INTL XML')

        # First click: Preview
        preview_response = self.client.post('/preview-file', json=payload)
        self.assertEqual(preview_response.status_code, 200)

        # Second click: Generate
        generate_response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(generate_response.status_code, 200)

        # Third click: Preview again
        preview_response2 = self.client.post('/preview-file', json=payload)
        self.assertEqual(preview_response2.status_code, 200)


if __name__ == '__main__':
    unittest.main()


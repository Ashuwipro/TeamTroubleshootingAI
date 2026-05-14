#!/usr/bin/env python3
"""Test WebSeries Wire payload from frontend form perspective."""
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


class WebSeriesWireFrontendTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_preview_webserieswire_dom_minimal_payload(self):
        """Test that minimal WebSeries Wire DOM payload works."""
        migration_rows = [
            {'BENE_ADDRESS_1': 'Addr 1', 'BENE_ADDRESS_2': 'Addr 2'},
            {'BENE_ADDRESS_1': 'Addr 3', 'BENE_ADDRESS_2': 'Addr 4'},
        ]
        payload = {
            'fileType': 'WebSeries Wire DOM XML',
            'migrationAddressFields': json.dumps(migration_rows),
            '__tagValues': {
                'wsTransactionsCount': ['1'],
                'wsAccountNumber': ['11223344'],
                'wsIncrement': ['0'],
                'wsOriginatorName': ['Test Originator'],
                'wsBankNameCompany': ['BOA'],
                'wsAbas': ['021000018'],
                'wsClientCompany': ['TESTCLIENT'],
                'wsUserId': ['TESTUSER'],
                'wsPayeeBankAccountNumber': ['9876543210'],
                'wsPayeeBankID': ['987654321'],
                'wsPayeeBankName': ['TEST BANK'],
                'wsPayeeBankRoutingABA': ['011101024'],
                'wsAddressLine3': ['TEST ADDRESS'],
                'wsState': ['CA'],
                'wsBankID': ['011000015'],
                'wsBankNameCorr': ['FEDERAL RESERVE'],
                'wsBankRoutingABA': ['021000018']
            }
        }

        response = self.client.post('/preview-file', json=payload)
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}")
        data = response.get_json()
        self.assertIn('content', data)
        self.assertGreater(len(data['content']), 0)
        print(f"Preview response preview: {data['content'][:200]}")

    def test_generate_webserieswire_dom_minimal_payload(self):
        """Test that minimal WebSeries Wire DOM payload works for generation."""
        migration_rows = [
            {'BENE_ADDRESS_1': 'Addr 1', 'BENE_ADDRESS_2': 'Addr 2'},
            {'BENE_ADDRESS_1': 'Addr 3', 'BENE_ADDRESS_2': 'Addr 4'},
        ]
        payload = {
            'fileType': 'WebSeries Wire DOM XML',
            'migrationAddressFields': json.dumps(migration_rows),
            '__tagValues': {
                'wsTransactionsCount': ['1'],
                'wsAccountNumber': ['11223344'],
                'wsIncrement': ['0'],
                'wsOriginatorName': ['Test Originator'],
                'wsBankNameCompany': ['BOA'],
                'wsAbas': ['021000018'],
                'wsClientCompany': ['TESTCLIENT'],
                'wsUserId': ['TESTUSER'],
                'wsPayeeBankAccountNumber': ['9876543210'],
                'wsPayeeBankID': ['987654321'],
                'wsPayeeBankName': ['TEST BANK'],
                'wsPayeeBankRoutingABA': ['011101024'],
                'wsAddressLine3': ['TEST ADDRESS'],
                'wsState': ['CA'],
                'wsBankID': ['011000015'],
                'wsBankNameCorr': ['FEDERAL RESERVE'],
                'wsBankRoutingABA': ['021000018']
            }
        }

        response = self.client.post('/generate-xml', json=payload)
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}")
        content = response.get_data(as_text=True)
        self.assertGreater(len(content), 0)
        # Should have XML envelope
        self.assertIn('<?xml', content)
        print(f"Generate response first 200 chars: {content[:200]}")


if __name__ == '__main__':
    unittest.main()



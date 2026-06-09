#!/usr/bin/env python3
"""Regression tests for extracted PCM CHECKS XML frontend module and backend flows."""
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


class ChecksXmlModularizationTests(unittest.TestCase):
    """Validate CHECKS XML module asset serving and generation behavior."""

    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def build_payload():
        return {
            'fileType': 'CHECKS XML',
            'batchesQuantity': '2',
            'transactionsCount': '1,2',
            'checkOrder': 'Ascending',
            'checkAppType': 'Name',
            'checkAppValue': 'CheckAppOne,CheckAppTwo',
            'checkProfiles': 'ProfileOne,ProfileTwo',
            'clientCompany': 'RISKUG',
            'bankName': 'BOFA',
            'fileName': 'AP',
            '__tagValues': {
                'batchesQuantity': ['2'],
                'transactionsCount': ['1', '2'],
                'checkAppValue': ['CheckAppOne', 'CheckAppTwo'],
                'checkProfiles': ['ProfileOne', 'ProfileTwo'],
                'clientCompany': ['RISKUG'],
                'bankName': ['BOFA']
            }
        }

    def test_pcm_checks_xml_module_assets_are_served(self):
        for filename, expected_marker in (
            ('ui.js', 'PcmChecksXmlUI'),
            ('actions.js', 'PcmChecksXmlActions'),
        ):
            response = self.client.get(f'/payment-screens/pcm/checks_xml/{filename}')
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
            self.assertIn(expected_marker, response.get_data(as_text=True))
            response.close()

    def test_checks_xml_preview_returns_xml_content(self):
        response = self.client.post('/preview-file', json=self.build_payload())
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        data = response.get_json()
        self.assertIn('<File', data.get('content', ''))
        self.assertIn('<Check', data.get('content', ''))

    def test_checks_xml_generate_downloads_xml(self):
        response = self.client.post('/generate-xml', json=self.build_payload())
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.mimetype, 'application/xml')
        self.assertIn('.xml', response.headers.get('Content-Disposition', '').lower())
        generated_content = response.get_data(as_text=True)
        self.assertIn('<File', generated_content)
        self.assertIn('<Check', generated_content)


if __name__ == '__main__':
    unittest.main()


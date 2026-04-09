#!/usr/bin/env python3
"""
Test script to verify SFTP directory listing functionality
"""

import requests
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
SFTP_ENDPOINT = "/api/sftp-directory"

def test_sftp_directory_listing():
    """Test the SFTP directory listing endpoint"""

    print("=" * 60)
    print("SFTP Directory Listing Test")
    print("=" * 60)

    # Test parameters
    test_cases = [
        {
            "name": "Root directory (Saas-N)",
            "params": {"saas": "saasN", "path": "/"}
        },
        {
            "name": "Saas-P Non Prod root",
            "params": {"saas": "saasPNonProd", "path": "/"}
        },
        {
            "name": "Saas-P Prod root",
            "params": {"saas": "saasPProd", "path": "/"}
        }
    ]

    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print("-" * 60)

        try:
            # Make request
            response = requests.get(
                f"{BASE_URL}{SFTP_ENDPOINT}",
                params=test_case['params'],
                timeout=15
            )

            print(f"Status Code: {response.status_code}")

            if response.ok:
                data = response.json()
                print(f"Current Path: {data.get('path')}")
                print(f"Parent Path: {data.get('parentPath')}")
                print(f"Entries Count: {len(data.get('entries', []))}")

                # Show first few entries
                entries = data.get('entries', [])[:5]
                if entries:
                    print("\nFirst entries:")
                    for entry in entries:
                        print(f"  - {entry['name']} ({entry['entryType']})")
            else:
                error_data = response.json()
                print(f"Error: {error_data.get('error')}")

        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to Flask server at localhost:5000")
            print("Make sure Flask app is running: python app.py")
        except Exception as e:
            print(f"ERROR: {str(e)}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_sftp_directory_listing()


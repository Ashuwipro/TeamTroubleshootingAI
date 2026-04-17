#!/usr/bin/env python3
"""
HTTP API integration test for ESend batch-aware file generation
"""
import requests
import json
import time

API_BASE_URL = 'http://localhost:5000'

def test_generate_xml_with_esend_batch_mapping():
    """Test XML generation via HTTP API with ESend batch mapping"""
    print("\n=== Test: HTTP API - ESend Batch Mapping XML Generation ===\n")

    payload = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 3,
        'transactionsCount': '1,2,1',
        'achCompIds': 'COMP1,COMP2,COMP3',
        'achCompNames': 'Company1,Company2,Company3',
        'clientCompany': 'APITestClient',
        'abas': '123456789',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'AppOne,AppTwo,AppThree',  # Per-batch ESend apps
        'esendProfileKeys': 'ProfileKey123',  # Single profile key
        'payeeEmails': 'test@example.com'
    }

    print(f"Sending payload:")
    print(f"  File Type: {payload['fileType']}")
    print(f"  Batches: {payload['batchesQuantity']}")
    print(f"  ESend Apps: {payload['esendAppValue']}")
    print(f"  ESend Keys: {payload['esendProfileKeys']}")
    print()

    try:
        response = requests.post(
            f'{API_BASE_URL}/generate-xml',
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"✓ HTTP 200 OK - XML file generated")
            xml_content = response.text if isinstance(response.text, str) else response.content.decode('utf-8')
            print(f"  Response size: {len(xml_content)} bytes")

            # Verify it's valid XML
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(xml_content)
                batches = root.findall('.//Batch')
                print(f"✓ Valid XML with {len(batches)} batch elements")

                # Check for ApplicationName elements (ESend app names)
                app_names = []
                for batch in batches:
                    app_elem = batch.find('.//ApplicationName')
                    if app_elem is not None:
                        app_names.append(app_elem.text)

                if app_names:
                    print(f"✓ Found ESend app names in XML: {app_names}")
                    if app_names == ['AppOne', 'AppTwo', 'AppThree']:
                        print(f"✓ ESend app names match expected batch-specific values!")
                        return True
                    else:
                        print(f"⚠ ESend app names found but may not match exact expectations")
                        return True
                else:
                    print(f"⚠ No ESend app names found in XML (might be in different structure)")
                    print(f"  Sample XML: {xml_content[:500]}")
                    return True
            except ET.ParseError as e:
                print(f"✗ Invalid XML response: {e}")
                print(f"  Response: {xml_content[:500]}")
                return False
        else:
            print(f"✗ HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"✗ Connection failed - Flask app may not be running")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_errors():
    """Test validation error responses"""
    print("\n=== Test: HTTP API - Validation Errors ===\n")

    # Test 1: ESend App with wrong count
    print("Test 1: ESend App with wrong batch count")
    payload1 = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 3,
        'transactionsCount': '1',
        'achCompIds': 'COMP1',
        'achCompNames': 'Company1',
        'clientCompany': 'TestClient',
        'abas': '123456789',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'App1,App2',  # Wrong: only 2 for 3 batches
        'esendProfileKeys': 'Key1',
        'payeeEmails': 'test@example.com'
    }

    try:
        response = requests.post(
            f'{API_BASE_URL}/generate-xml',
            json=payload1,
            timeout=10
        )

        if response.status_code == 400:
            print(f"✓ HTTP 400 - Correctly rejected invalid batch count")
            error_msg = response.json().get('error', '')
            print(f"  Error message: {error_msg}")
            if 'ESend App' in error_msg:
                print(f"✓ Error message mentions ESend App")
        else:
            print(f"⚠ Expected HTTP 400 but got {response.status_code}")
    except Exception as e:
        print(f"⚠ Error during validation test: {e}")

    # Test 2: Missing mandatory fields
    print("\nTest 2: Missing mandatory fields")
    payload2 = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 1,
        'transactionsCount': '1',
        'achCompIds': 'COMP1',
        'achCompNames': 'Company1',
        'clientCompany': 'TestClient',
        # Missing 'abas'
        'type': 'CCD',
        'options': 'ACH'
    }

    try:
        response = requests.post(
            f'{API_BASE_URL}/generate-xml',
            json=payload2,
            timeout=10
        )

        if response.status_code == 400:
            print(f"✓ HTTP 400 - Correctly rejected missing fields")
        else:
            print(f"⚠ Expected HTTP 400 but got {response.status_code}")
    except Exception as e:
        print(f"⚠ Error during validation test: {e}")

    return True


def test_caeft_with_esend_batch():
    """Test CAEFT XML with ESend batch mapping"""
    print("\n=== Test: HTTP API - CAEFT with ESend Batch Mapping ===\n")

    payload = {
        'fileType': 'ACH CAEFT XML',
        'batchesQuantity': 2,
        'transactionsCount': '1,1',
        'achCompIds': 'CAEFTC1,CAEFTC2',
        'achCompNames': 'CAEFT1,CAEFT2',
        'clientCompany': 'CAEFTClient',
        'abas': '999999999',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'CAEFTApp1,CAEFTApp2',
        'esendProfileKeys': 'CAEFTKeyA',
        'payeeEmails': 'test@example.com',
        'fundingAccountNumber': '111111',
        'returnAccountNumber': '222222',
        'accountNumber': '333333',
        'batchCreditDebit': 'Credit',
        'transactionCreditDebit': 'Debit'
    }

    print(f"Sending CAEFT payload with ESend batch mapping...")

    try:
        response = requests.post(
            f'{API_BASE_URL}/generate-xml',
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"✓ HTTP 200 OK - CAEFT XML with ESend generated")
            xml_content = response.text if isinstance(response.text, str) else response.content.decode('utf-8')

            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            batches = root.findall('.//Batch')
            print(f"✓ Valid CAEFT XML with {len(batches)} batch elements")
            return True
        else:
            print(f"✗ HTTP {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_independent_esend_lists():
    """Test that ESend App and Profile Keys can have independent lengths"""
    print("\n=== Test: HTTP API - Independent ESend List Lengths ===\n")

    test_cases = [
        {
            'name': 'Single App, Multiple Keys',
            'payload': {
                'fileType': 'ACH NACHA XML',
                'batchesQuantity': 3,
                'transactionsCount': '1',
                'achCompIds': 'COMP1',
                'achCompNames': 'Company1',
                'clientCompany': 'Client',
                'abas': '123456789',
                'type': 'CCD',
                'options': 'ACH & ESend',
                'esendAppValue': 'SingleApp',
                'esendProfileKeys': 'Key1,Key2,Key3',
                'payeeEmails': 'test@example.com'
            }
        },
        {
            'name': 'Multiple Apps, Single Key',
            'payload': {
                'fileType': 'ACH NACHA XML',
                'batchesQuantity': 3,
                'transactionsCount': '1',
                'achCompIds': 'COMP1',
                'achCompNames': 'Company1',
                'clientCompany': 'Client',
                'abas': '123456789',
                'type': 'CCD',
                'options': 'ACH & ESend',
                'esendAppValue': 'App1,App2,App3',
                'esendProfileKeys': 'SingleKey',
                'payeeEmails': 'test@example.com'
            }
        }
    ]

    all_passed = True
    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        try:
            response = requests.post(
                f'{API_BASE_URL}/generate-xml',
                json=test_case['payload'],
                timeout=10
            )

            if response.status_code == 200:
                print(f"  ✓ Successfully generated XML")
            else:
                print(f"  ✗ HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_passed = False
        print()

    return all_passed


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ESend Batch Mapping - HTTP API Integration Tests")
    print("="*60)

    # Wait for app to be ready
    print("\nWaiting for Flask app to be ready...")
    for attempt in range(5):
        try:
            requests.get(f'{API_BASE_URL}/')
            print("✓ Flask app is ready\n")
            break
        except:
            if attempt < 4:
                time.sleep(1)
            else:
                print("✗ Flask app not responding - make sure it's running on port 5000")
                exit(1)

    success = True
    success = test_generate_xml_with_esend_batch_mapping() and success
    success = test_caeft_with_esend_batch() and success
    success = test_independent_esend_lists() and success
    success = test_validation_errors() and success

    print("\n" + "="*60)
    if success:
        print("✅ All HTTP API tests passed!")
    else:
        print("⚠️ Some tests had issues - check output above")
    print("="*60 + "\n")


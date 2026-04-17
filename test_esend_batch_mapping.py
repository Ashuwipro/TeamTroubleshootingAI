#!/usr/bin/env python3
"""
Test script to verify ESend batch-aware field mapping
"""
import sys
import json
sys.path.insert(0, r'C:\Users\Ashutosh.Pal\PycharmProjects\TeamTroubleshootingAI\backend')

from payment_generator import PaymentData, XMLFieldMapper

def test_esend_independent_batch_mapping():
    """Test that ESend App and ESend Profile Keys can have independent list lengths"""
    print("\n=== Test: ESend Independent Batch Mapping ===\n")

    # Test Case 1: Single ESend App, Multiple Profile Keys
    print("Test Case 1: Single ESend App, Multiple Profile Keys")
    form_data_1 = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 3,
        'transactionsCount': '1',
        'achCompIds': 'COMP1',
        'achCompNames': 'Company1',
        'clientCompany': 'MyCompany',
        'abas': '123456789',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'AppName1',  # Single value
        'esendProfileKeys': 'Key1,Key2,Key3',  # Multiple values
        'payeeEmails': 'test@example.com'
    }

    try:
        payment_data_1 = PaymentData.from_form_data(form_data_1)
        print(f"  ✓ Parsed successfully")
        print(f"    ESend App values: {payment_data_1.esend_app_values}")
        print(f"    ESend Profile Key values: {payment_data_1.esend_profile_key_values}")

        # Verify batch resolution
        for batch_idx in range(3):
            app = payment_data_1.get_esend_app_for_batch(batch_idx)
            key = payment_data_1.get_esend_profile_key_for_batch(batch_idx)
            print(f"    Batch {batch_idx}: App='{app}', Key='{key}'")
            assert app == 'AppName1', f"Batch {batch_idx} app should be 'AppName1'"
            expected_key = f"Key{batch_idx + 1}"
            assert key == expected_key, f"Batch {batch_idx} key should be '{expected_key}'"
        print("  ✓ All batch resolutions correct\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

    # Test Case 2: Multiple ESend Apps, Single Profile Key
    print("Test Case 2: Multiple ESend Apps, Single Profile Key")
    form_data_2 = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 3,
        'transactionsCount': '1',
        'achCompIds': 'COMP1',
        'achCompNames': 'Company1',
        'clientCompany': 'MyCompany',
        'abas': '123456789',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'App1,App2,App3',  # Multiple values
        'esendProfileKeys': 'ProfileKey1',  # Single value
        'payeeEmails': 'test@example.com'
    }

    try:
        payment_data_2 = PaymentData.from_form_data(form_data_2)
        print(f"  ✓ Parsed successfully")
        print(f"    ESend App values: {payment_data_2.esend_app_values}")
        print(f"    ESend Profile Key values: {payment_data_2.esend_profile_key_values}")

        # Verify batch resolution
        for batch_idx in range(3):
            app = payment_data_2.get_esend_app_for_batch(batch_idx)
            key = payment_data_2.get_esend_profile_key_for_batch(batch_idx)
            print(f"    Batch {batch_idx}: App='{app}', Key='{key}'")
            expected_app = f"App{batch_idx + 1}"
            assert app == expected_app, f"Batch {batch_idx} app should be '{expected_app}'"
            assert key == 'ProfileKey1', f"Batch {batch_idx} key should be 'ProfileKey1'"
        print("  ✓ All batch resolutions correct\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

    # Test Case 3: Mismatched lengths should fail
    print("Test Case 3: Mismatched ESend App length (should fail)")
    form_data_3 = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 3,
        'transactionsCount': '1',
        'achCompIds': 'COMP1',
        'achCompNames': 'Company1',
        'clientCompany': 'MyCompany',
        'abas': '123456789',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'App1,App2',  # Wrong length (2 instead of 1 or 3)
        'esendProfileKeys': 'Key1,Key2,Key3',
        'payeeEmails': 'test@example.com'
    }

    try:
        payment_data_3 = PaymentData.from_form_data(form_data_3)
        print(f"  ✗ Should have raised ValueError but didn't\n")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejected: {e}\n")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}\n")
        return False

    # Test Case 4: Both single values
    print("Test Case 4: Both ESend fields with single values")
    form_data_4 = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 3,
        'transactionsCount': '1',
        'achCompIds': 'COMP1',
        'achCompNames': 'Company1',
        'clientCompany': 'MyCompany',
        'abas': '123456789',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'AppName',
        'esendProfileKeys': 'ProfileKey',
        'payeeEmails': 'test@example.com'
    }

    try:
        payment_data_4 = PaymentData.from_form_data(form_data_4)
        print(f"  ✓ Parsed successfully")
        print(f"    ESend App values: {payment_data_4.esend_app_values}")
        print(f"    ESend Profile Key values: {payment_data_4.esend_profile_key_values}")

        # Verify batch resolution
        for batch_idx in range(3):
            app = payment_data_4.get_esend_app_for_batch(batch_idx)
            key = payment_data_4.get_esend_profile_key_for_batch(batch_idx)
            print(f"    Batch {batch_idx}: App='{app}', Key='{key}'")
            assert app == 'AppName', f"Batch {batch_idx} app should be 'AppName'"
            assert key == 'ProfileKey', f"Batch {batch_idx} key should be 'ProfileKey'"
        print("  ✓ All batch resolutions correct\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

    print("=== All Tests Passed ===\n")
    return True


def test_xml_generation_with_esend():
    """Test XML generation with ESend batch mapping"""
    print("\n=== Test: XML Generation with ESend Batch Mapping ===\n")

    form_data = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 2,
        'transactionsCount': '2,3',
        'achCompIds': 'COMP1,COMP2',
        'achCompNames': 'Company1,Company2',
        'clientCompany': 'MyCompany',
        'abas': '123456789,987654321',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'AppA,AppB',  # Per-batch ESend apps
        'esendProfileKeys': 'KeyX',  # Single profile key for all
        'payeeEmails': 'test1@example.com,test2@example.com,test3@example.com'
    }

    try:
        payment_data = PaymentData.from_form_data(form_data)
        print(f"✓ Payment data parsed successfully")

        # Verify the structure
        print(f"  Batches: {payment_data.batches_quantity}")
        print(f"  Transactions per batch: {payment_data.transactions_count}")
        print(f"  ESend Apps: {payment_data.esend_app_values}")
        print(f"  ESend Keys: {payment_data.esend_profile_key_values}")

        # Check batch resolution
        for batch_idx in range(payment_data.batches_quantity):
            app = payment_data.get_esend_app_for_batch(batch_idx)
            key = payment_data.get_esend_profile_key_for_batch(batch_idx)
            print(f"  Batch {batch_idx}: App='{app}', Key='{key}'")

        print("✓ ESend batch mapping working correctly\n")
        return True
    except Exception as e:
        print(f"✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = True
    success = test_esend_independent_batch_mapping() and success
    success = test_xml_generation_with_esend() and success

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


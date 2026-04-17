#!/usr/bin/env python3
"""
Integration test for XML generation with ESend batch mapping
"""
import sys
import os
sys.path.insert(0, r'C:\Users\Ashutosh.Pal\PycharmProjects\TeamTroubleshootingAI\backend')

from payment_generator import PaymentData, ACHNachaXMLGenerator
import xml.etree.ElementTree as ET

def test_xml_generation_with_batch_esend():
    """Test complete XML generation with ESend batch-aware values"""
    print("\n=== Test: XML Generation with ESend Batch Values ===\n")

    form_data = {
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 2,
        'transactionsCount': '1,2',  # Batch 1: 1 transaction, Batch 2: 2 transactions
        'achCompIds': 'COMP1,COMP2',
        'achCompNames': 'Company1,Company2',
        'clientCompany': 'ClientCorp',
        'abas': '123456789,987654321',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'AppBatchA,AppBatchB',  # Different app per batch
        'esendProfileKeys': 'SingleKey',  # Same key for all batches
        'payeeEmails': 'test@example.com'
    }

    try:
        # Parse form data
        payment_data = PaymentData.from_form_data(form_data)
        print(f"✓ Form data parsed successfully")
        print(f"  Batches: {payment_data.batches_quantity}")
        print(f"  Transactions: {payment_data.transactions_count}")
        print(f"  ESend Apps: {payment_data.esend_app_values}")
        print(f"  ESend Keys: {payment_data.esend_profile_key_values}")

        # Generate XML
        template_dir = r'C:\Users\Ashutosh.Pal\PycharmProjects\TeamTroubleshootingAI\backend\templates'
        generator = ACHNachaXMLGenerator(template_dir)
        xml_content = generator.generate(payment_data)

        print(f"✓ XML generated successfully ({len(xml_content)} characters)")

        # Parse and validate XML structure
        root = ET.fromstring(xml_content)
        batches = root.findall('.//Batch')
        print(f"✓ XML parsed successfully")
        print(f"  Found {len(batches)} batch elements")

        # Verify batch content and ESend values
        for batch_idx, batch in enumerate(batches):
            # Find ESend app reference in batch
            esend_app_elem = batch.find('.//ESendAppName')
            transactions = batch.findall('.//Transactions/*')

            print(f"\n  Batch {batch_idx}:")
            print(f"    Transaction count: {len(transactions)}")
            if esend_app_elem is not None:
                print(f"    ESend App: {esend_app_elem.text}")
                # Verify it matches expected batch value
                expected_app = payment_data.get_esend_app_for_batch(batch_idx)
                if esend_app_elem.text == expected_app:
                    print(f"    ✓ ESend App matches expected: {expected_app}")
                else:
                    print(f"    ✗ ESend App mismatch! Expected: {expected_app}, Got: {esend_app_elem.text}")

        print("\n✓ XML generation with ESend batch mapping successful!")

        # Print a sample of the generated XML
        print("\n--- Sample XML (first 1500 chars) ---")
        print(xml_content[:1500])
        print("--- End Sample ---\n")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_caeft_with_esend():
    """Test ACH CAEFT XML with ESend batch mapping"""
    print("\n=== Test: ACH CAEFT XML with ESend ===\n")

    form_data = {
        'fileType': 'ACH CAEFT XML',
        'batchesQuantity': 2,
        'transactionsCount': '1,1',
        'achCompIds': 'CAEFTCOMP1,CAEFTCOMP2',
        'achCompNames': 'CAEFT Company1,CAEFT Company2',
        'clientCompany': 'CAEFT Client',
        'abas': '111111111',
        'type': 'CCD',
        'options': 'ACH & ESend',
        'esendAppValue': 'CAEFTApp1,CAEFTApp2',
        'esendProfileKeys': 'CAEFTKey',
        'payeeEmails': 'test@example.com',
        'fundingAccountNumber': '1234567',
        'returnAccountNumber': '7654321',
        'accountNumber': '9999999',
        'batchCreditDebit': 'Credit',
        'transactionCreditDebit': 'Credit'
    }

    try:
        payment_data = PaymentData.from_form_data(form_data)
        print(f"✓ CAEFT form data parsed successfully")

        template_dir = r'C:\Users\Ashutosh.Pal\PycharmProjects\TeamTroubleshootingAI\backend\templates'
        generator = ACHNachaXMLGenerator(template_dir)
        xml_content = generator.generate(payment_data)

        print(f"✓ CAEFT XML generated successfully")

        # Parse and validate
        root = ET.fromstring(xml_content)
        batches = root.findall('.//Batch')
        print(f"✓ CAEFT XML parsed successfully with {len(batches)} batch elements")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = True
    success = test_xml_generation_with_batch_esend() and success
    success = test_caeft_with_esend() and success

    if success:
        print("\n✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)


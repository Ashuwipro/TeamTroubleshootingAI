# ACH NACHA Payment File Generation - Field Mapping Documentation

## Overview
This document describes how form field values from the UI are structured, mapped, and transformed into XML template placeholders for ACH NACHA payment file generation.

## Data Flow Architecture

```
UI Form Fields
    ↓
PaymentData Object (Structured)
    ↓
XMLFieldMapper (Mapping Logic)
    ↓
ACHNachaXMLGenerator (XML Generation)
    ↓
XML Output File
```

## PaymentData Class

The `PaymentData` class serves as a structured container for all form input values.

### Basic Information
- **file_type**: `str` - Type of file being generated (e.g., 'ACH NACHA XML')

### Batch Information
- **batches_quantity**: `int` - Number of batches to generate
- **transactions_count**: `int` - Number of transactions per batch
- **comp_ids**: `str` - Company IDs (from "ACH Comp IDs" field)
- **comp_names**: `str` - Company Names (from "ACH Comp Names" field)
- **client_company**: `str` - Client Company name

### Bank Information
- **abas**: `List[str]` - List of ABA numbers (comma-separated from "ABAs" field)
- **bank_name**: `str` - Bank name

### Payment Type Information
- **payment_type**: `str` - Payment type (CCD, CTX, PPD, IAT)
- **options**: `str` - Payment options (ACH, ACH & ESend, ESend_Only)

### Payee Information (Optional - BAB)
- **payee_ids**: `str` - Payee IDs
- **payee_lookup_type**: `str` - Lookup type (No Flag, DB, FILE, NONE)
- **payee_lookup_elements**: `List[str]` - Selected lookup elements

### ESend Information (Optional)
- **esend_app_type**: `str` - ESend app type (Name or ID)
- **esend_app_value**: `str` - ESend app value
- **esend_profile_keys**: `str` - ESend profile keys
- **payee_emails**: `str` - Payee emails

### Metadata
- **creation_date**: `str` - Date in YYYY-MM-DD format (automatically set to current date)

## Field Mapping to XML Templates

### ACH NACHA Batch XML Mapping

The batch template has these placeholders (6 total):

```xml
<BatchInformation>
    <BatchDescription>%s</BatchDescription>      <!-- Position 0 -->
    <CompanyID>%s</CompanyID>                    <!-- Position 1 -->
    <CompanyName>%s</CompanyName>                <!-- Position 2 -->
    <EffectiveDate>%s</EffectiveDate>            <!-- Position 3 -->
    <BatchStatus>%s</BatchStatus>                <!-- Position 4 -->
    <BatchUserGroup>%s</BatchUserGroup>          <!-- Position 5 -->
    <CreditDebit>Credit</CreditDebit>
</BatchInformation>
```

**Mapping Logic (in XMLFieldMapper.get_batch_values()):**

| Placeholder Position | XML Field | Source | Value |
|---|---|---|---|
| 0 | BatchDescription | Generated | "Batch " + random 4-char string (e.g., "Batch A1K9") |
| 1 | CompanyID | Form | `payment_data.comp_ids` |
| 2 | CompanyName | Form | `payment_data.comp_names` |
| 3 | EffectiveDate | Metadata | `payment_data.creation_date` (YYYY-MM-DD) |
| 4 | BatchStatus | Fixed | "AP" |
| 5 | BatchUserGroup | Form | `payment_data.client_company` |

### ACH NACHA Payment XML Mapping

The payment template has these placeholders (10 total):

```xml
<Nacha%s>                                          <!-- Position 0 -->
    <DiscretionaryData>CR</DiscretionaryData>
    <NachaTranType>22</NachaTranType>
    <PayeeBankInfo>
        <BankAccount>
            <AccountNumber>%s</AccountNumber>     <!-- Position 1 -->
        </BankAccount>
        <BankRouting>
            <ABA>%s</ABA>                         <!-- Position 2 -->
        </BankRouting>
    </PayeeBankInfo>
    <PayeeInformation>
        <PayeeEntity>%s</PayeeEntity>             <!-- Position 3 -->
        <PayeeID>%s</PayeeID>                     <!-- Position 4 -->
        <PayeeName1>%s</PayeeName1>               <!-- Position 5 -->
    </PayeeInformation>
    <TranAmount>%s</TranAmount>                   <!-- Position 6 -->
    <TranCurrency>USD</TranCurrency>
    <TranDate>%s</TranDate>                       <!-- Position 7 -->
    <TranDescription>PAC - %s Addenda Information</TranDescription> <!-- Position 8 -->
</Nacha%s>                                         <!-- Position 9 -->
```

**Mapping Logic (in XMLFieldMapper.get_payment_values()):**

| Placeholder Position | XML Field | Source | Value |
|---|---|---|---|
| 0 | Nacha%s (opening tag) | Form | `payment_data.payment_type` (e.g., "CCD") |
| 1 | AccountNumber | Generated | Random 6-digit number (100000-999999) |
| 2 | ABA | Form | From `payment_data.abas` list (cycles through if multiple ABAs) |
| 3 | PayeeEntity | Generated | "PayeeEntity-" + random 4-digit number (1000-9999) |
| 4 | PayeeID | Generated | "PayeeID-" + random 4-digit number (1000-9999) |
| 5 | PayeeName1 | Generated | "PayeeName1-" + random 4-digit number (1000-9999) |
| 6 | TranAmount | Generated | Random amount formatted as "XXXX.XX" (e.g., "1234.56") |
| 7 | TranDate | Metadata | `payment_data.creation_date` (YYYY-MM-DD) |
| 8 | TranDescription | Generated | "Payment" or custom value |
| 9 | Nacha%s (closing tag) | Form | `payment_data.payment_type` (same as position 0) |

## Example Data Flow

### Example Input from UI Form

```json
{
    "fileType": "ACH NACHA XML",
    "batchesQuantity": "2",
    "transactionsCount": "3",
    "achCompIds": "COMP001",
    "achCompNames": "Acme Corp",
    "abas": "123456789,987654321",
    "clientCompany": "Finance Team",
    "type": "CCD",
    "options": "ACH",
    "bankName": "Bank of America",
    "payeeIds": "",
    "payeeLookupType": "No Flag",
    "payeeLookupElements": "",
    "esendAppType": "Name",
    "esendAppValue": "",
    "esendProfileKeys": "",
    "payeeEmails": ""
}
```

### PaymentData Object Created

```python
PaymentData(
    file_type='ACH NACHA XML',
    batches_quantity=2,
    transactions_count=3,
    comp_ids='COMP001',
    comp_names='Acme Corp',
    client_company='Finance Team',
    abas=['123456789', '987654321'],  # Note: parsed as list
    bank_name='Bank of America',
    payment_type='CCD',
    options='ACH',
    payee_ids='',
    payee_lookup_type='No Flag',
    payee_lookup_elements=[],
    esend_app_type='Name',
    esend_app_value='',
    esend_profile_keys='',
    payee_emails='',
    creation_date='2026-03-30'
)
```

### Generated XML Content

The XML will have the structure:
```
File Header
├── Batch 1 (with BatchDescription="Batch A7K2", CompanyID="COMP001", etc.)
│   ├── Payment 1 (with ABA="123456789", AccountNumber="456789", etc.)
│   ├── Payment 2 (with ABA="987654321", AccountNumber="234567", etc.)
│   └── Payment 3 (with ABA="123456789", AccountNumber="678901", etc.)
├── Batch 2 (with BatchDescription="Batch K9L3", CompanyID="COMP001", etc.)
│   ├── Payment 1 (with ABA="987654321", AccountNumber="345678", etc.)
│   ├── Payment 2 (with ABA="123456789", AccountNumber="567890", etc.)
│   └── Payment 3 (with ABA="987654321", AccountNumber="123456", etc.)
└── </File>
```

## Key Features

### 1. **Multi-value Support**
- **ABAs Field**: Comma-separated values are parsed into a list and cycled through for each transaction
- **Payee Lookup Elements**: Comma-separated values are parsed and stored as a list

### 2. **Automatic Generation**
- Account Numbers: Random 6-digit numbers per transaction
- Payee Entity/ID/Name: Generated with random suffixes for uniqueness
- Transaction Amounts: Random values formatted with 2 decimal places
- Batch Descriptions: Random 4-character suffixes for variety
- Effective Date: Automatically set to current date

### 3. **Date Handling**
- All dates are in YYYY-MM-DD format
- Automatically uses current date (no manual date entry required)

### 4. **Batch-Transaction Relationship**
- Each batch can have multiple transactions
- Example: 2 batches × 3 transactions = 6 total payment records + 1 batch header = 7 XML blocks

## Implementation in Classes

### PaymentData.from_form_data(form_data)
Converts raw form dictionary into structured PaymentData object with proper type conversions.

### XMLFieldMapper.get_batch_values(payment_data, batch_index)
Returns dictionary of mapped values for batch XML template.

### XMLFieldMapper.get_payment_values(payment_data, transaction_index, batch_index)
Returns dictionary of mapped values for payment XML template. Handles ABA cycling for multiple transactions.

### ACHNachaXMLGenerator.generate(payment_data)
Orchestrates the complete XML generation process:
1. Adds file header
2. Loops through batches
3. For each batch, loops through transactions
4. Applies mappings and generates XML
5. Adds closing tag

## Extension Points

To add new fields in the future:
1. Add property to `PaymentData` class
2. Update `PaymentData.from_form_data()` to parse the field
3. Add field to appropriate XML template if needed
4. Update mapping method in `XMLFieldMapper` if needed
5. Update form in HTML UI


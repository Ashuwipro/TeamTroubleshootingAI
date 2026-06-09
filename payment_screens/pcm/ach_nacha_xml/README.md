# ACH NACHA XML Frontend Module

PCM-specific frontend module for the `ACH NACHA XML` payment screen under `payment_screens/pcm/ach_nacha_xml`.

- `ui.js`: Builds and wires the `ACH NACHA XML` form UI with fields for batch configuration, payment type, ACH company information, bank information, payee information, ESend configuration, and CAEFT details.
- `actions.js`: Handles ACH NACHA XML preview/generate API requests.

These files are served by backend route `/payment-screens/pcm/ach_nacha_xml/<filename>` and loaded by `backend/static/index.html`.

## Form Fields

The ACH NACHA XML form is organized into three columns:

### Left Column: Batch & Transaction Configuration
- Batches Quantity: Number of batches to generate
- Transactions Count: Number of transactions per batch
- Payment Type: CCD, CTX, PPD, or IAT
- Options: ACH, ACH & ESend, or ESend Only

### Middle Column: ACH Company & Bank Information
- ACH Comp IDs: Company identifiers
- ACH Comp Names: Company names
- Client Company: Client company name
- ABAs: ABA numbers (9 digits)
- Bank Name: Financial institution name

### Right Column: Payee & ESend Information
- Payee IDs: Payee identifiers (optional)
- Payee Lookup Type: None, DB, FILE, or NONE
- Payee Lookup Elements: Additional lookup elements
- Payee Emails: Email addresses for ESend
- ESend App Type: Name or ID
- ESend App Value: Application identifier/name
- ESend Profile Keys: Profile identifiers
- Funding Account Number: CAEFT funding account
- Return Account Number: CAEFT return account
- Account Number: Transaction account
- Batch Credit/Debit: Credit or Debit
- Transaction Credit/Debit: Credit or Debit

## Backend Integration

The frontend modules communicate with the following Flask endpoints:
- `/preview-file` (POST): Preview generated ACH NACHA XML content
- `/generate-xml` (POST): Generate and download ACH NACHA XML file

The backend uses the `ACHNachaXMLGenerator` class from `backend/payment_generator.py` to handle XML generation based on form data.



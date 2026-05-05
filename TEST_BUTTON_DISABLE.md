# Test: Disable Preview and Generate Buttons Until Table Has Records

## Objective
Verify that the Preview and Generate buttons are disabled until at least one record is present in the Check Recon table.

## Implementation Details

### New Function: `hasCheckReconTableRecords()`
- Checks if the `.checkReconPreviewTable` element exists
- Gets the tbody element
- Counts the number of rows (tr elements)
- Returns `true` if rows.length > 0, `false` otherwise

### Modified Function: `updateGenerateButtonState()`
- Added logic to check if current form type is "Check Recon File"
- If Check Recon File:
  - Calls `hasCheckReconTableRecords()` to check for table records
  - Disables buttons if no table records AND form is not complete
- Updated tooltip messages:
  - Shows "Add at least one record to the table" when Check Recon has no records
  - Shows "Fill all mandatory fields" for other validation failures

## Test Scenarios

### Scenario 1: Check Recon File - No Data Entered
1. Select "Check Recon File" from file type dropdown
2. Leave all input fields empty
3. **Expected Result**: 
   - Table should be empty (no tbody rows)
   - Preview button should be **DISABLED** (grayed out)
   - Generate button should be **DISABLED** (grayed out)
   - Tooltip should show: "Add at least one record to the table"

### Scenario 2: Check Recon File - One Field Enters Data
1. Select "Check Recon File" from file type dropdown
2. Enter Account Number: "123456789"
3. Leave other fields empty
4. **Expected Result**:
   - Table should show 1 row with the account number
   - `getCheckReconPreviewRow()` returns non-null (has at least one value)
   - Preview button should be **ENABLED** (if all mandatory fields are filled)
   - Generate button should be **ENABLED** (if all mandatory fields are filled)

### Scenario 3: Check Recon File - All Fields Filled
1. Select "Check Recon File" from file type dropdown
2. Fill in all required fields:
   - Account Number: "123456789"
   - Check Number: "001"
   - Amount: "1000.00"
   - Payment Date: Select a date
   - Payee Name: "John Doe"
   - Client Company: "ACME Corp"
   - Bank Name: "Wells Fargo"
3. **Expected Result**:
   - Table should show 1 row with all data
   - Both buttons should be **ENABLED**

### Scenario 4: Check Recon File - Clear a Field
1. Start with Scenario 3 (all fields filled, buttons enabled)
2. Clear the Account Number field
3. **Expected Result**:
   - Table should still show the row (at least one field still has data)
   - Buttons should remain **ENABLED**

### Scenario 5: Check Recon File - Clear All Fields
1. Start with Scenario 3 (all fields filled, buttons enabled)
2. Clear all input fields
3. **Expected Result**:
   - Table should be empty (no rows in tbody)
   - Buttons should be **DISABLED**

### Scenario 6: Other File Types (e.g., ACH NACHA XML)
1. Select "ACH NACHA XML"
2. **Expected Result**:
   - Buttons behavior should be unchanged from before
   - `hasCheckReconTableRecords()` is bypassed (hasTableData defaults to true)
   - Only mandatory field validation applies

## How to Test

1. Open the application in a web browser
2. Navigate to the "Generate" modal
3. Follow each test scenario above
4. Verify button states match expected results
5. Check tooltip messages by hovering over disabled buttons

## Code Changes Summary

- Added `hasCheckReconTableRecords()` function to check for table records
- Modified `updateGenerateButtonState()` to include table record validation
- Updated tooltip messages for better UX
- Integrated check into form validation flow


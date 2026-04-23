# ACH FILE Form - Complete Documentation

## Overview
The `.ACH File` form has been fully implemented with a three-column layout in the Generate File modal. This form allows users to generate ACH formatted payment files with support for multiple payment configurations.

## Form Structure

### Three-Column Layout

#### **LEFT COLUMN - Mandatory Fields**
These fields are always required and visible:

1. **Immediate Destination** (Mandatory)
   - Type: Single-value tag input
   - Default Value: `22` (displayed as block)
   - Purpose: Immediate destination code for ACH file header
   - Behavior: Block style with × removal button

2. **Immediate Origin** (Mandatory)
   - Type: Single-value tag input
   - Default Value: `112412` (displayed as block)
   - Purpose: Immediate origin code for ACH file header
   - Behavior: Block style with × removal button

3. **Immediate Destination Name** (Mandatory)
   - Type: Single-value tag input
   - Default Value: `BONY` (displayed as block)
   - Purpose: Name associated with immediate destination
   - Behavior: Block style with × removal button

4. **ACH Comp IDs** (Mandatory)
   - Type: Multi-value tag input
   - Accepts: Comma-separated values
   - Behavior: Each value converts to block on comma press or blur
   - Duplicate Values: Allowed
   - Validation: Must match count of ACH Comp Names (either 1 or batch quantity)

5. **ACH Comp Names** (Mandatory)
   - Type: Multi-value tag input
   - Accepts: Comma-separated values
   - Behavior: Each value converts to block on comma press or blur
   - Duplicate Values: Allowed
   - Validation: Must match count of ACH Comp IDs (either 1 or batch quantity)

---

#### **MIDDLE COLUMN - File & Batch Configuration**
These fields configure the basic file and batch structure:

1. **File Name** (Optional)
   - Type: Text input
   - Placeholder: "Enter file name..."
   - Purpose: Custom name for generated file
   - Behavior: Regular text input

2. **Client Company** (Optional)
   - Type: Text input
   - Placeholder: "Enter client company..."
   - Purpose: Company identifier/usergroup
   - Behavior: Regular text input

3. **Bank Name** (Optional)
   - Type: Text input
   - Placeholder: "Enter bank name..."
   - Purpose: Bank identifier
   - Behavior: Regular text input

4. **Batches Quantity** (Mandatory - Red *)
   - Type: Single-value tag input (numeric only)
   - Placeholder: "Enter batches quantity..."
   - Accepts: Only numeric values > 0
   - Behavior: Block style with × removal
   - Validation: Must be a single positive integer

5. **Transactions Count** (Mandatory - Red *)
   - Type: Multi-value tag input (numeric only)
   - Placeholder: "Enter transactions count..."
   - Accepts: Comma-separated numeric values > 0
   - Behavior: Each value converts to block
   - Validation: 
     - Single value: applies to all batches
     - Multiple values: sum must equal batch quantity
     - All values must be > 0

---

#### **RIGHT COLUMN - Payment Options & Details**

**Message:** "Only applicable with ACH options (optional)."

1. **Options Dropdown** (Mandatory)
   - Type: Select dropdown
   - Options:
     - `ACH` - Standard ACH processing (default)
     - `ACH & ESend` - ACH with ESend integration
     - `ESend_Only` - ESend-only processing
   - Behavior: Controls visibility of other fields
   - onChange Event: `toggleACHFileOptionsVisibility()`

##### **When Options = "ACH"**

**ABAs Field** (Visible)
- Type: Multi-value tag input
- Accepts: Comma-separated ABA routing numbers
- Behavior: Each ABA (9 digits) converts to block on comma or blur
- Validation: Each ABA must be exactly 9 numeric digits
- Duplicate Values: Allowed

##### **When Options = "ACH & ESend" or "ESend_Only"**

**ESend Details Section** (Visible - Contains 3 fields)

1. **ESend App** (Mandatory - Red *)
   - Type: Type selector + Multi-value tag input
   - Type Selector: Dropdown with "Name" or "ID" options (default: "Name")
   - Accepts: Comma-separated values
   - Behavior: Each value converts to block
   - Name Field: `achEsendApp`
   - Type Field: `achEsendAppType`

2. **ESend Profile Keys** (Mandatory - Red *)
   - Type: Multi-value tag input
   - Accepts: Comma-separated profile key values
   - Behavior: Each key converts to block
   - Validation: Can have different length from ESend App (flexible)

3. **Payee Emails** (Mandatory - Red *)
   - Type: Multi-value tag input
   - Accepts: Comma-separated email addresses
   - Behavior: Each email converts to block
   - Validation: Email format validation when submitted

---

## Validation Rules

### Mandatory Fields (Must be filled before generating)
- Immediate Destination
- Immediate Origin
- Immediate Destination Name
- ACH Comp IDs
- ACH Comp Names
- Batches Quantity
- Transactions Count
- Options (default: ACH)
- ABAs (when Options = ACH)
- ESend App, Profile Keys, Payee Emails (when Options = ACH & ESend or ESend_Only)

### Field-Specific Validations

#### ACH Comp IDs & Names
- Count must match: either 1 or batch quantity
- If 1 value: applies to all batches
- If multiple values: must be exactly equal to batch quantity
- Both fields must have same count

#### ABAs (ACH Option)
- Format: Exactly 9 numeric digits
- Can contain duplicates
- Multiple values separated by commas

#### Transactions Count
- Single value: applies to all batches
- Multiple values: sum must equal batch quantity
- All values must be > 0

#### Payee Emails (ESend Option)
- Must be valid email format (contains @)
- Can be multiple comma-separated values

---

## Form State Management

### Default Values (Auto-populated)
When `.ACH File` form is loaded:
- Immediate Destination: `22`
- Immediate Origin: `112412`
- Immediate Destination Name: `BONY`
- Options: `ACH` (default selection)

### Form Restoration
- Form state is saved when switching between payment types
- When returning to `.ACH File`, previous values are restored
- Pre-seed data overrides default values

### Multi-Value Field Behavior
- Values display as blocks/badges
- × button removes individual blocks
- Comma-separated input converts to blocks on comma press
- Clicking outside field (blur) also converts pending input to block
- Horizontal scrolling when values exceed column width

---

## Integration with Pre-Seed Data

### YAML Configuration Support
The `.ACH File` form supports pre-seed data from `file_templates_config.yaml`:

```yaml
environments:
  PR1:
    PCM312P:
      ACH FILE:
        SAMPLE_FILE_NAME:
          attributes:
            achCompIds: ['123456789', '987654321']
            achCompNames: ['COMPANY A', 'COMPANY B']
```

### Pre-Seed Data Population
When pre-seed data is selected:
1. File name dropdown filters to ACH FILE type files
2. Selecting a file auto-populates:
   - ACH Comp IDs
   - ACH Comp Names
   - Batches Quantity (default: 1)
   - Transactions Count (default: 1)
3. Default values (Immediate Destination, Origin, Name) remain
4. ESend and ABA fields remain empty unless specified in pre-seed data

### Pre-Seed Data Display
- Pre-seed populated values display fully visible (no left scroll)
- Values align left in their field
- Complete data is visible without horizontal scrolling

---

## JavaScript Functions

### Toggle Options Visibility
```javascript
window.toggleACHFileOptionsVisibility = function()
```
- Called when Options dropdown value changes
- Shows/hides ABAs field and ESend section
- Updates field visibility based on selected option

### Event Handlers
- `onchange="toggleACHFileOptionsVisibility()"` - Options dropdown
- Multi-value tag inputs support comma separator and blur events
- Pre-seed file dropdown triggers data population

---

## Form Submission & Validation

### Generate Button State
- Enabled only when all mandatory fields are filled
- Hover text: "Fill all mandatory fields" (when disabled)

### Error Messages
When Generate is clicked with validation errors:
- Popup displays all validation issues in bullet points
- Issues listed clearly for user correction
- Must fix all issues before generating

### Supported Error Scenarios
1. ACH Comp IDs and Names count mismatch
2. ABA format error (not 9 digits)
3. Email validation error in Payee Emails
4. Transactions Count sum mismatch with batch quantity
5. Missing mandatory fields

---

## File Generation

### Output Format
- File extension: `.ACH` (NACHA format)
- Generated file contains:
  - File header with Immediate Destination/Origin/Name
  - One or more Batches (as per Batches Quantity)
  - Each batch containing configured transactions
  - Proper NACHA record formatting

### Generation Data Flow
1. User fills all required fields
2. Clicks "Generate" button
3. Filename popup appears (editable)
4. User confirms filename
5. Backend generates `.ACH` file using:
   - Immediate Destination/Origin/Name as file header
   - ACH Comp IDs/Names for batch company information
   - ABAs or ESend details based on Options selection
   - Transactions Count for record generation
6. File downloads to user's Downloads folder

---

## Technical Implementation

### HTML Structure
- Form created dynamically in JavaScript
- Three-column layout with CSS flexbox
- All fields use `createTagInput()` helper function
- ESend section toggled via CSS display property

### Field Names (Form Data Keys)
- `immediateDestination`
- `immediateOrigin`
- `immediateDestinationName`
- `achCompIds`
- `achCompNames`
- `achFileName`
- `achClientCompany`
- `achBankName`
- `achBatchesQuantity`
- `achTransactionsCount`
- `achOptions`
- `achOptionsAbAs`
- `achEsendAppType`
- `achEsendApp`
- `achEsendProfileKeys`
- `achPayeeEmails`

### CSS Classes
- `.formColumn` - Column container
- `.formGroup` - Field group container
- `.formLabel` - Field label
- `.formInput` - Input field styling
- `.tagInputContainer` - Tag input container
- `tagStyleSelectTrigger` - Dropdown trigger styling
- `.selectOptions` - Multi-select dropdown options

---

## Testing Checklist

- [ ] Form renders with correct 3-column layout
- [ ] Default values populate (22, 112412, BONY)
- [ ] Options dropdown changes show/hide correct sections
- [ ] ACH option shows ABAs field
- [ ] ESend options show ESend section
- [ ] Multi-value fields accept comma-separated input
- [ ] Validation prevents generation with errors
- [ ] Pre-seed data populates correctly
- [ ] Form state persists when switching between payment types
- [ ] Generate button creates .ACH file
- [ ] File download works correctly

---

## Known Limitations

1. **Mix File Support**: When `.ACH File` is selected, Mix File checkbox is hidden (design requirement)
2. **Pre-Seed Data Dependency**: ESend values only populate if specified in YAML
3. **File Format**: Only generates NACHA format (.ACH files)

---

## Future Enhancements

1. Add help tooltips for each field
2. Support for custom NACHA record types
3. File preview before generation
4. Batch processing for multiple file generations
5. Additional ACH file format variations (CTX, PPD, IAT)

---

## Code References

### File Locations
- **Frontend Form**: `backend/static/index.html` (lines 3422-3666)
- **Toggle Function**: `backend/static/index.html` (end of script section)
- **Validation Logic**: `backend/static/index.html` (validation functions)
- **Form State Management**: `backend/static/index.html` (form save/restore functions)

### Related Files
- `file_templates_config.yaml` - Pre-seed data configuration
- `payment_generator.py` - Backend file generation logic
- `app.py` - Flask API endpoints

---

## Version History

**v1.0 (Current)**
- Initial implementation of `.ACH File` form
- Three-column layout with all required fields
- Support for ACH and ESend options
- Pre-seed data integration
- Full validation framework
- Default values implementation

---

## User Guide Quick Reference

### To Generate an ACH File:
1. Select ".ACH File" from Payment Form dropdown
2. Enter/confirm Immediate Destination (default: 22)
3. Enter/confirm Immediate Origin (default: 112412)
4. Enter/confirm Immediate Destination Name (default: BONY)
5. Add ACH Company IDs and Names
6. Set Batches Quantity
7. Set Transactions Count for each batch
8. Select ACH Options (ACH, ACH & ESend, or ESend_Only)
9. Fill corresponding ABA or ESend details
10. Click Generate
11. Edit filename if needed
12. File downloads

### To Use Pre-Seed Data:
1. Check "Use Pre-Seed Data" checkbox
2. Select Environment
3. Select Usergroup
4. Select File from dropdown
5. Form auto-populates with pre-seed values
6. Modify as needed
7. Click Generate



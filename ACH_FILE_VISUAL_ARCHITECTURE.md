# .ACH File Form - Visual Architecture & Data Flow

## Form Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    GENERATE FILE MODAL                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  Payment Form Dropdown: [▼ .ACH File .................]                                      │
│                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                   3-COLUMN FORM LAYOUT                                       │
│                                                                                              │
│  ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐     │
│  │    LEFT COLUMN            │   MIDDLE COLUMN           │    RIGHT COLUMN           │     │
│  │   (Mandatory Fields)       │  (File Configuration)     │   (Payment Options)       │     │
│  ├───────────────────────────┼───────────────────────────┼───────────────────────────┤     │
│  │                           │                           │                           │     │
│  │ ★ Immediate Dest.         │ • File Name               │ Options Dropdown          │     │
│  │   [22] ✕                  │   [________________...]   │ [ACH ▼]                   │     │
│  │                           │                           │ ┌───────────────────────┐ │     │
│  │ ★ Immediate Origin        │ • Client Company          │ │ ACH                   │ │     │
│  │   [112412] ✕              │   [________________...]   │ │ ACH & ESend           │ │     │
│  │                           │                           │ │ ESend_Only            │ │     │
│  │ ★ Imm. Dest. Name         │ • Bank Name               │ └───────────────────────┘ │     │
│  │   [BONY] ✕                │   [________________...]   │                           │     │
│  │                           │                           │ ★ ABAs                    │     │
│  │ ★ ACH Comp IDs            │ ★ Batches Quantity        │   [________________...]   │     │
│  │   [COMP_ID] ✕ [COMP_ID]   │   [1] ✕                   │   [011000015] ✕           │     │
│  │   [scroll ≫]              │                           │   [021000021] ✕           │     │
│  │                           │ ★ Transactions Count      │   [scroll ≫]             │     │
│  │ ★ ACH Comp Names          │   [1] ✕                   │                           │     │
│  │   [Company A] ✕           │   [2] ✕                   │ ESend Details Section     │     │
│  │   [Company B] ✕           │                           │ (Hidden when Options=ACH) │     │
│  │   [scroll ≫]              │                           │                           │     │
│  │                           │                           │ ★ ESend App               │     │
│  │                           │                           │ Type: [Name ▼]            │     │
│  │                           │                           │ [APP_1] ✕ [APP_2] ✕      │     │
│  │                           │                           │ [scroll ≫]                │     │
│  │                           │                           │                           │     │
│  │                           │                           │ ★ ESend Profile Keys      │     │
│  │                           │                           │ [PROFILE_1] ✕ [PROFILE_2]│     │
│  │                           │                           │ [scroll ≫]                │     │
│  │                           │                           │                           │     │
│  │                           │                           │ ★ Payee Emails            │     │
│  │                           │                           │ [user@test.com] ✕         │     │
│  │                           │                           │ [scroll ≫]                │     │
│  │                           │                           │                           │     │
│  └───────────────────────────┴───────────────────────────┴───────────────────────────┘     │
│                                                                                              │
│  [Upload File]  [Generate]                                                                 │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

Legend:
★ = Mandatory field (red asterisk)
✕ = Remove block button
[scroll ≫] = Horizontal scroll indicator
[...] = Text input placeholder
[▼] = Dropdown indicator
```

---

## Data Flow Diagram

### User Input → Form State → File Generation

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION FLOW                                    │
└──────────────────────────────────────────────────────────────────────────────────┘

User fills .ACH File form
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│  Form State Object (Saved Automatically)                │
├─────────────────────────────────────────────────────────┤
│ formState['ACH FILE'] = {                               │
│   immediateDestination: "22",                           │
│   immediateOrigin: "112412",                            │
│   immediateDestinationName: "BONY",                     │
│   achCompIds: ["123456789", "987654321"],              │
│   achCompNames: ["COMPANY A", "COMPANY B"],            │
│   achFileName: "payment_file",                          │
│   achClientCompany: "USERGROUP_NAME",                  │
│   achBankName: "BANK_NAME",                            │
│   achBatchesQuantity: "2",                             │
│   achTransactionsCount: ["5", "3"],                    │
│   achOptions: "ACH & ESend",                           │
│   achEsendAppType: "Name",                             │
│   achEsendApp: ["APP_NAME_1", "APP_NAME_2"],          │
│   achEsendProfileKeys: ["PROFILE_1", "PROFILE_2"],    │
│   achPayeeEmails: ["user1@test.com", "user2@test.com"]│
│ }                                                       │
└─────────────────────────────────────────────────────────┘
            │
            ▼
User clicks "Generate" button
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│  Validation Phase                                        │
├─────────────────────────────────────────────────────────┤
│ 1. Check all mandatory fields filled  ✓                │
│ 2. Validate ACH Comp IDs/Names count  ✓                │
│ 3. Validate Batches Quantity numeric  ✓                │
│ 4. Validate Transactions Count logic  ✓                │
│ 5. Validate ABAs if Options=ACH       ✓                │
│ 6. Validate ESend if needed           ✓                │
│ 7. Validate Email format              ✓                │
└─────────────────────────────────────────────────────────┘
            │
     (Success) ▼
    ┌─────────────────────┐
    │ Filename Popup      │
    │ [filename_____...] │
    │ [Download]          │
    └─────────────────────┘
            │
     (User confirms) ▼
┌──────────────────────────────────────────────────────────┐
│  Send to Backend API                                     │
│  POST /api/generate-file                                 │
│  Content: All form data + filename                       │
└──────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│  Backend Processing                                      │
│  ├─ Create PaymentData object                           │
│  ├─ Validate all fields again                           │
│  ├─ Generate NACHA records                              │
│  │   ├─ File header (using Immediate fields)           │
│  │   ├─ Batch records × Batches Quantity               │
│  │   │   ├─ Batch header (using Comp IDs/Names)        │
│  │   │   ├─ Transaction records × Trans. Count         │
│  │   │   └─ Batch trailer                              │
│  │   └─ File trailer                                    │
│  ├─ Format with proper indentation                      │
│  ├─ Generate .ACH file                                  │
│  └─ Send as download response                           │
└──────────────────────────────────────────────────────────┘
            │
            ▼
      File Downloaded
      (To Downloads folder)
```

---

## Options Selection Flow

```
User selects "Options" dropdown
            │
            ▼
┌─────────────────────────────────────────────┐
│  toggleACHFileOptionsVisibility()            │
│  (JavaScript function)                       │
└─────────────────────────────────────────────┘
            │
        ┌───┴───┬────────────┬──────────────┐
        │       │            │              │
        ▼       ▼            ▼              ▼
      "ACH"  "ACH &"      "ESend_"      (other)
             "ESend"       "Only"
        │       │            │              │
        ▼       ▼            ▼              ▼
    Show   Show ESend   Show ESend    Hide both
    ABAs   Hide ABAs    Hide ABAs
    Hide   Section      Section
    ESend

┌──────────────────────────────────┐
│ OPTION: ACH (Default)            │
├──────────────────────────────────┤
│ • ABAs field: VISIBLE (Required) │
│ • ESend section: HIDDEN          │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ OPTION: ACH & ESend              │
├──────────────────────────────────┤
│ • ABAs field: HIDDEN             │
│ • ESend section: VISIBLE         │
│   - ESend App: REQUIRED          │
│   - Profile Keys: REQUIRED       │
│   - Payee Emails: REQUIRED       │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ OPTION: ESend_Only               │
├──────────────────────────────────┤
│ • ABAs field: HIDDEN             │
│ • ESend section: VISIBLE         │
│   - ESend App: REQUIRED          │
│   - Profile Keys: REQUIRED       │
│   - Payee Emails: REQUIRED       │
└──────────────────────────────────┘
```

---

## Pre-Seed Data Population Flow

```
User selects "Use Pre-Seed Data" checkbox
            │
            ▼
Select Environment (e.g., "PR1")
            │
            ▼
Load environment from file_templates_config.yaml
PR1:
  PCM312P:
    ACH FILE:
      SAMPLE_FILE:
        attributes:
          achCompIds: ['123456789']
          achCompNames: ['TEST COMPANY']
            │
            ▼
Select Usergroup (e.g., "PCM312P")
            │
            ▼
Display File dropdown with ACH FILE files
            │
            ▼
User selects File (e.g., "SAMPLE_FILE")
            │
            ▼
┌─────────────────────────────────────────────┐
│  Populate Pre-Seed Data                      │
├─────────────────────────────────────────────┤
│ setGenerateTagValues('achCompIds',           │
│   ['123456789'])                             │
│                                              │
│ setGenerateTagValues('achCompNames',         │
│   ['TEST COMPANY'])                          │
│                                              │
│ setGenerateTagValues(                        │
│   'achBatchesQuantity', ['1'])               │
│ (default if not in yaml)                     │
│                                              │
│ setGenerateTagValues(                        │
│   'achTransactionsCount', ['1'])             │
│ (default if not in yaml)                     │
└─────────────────────────────────────────────┘
            │
            ▼
Form displays pre-seed values as blocks:
  ACH Comp IDs: [123456789] ✕
  ACH Comp Names: [TEST COMPANY] ✕
  Batches Qty: [1] ✕
  Trans. Count: [1] ✕

User can now:
  • Modify any pre-populated value
  • Fill in remaining fields (optional fields)
  • Select Options dropdown
  • Fill ESend/ABAs as needed
  • Click Generate
```

---

## Multi-Value Field Input Behavior

```
User types in multi-value field (e.g., ACH Comp Names)
            │
Input: "TEST COMPANY"
            │
            ▼
User presses COMMA or TAB or clicks elsewhere (blur)
            │
            ▼
┌─────────────────────────────────────────────┐
│  Block Conversion                            │
├─────────────────────────────────────────────┤
│ Input text "TEST COMPANY"                    │
│         ▼                                    │
│ Convert to block: [TEST COMPANY] ✕           │
│         ▼                                    │
│ Add to tags container                        │
│         ▼                                    │
│ Clear input field                            │
│         ▼                                    │
│ Ready for next value                         │
└─────────────────────────────────────────────┘
            │
            ▼
Display: [TEST COMPANY] ✕ [ANOTHER COMPANY] ✕ [scroll ≫]
            
If user clicks ✕ on a block:
            │
            ▼
Remove that block from field
Reflow remaining blocks
Update form state
```

---

## Validation Error Flow

```
User clicks "Generate" without filling mandatory fields
            │
            ▼
┌─────────────────────────────────────────────┐
│  Validation Check                            │
├─────────────────────────────────────────────┤
│ if (immediateDestination is empty) {         │
│   errors.push(                               │
│     "Immediate Destination is required"      │
│   );                                         │
│ }                                            │
│                                              │
│ if (achCompIds count !== achCompNames count)│
│   errors.push(                               │
│     "ACH Comp IDs and Names must match"      │
│   );                                         │
│ }                                            │
│                                              │
│ if (aba.length !== 9 or !numeric) {          │
│   errors.push(                               │
│     "ABAs must be exactly 9 digits"          │
│   );                                         │
│ }                                            │
│ ... more validations ...                     │
└─────────────────────────────────────────────┘
            │
        (if errors) ▼
┌─────────────────────────────────────────────┐
│  Error Popup Display                         │
├─────────────────────────────────────────────┤
│ ⚠ Form Validation Errors                    │
│                                              │
│ • Immediate Destination is required         │
│ • ACH Comp IDs and Names must match          │
│ • ABAs must be exactly 9 digits              │
│ • Transactions Count sum invalid             │
│                                              │
│ [OK]                                         │
└─────────────────────────────────────────────┘
            │
            ▼
User fixes errors and tries again
```

---

## Form State Persistence

```
User fills .ACH File form
Form state saved automatically:
  saveGenerateFormState('ACH FILE', formData)
            │
            ▼
User switches to "ACH NACHA XML" form
            │
Form state for .ACH FILE saved
Form state for ACH NACHA XML loaded/created
            │
            ▼
User switches back to ".ACH FILE" form
            │
            ▼
┌─────────────────────────────────────────────┐
│  Form Restoration                            │
├─────────────────────────────────────────────┤
│ restoreGenerateFormState('ACH FILE')         │
│   │                                          │
│   ├─ Restore immediateDestination: "22"    │
│   ├─ Restore immediateOrigin: "112412"     │
│   ├─ Restore achCompIds: [saved values]    │
│   ├─ ... restore all saved fields ...       │
│   │                                          │
│   └─ Set form to exact previous state       │
└─────────────────────────────────────────────┘
            │
            ▼
Form displays with all previous values intact
User can continue editing where they left off
```

---

## File Output Structure (Example)

```
Generated .ACH File Content:

<File>
    <FileInformation>
        <FileCreateDate>2026-04-23</FileCreateDate>
        <FileDescription>PAC T1 2026-04-23</FileDescription>
        <FileVersion>XMLv1.1 CSv6.7.2</FileVersion>
        <ImmediateDestination>22</ImmediateDestination>
        <ImmediateOrigin>112412</ImmediateOrigin>
        <ImmediateDestinationName>BONY</ImmediateDestinationName>
    </FileInformation>
    
    <Batch>
        <BatchDescription>Batch ABCD</BatchDescription>
        <CompanyID>123456789</CompanyID>
        <CompanyName>TEST COMPANY</CompanyName>
        <EffectiveDate>2026-04-23</EffectiveDate>
        <BatchStatus>AP</BatchStatus>
        <BatchUserGroup>PCM312P</BatchUserGroup>
        
        <Transactions>
            <NachaCCD>
                <ABA>011000015</ABA>
                <AccountNumber>123456</AccountNumber>
                <PayeeID>PAYEE001</PayeeID>
                <PayeeName1>John Doe</PayeeName1>
                <TranAmount>1000.00</TranAmount>
                <TranDate>2026-04-23</TranDate>
                <TranDescription>Payment</TranDescription>
            </NachaCCD>
            ... more transactions ...
        </Transactions>
    </Batch>
    
    ... more batches ...
    
</File>
```

---

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Generate File Modal System                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────┐        ┌──────────────────────────┐    │
│  │  Form Type Selector │        │  .ACH File Form          │    │
│  │ [ACH NACHA XML] ▼   │◄─────►│ ├─ Left Column           │    │
│  │ [ACH CAEFT XML]     │        │ ├─ Middle Column         │    │
│  │ [Checks XML]        │        │ └─ Right Column          │    │
│  │ [.ACH File]    ✓    │        └──────────────────────────┘    │
│  └─────────────────────┘                 │                       │
│                                          │                       │
│                                          ▼                       │
│                        ┌─────────────────────────────────┐       │
│                        │  Form State Manager              │       │
│                        │  ├─ Save state                   │       │
│                        │  ├─ Restore state                │       │
│                        │  ├─ Clear state                  │       │
│                        │  └─ Get form data                │       │
│                        └─────────────────────────────────┘       │
│                                          │                       │
│                                          ▼                       │
│                        ┌─────────────────────────────────┐       │
│                        │  Validation Engine               │       │
│                        │  ├─ Mandatory check              │       │
│                        │  ├─ Format validation            │       │
│                        │  ├─ Count matching               │       │
│                        │  └─ Email validation             │       │
│                        └─────────────────────────────────┘       │
│                                          │                       │
│              ┌───────────────────────────┴─────────────┐          │
│              │                                         │          │
│              ▼                                         ▼          │
│      ┌──────────────────┐              ┌──────────────────┐      │
│      │ Error Popup      │              │ File Generation  │      │
│      │ Shows all errors │              │ ├─ Backend call  │      │
│      │ User fixes       │              │ ├─ File download │      │
│      │ Try again        │              │ └─ Popup close   │      │
│      └──────────────────┘              └──────────────────┘      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Field Dependency Tree

```
.ACH File Form Fields
│
├─ ALWAYS REQUIRED
│  ├─ immediateDestination (default: 22)
│  ├─ immediateOrigin (default: 112412)
│  ├─ immediateDestinationName (default: BONY)
│  ├─ achCompIds
│  ├─ achCompNames
│  ├─ achBatchesQuantity
│  ├─ achTransactionsCount
│  └─ achOptions (always defaults to "ACH")
│
├─ OPTIONAL (No validation)
│  ├─ achFileName
│  ├─ achClientCompany
│  └─ achBankName
│
└─ CONDITIONAL (Depend on achOptions)
   │
   ├─ When achOptions = "ACH"
   │  └─ REQUIRED
   │     └─ achOptionsAbAs
   │        └─ Must be: 9 numeric digits each
   │
   └─ When achOptions = "ACH & ESend" OR "ESend_Only"
      └─ REQUIRED
         ├─ achEsendAppType (Name or ID)
         ├─ achEsendApp
         │  └─ Values match selected type
         ├─ achEsendProfileKeys
         │  └─ Can be different length from App
         └─ achPayeeEmails
            └─ Must be valid email format
```

---

## CSS Grid/Flexbox Layout

```
3-Column Layout Structure:

.formColumn {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

Left Column: { border-right: 1px solid #555; padding-right: 15px; }
Middle Column: { border-right: 1px solid #555; padding-right: 15px; }
Right Column: { (no right border) }

Each Field Group:
.formGroup {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

Multi-Value Field:
.tagInputContainer {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  width: 100%;
  overflow-x: auto;
  max-height: 120px;
  padding: 5px;
  border: 1px solid #444;
  border-radius: 3px;
}

Tag Block:
.tagBlock {
  background: #0078d4;
  color: white;
  padding: 3px 8px;
  border-radius: 3px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
```

---

## Summary

This comprehensive visual architecture document shows:

1. **Form Layout**: How the 3 columns are structured visually
2. **Data Flow**: How user input flows through validation to file generation
3. **Options Logic**: How Options dropdown controls field visibility
4. **Pre-Seed Integration**: How pre-seed data populates the form
5. **Multi-Value Behavior**: How users interact with comma-separated fields
6. **Error Handling**: How validation errors are displayed
7. **State Persistence**: How form data is saved and restored
8. **File Output**: Example of generated file structure
9. **Component Interaction**: How form parts interact
10. **Field Dependencies**: Which fields depend on others



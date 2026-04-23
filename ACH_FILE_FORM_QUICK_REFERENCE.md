# ACH FILE Form - Quick Reference Guide

## Form Layout Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    .ACH File Form (3 Partitions)            │
├─────────────────────────┬──────────────────┬────────────────┤
│   LEFT COLUMN           │  MIDDLE COLUMN   │  RIGHT COLUMN  │
├─────────────────────────┼──────────────────┼────────────────┤
│                         │                  │                │
│ 1. Immediate            │                  │                │
│    Destination [22] ×   │   (Empty)        │   (Empty)      │
│                         │                  │                │
│ 2. Immediate Origin     │                  │                │
│    [112412] ×           │                  │                │
│                         │                  │                │
│ 3. Immediate            │                  │                │
│    Destination Name     │                  │                │
│    [BONY] ×             │                  │                │
│                         │                  │                │
│ 4. ACH Comp IDs         │                  │                │
│    [tag1] × [tag2] ×    │                  │                │
│                         │                  │                │
│ 5. ACH Comp Names       │                  │                │
│    [tag1] × [tag2] ×    │                  │                │
│                         │                  │                │
└─────────────────────────┴──────────────────┴────────────────┘
```

## Field Configuration

| Field | Type | Default | Constraint | Notes |
|-------|------|---------|-----------|-------|
| Immediate Destination | Tag Input (Single) | 22 | Single value only | Numeric |
| Immediate Origin | Tag Input (Single) | 112412 | Single value only | Numeric |
| Immediate Destination Name | Tag Input (Single) | BONY | Single value only | Text |
| ACH Comp IDs | Tag Input (Multi) | (empty) | Multiple values allowed | Same count as Comp Names |
| ACH Comp Names | Tag Input (Multi) | (empty) | Multiple values allowed | Same count as Comp IDs |

## Key Features

### 1. Block Style Display
- All fields display values as tags in a block/badge style
- Each tag has a remove button (×) on the right
- Clicking the × instantly removes that tag

### 2. Default Values
- When form opens, the first 3 fields auto-populate with default values
- Defaults appear as removable tags
- User can modify or delete any default value

### 3. Multi-value Input
- For ACH Comp IDs and Names: Enter comma-separated values or press Enter after each value
- Examples:
  - Input: `comp1, comp2, comp3` → Creates 3 tags
  - Input: `comp1` [Enter] `comp2` [Enter] → Creates 2 tags

### 4. Validation Rules
- **ACH Comp IDs and Names must match in count**
  - If IDs has 3 values, Names must have exactly 3 values
  - Error shown before file generation

### 5. Pre-Seed Data Support
- Can auto-populate from configuration files
- Overrides default values when available
- Works with multi-value fields

## User Actions

### Adding a Value
1. Click in the input field (after existing tags)
2. Type your value
3. Press Enter or comma (,) to add the tag
4. Tag appears with × button

### Removing a Value
1. Click the × button on any tag
2. Tag immediately disappears
3. Input field gains focus

### Modifying a Value
1. Click × to remove the old tag
2. Type and add the new value
3. New tag replaces the old one

## Validation Examples

### Valid Configuration
```
ACH Comp IDs: [ID1] × [ID2] × [ID3] ×
ACH Comp Names: [Name1] × [Name2] × [Name3] ×
✓ VALID: Both have 3 values
```

### Invalid Configuration
```
ACH Comp IDs: [ID1] × [ID2] ×
ACH Comp Names: [Name1] × [Name2] × [Name3] ×
✗ INVALID: IDs has 2 values, Names has 3
Error: "ACH Comp IDs and ACH Comp Names must have the same number of values."
```

## Integration with Pre-Seed Data

When pre-seed data is enabled:
1. Select Environment → UserGroup → Pre-Seed File
2. If pre-seed file contains `ach_comp_ids` and `ach_comp_names`:
   - Values automatically populate the fields
   - Override default values
3. Defaults (Immediate Destination/Origin/Name) still appear

## CSS Classes Used

- `.formColumn` - Column container
- `.formGroup` - Field group wrapper
- `.formLabel` - Field label styling
- `.tagInputContainer` - Tag input wrapper
- `.tag` - Individual tag styling
- `.tagRemoveBtn` - Remove button (×) styling

## Related Forms

- **ACH NACHA XML**: Uses same `achCompIds` and `achCompNames` fields with same validation rules
- **ACH CAEFT XML**: Also uses the same fields
- **CHECKS XML**: Uses different fields (CheckProfiles instead)

## Development Notes

### Component Used
- `createTagInput()` function in `index.html`
- Handles rendering, validation, and user interaction
- Supports configurable options (singleValueOnly, numericPositiveOnly, etc.)

### Event Listeners
- `keydown`: Handles Enter and Comma keys
- `blur`: Finalizes pending input
- `paste`: Handles bulk input via clipboard

### Data Storage
- Field values stored in form state cache
- Pre-seed values stored in activePreSeedValuesByForm
- State automatically preserved between form switches

## Testing Checklist

- [ ] Open ACH FILE form - verify 3 partitions visible
- [ ] Check default values populate in tags
- [ ] Add new tags using comma or Enter
- [ ] Remove tags using × button
- [ ] Test multi-value input for ACH Comp fields
- [ ] Verify validation error on mismatch counts
- [ ] Test pre-seed data loading
- [ ] Verify form state persists when switching forms
- [ ] Test with mix file feature if enabled

## Troubleshooting

### Tags not appearing
- Ensure form has fully loaded (50ms delay built in)
- Check browser console for JS errors
- Verify `createTagInput()` function is defined

### Default values missing
- Check if form successfully rendered
- Verify `setTimeout` delay is sufficient
- Check if pre-seed data is overriding defaults

### Validation not triggering
- Ensure `validateBeforeGenerate()` is called before file generation
- Check if file type is correctly identified as 'ACH FILE'
- Verify `getSnapshotTagValues()` function works correctly

### Pre-seed not loading
- Verify pre-seed configuration file exists
- Check environment and usergroup selections
- Verify `ach_comp_ids` and `ach_comp_names` exist in config


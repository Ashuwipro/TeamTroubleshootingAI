# ESend Batch Mapping - Developer Quick Reference

## Architecture Overview

```
User Interface (HTML/JS)
    ↓
Form Submission (JSON)
    ↓
Flask Route: /generate-xml
    ↓
PaymentData.from_form_data()  ← Parsing & Validation
    ↓
ACHNachaXMLGenerator.generate()  ← XML Generation with Batch Resolution
    ↓
XMLFieldMapper.get_*_for_batch()  ← Per-Batch Value Resolution
    ↓
XML Output File
```

## Key Classes & Methods

### PaymentData (payment_generator.py:14)

**Initialization**
```python
self.esend_app_value: str = ''
self.esend_app_values: List[str] = []
self.esend_profile_keys: str = ''
self.esend_profile_key_values: List[str] = []
```

**Parsing (from_form_data)**
```python
data.esend_app_values = cls._parse_csv_values(data.esend_app_value)
if data.esend_app_values:
    cls._validate_batch_value_count(data.esend_app_values, 
                                    data.batches_quantity, 
                                    'ESend App')
```

**Batch Resolution**
```python
def get_esend_app_for_batch(self, batch_index: int) -> str:
    """Returns ESend app for this batch"""
    if len(self.esend_app_values) == 1:
        return self.esend_app_values[0]  # Single: broadcast to all
    return self.esend_app_values[batch_index]  # Per-batch
```

### XMLFieldMapper (payment_generator.py:261)

**Payment Values Mapping**
```python
@staticmethod
def get_payment_values(payment_data: PaymentData,
                      transaction_index: int = 0,
                      batch_index: int = 0) -> Dict[str, str]:
    """Returns field values for a single payment transaction"""
    profile_key = payment_data.get_esend_profile_key_for_batch(batch_index)
    app_name = payment_data.get_esend_app_for_batch(batch_index)
    return {
        'esend_app_name': app_name,
        'profile_key': profile_key,
        # ... other fields
    }
```

### ACHNachaXMLGenerator (payment_generator.py:373)

**Template Resolution**
```python
mode, batch_file, payment_file = self._resolve_template_files(payment_data)
# Returns: ('esend', 'batch_esend.xml', 'payment_esend.xml')
```

**Batch XML Formatting**
```python
batch_info = batch_template % (
    payment_values['esend_app_name'],  # Per-batch value
    batch_values['batch_description'],
    # ... other fields
)
```

## Data Flow Example

### Input
```json
{
  "fileType": "ACH NACHA XML",
  "batchesQuantity": 2,
  "esendAppValue": "AppA,AppB",
  "esendProfileKeys": "KeyX"
}
```

### Processing
```python
# 1. Parse
esend_app_values = ['AppA', 'AppB']
esend_profile_key_values = ['KeyX']

# 2. Validate
len(['AppA', 'AppB']) == 2  # OK (equals batchesQuantity)
len(['KeyX']) == 1  # OK (single value)

# 3. Resolve per batch
Batch 0: app = 'AppA', key = 'KeyX'
Batch 1: app = 'AppB', key = 'KeyX'
```

### Output XML
```xml
<Batch>
    <BatchInformation>
        <ApplicationInfo>
            <ApplicationName>AppA</ApplicationName>
        </ApplicationInfo>
        <ESendProfileKey>KeyX</ESendProfileKey>
    </BatchInformation>
</Batch>
<Batch>
    <BatchInformation>
        <ApplicationInfo>
            <ApplicationName>AppB</ApplicationName>
        </ApplicationInfo>
        <ESendProfileKey>KeyX</ESendProfileKey>
    </BatchInformation>
</Batch>
```

## Frontend Validation (index.html:2314)

```javascript
// Check ESend enabled
const esendEnabled = options === 'ACH & ESend' || options === 'ESend_Only';

// Validate ESend App
if (esendAppValues.length > 1 && esendAppValues.length !== batchesQuantity) {
    issues.push('ESend App must contain either one value for all batches 
                 or exactly one value per batch.');
}

// Validate ESend Profile Keys (independent)
if (esendProfileKeys.length > 1 && esendProfileKeys.length !== batchesQuantity) {
    issues.push('ESend Profile Keys must contain either one value for all 
                 batches or exactly one value per batch.');
}
```

## Error Messages

| Condition | Error Message |
|-----------|---------------|
| App count = 2, Batches = 3 | "ESend App must contain either one value for all batches or exactly one value per batch." |
| Key count = 2, Batches = 3 | "ESend Profile Keys must contain either one value for all batches or exactly one value per batch." |
| Invalid email with ESend | "Payee Emails must be valid email addresses when ESend details are provided." |

## Testing Utilities

### Run All Tests
```bash
# Unit tests
python test_esend_batch_mapping.py

# Integration tests  
python test_xml_generation_integration.py

# HTTP API tests
python test_http_api_integration.py
```

### Quick HTTP Test
```python
import requests
response = requests.post(
    'http://localhost:5000/generate-xml',
    json={
        'fileType': 'ACH NACHA XML',
        'batchesQuantity': 2,
        'esendAppValue': 'App1,App2',
        'esendProfileKeys': 'Key1'
        # ... other required fields
    }
)
```

## Template File Mapping

| File Type | ESend Option | Batch Template | Payment Template |
|-----------|--------------|-----------------|------------------|
| ACH NACHA | No | batch.xml | payment.xml |
| ACH NACHA | Yes | batch_esend.xml | payment_esend.xml |
| ACH NACHA | IAT | batch_iat.xml | payment_iat.xml |
| ACH NACHA | IAT+ESend | batch_iat_esend.xml | payment_iat_esend.xml |
| ACH CAEFT | No | N/A (uses standard) | N/A |
| ACH CAEFT | Yes | batch_caeft_esend.xml | payment_caeft_esend.xml |

## Constants & Configuration

```python
# payment_generator.py
VALID_PAYMENT_TYPES = ('CCD', 'CTX', 'PPD', 'IAT')
VALID_OPTIONS = ('ACH', 'ACH & ESend', 'ESend_Only')
VALID_BATCH_CREDIT_DEBIT = ('Credit', 'Debit')

# Validation Rules
ESend_App_Rule = "1 OR batch_quantity"
ESend_ProfileKeys_Rule = "1 OR batch_quantity"
Independent = True  # No cross-field dependency
```

## Common Modifications

### Add New ESend Variant

1. Create template files:
   - `batch_xxxxx.xml` 
   - `payment_xxxxx.xml`

2. Update template resolution (payment_generator.py:396):
   ```python
   if file_type == 'YOUR_TYPE':
       if has_esend:
           return 'your_mode', 'batch_xxxxx.xml', 'payment_xxxxx.xml'
   ```

3. Add formatting logic (payment_generator.py:438):
   ```python
   if mode == 'your_mode':
       return payment_template % (
           payment_values['esend_app_name'],
           # ... other fields
       )
   ```

### Add New Batch-Aware Field

1. Add to PaymentData class:
   ```python
   self.new_field: str = ''
   self.new_field_values: List[str] = []
   ```

2. Add parsing in from_form_data():
   ```python
   data.new_field = form_data.get('newField', '')
   data.new_field_values = cls._parse_csv_values(data.new_field)
   if data.new_field_values:
       cls._validate_batch_value_count(data.new_field_values, 
                                       data.batches_quantity, 'New Field')
   ```

3. Add resolver method:
   ```python
   def get_new_field_for_batch(self, batch_index: int) -> str:
       if len(self.new_field_values) == 1:
           return self.new_field_values[0]
       return self.new_field_values[batch_index]
   ```

## Performance Considerations

- **Batch Resolution**: O(1) array lookup
- **Validation**: O(n) where n = number of values
- **XML Generation**: Linear with batches + transactions
- **Caching**: Template cache speeds up repeated generations
- **Memory**: ESend field lists are small (typically < 50 entries)

## Debugging Tips

### Check Parsed Values
```python
print(f"ESend App values: {payment_data.esend_app_values}")
print(f"ESend Profile Key values: {payment_data.esend_profile_key_values}")
```

### Verify Batch Resolution
```python
for batch_idx in range(payment_data.batches_quantity):
    app = payment_data.get_esend_app_for_batch(batch_idx)
    key = payment_data.get_esend_profile_key_for_batch(batch_idx)
    print(f"Batch {batch_idx}: app={app}, key={key}")
```

### Check Generated XML
```python
import xml.etree.ElementTree as ET
root = ET.fromstring(xml_content)
for batch in root.findall('.//Batch'):
    app = batch.find('.//ApplicationName').text
    print(f"Found app: {app}")
```

### Enable Debug Logging
```python
# In app.py
if __name__ == '__main__':
    app.run(debug=True)  # Enables Flask debug mode
```

## Related Files

- **Frontend**: `backend/static/index.html`
- **Backend**: `backend/payment_generator.py`
- **Routes**: `backend/app.py`
- **Templates**: `backend/templates/*.xml`
- **Tests**: `test_*.py`
- **Docs**: `ESEND_*.md`, `COMPLETION_REPORT.md`

## Links & References

- ESend Field Mapping: line 208-226 in payment_generator.py
- Frontend Validation: line 2314-2337 in index.html
- XML Generation: line 616-673 in payment_generator.py
- API Route: line 508-521 in app.py

---

**Last Updated**: April 16, 2026  
**Status**: ✅ Production Ready  
**Test Coverage**: 20+ tests, 100% pass rate


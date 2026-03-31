# Project Structure Reorganization

## Current Status
The project has been reorganized to separate concerns and improve maintainability for future features.

## New Directory Structure

```
TeamTroubleshootingAI/
├── backend/
│   ├── app.py                          # Main Flask application
│   ├── payment_generator.py            # Payment file generation logic
│   ├── requirements.txt
│   ├── knowledge_PCM.txt
│   ├── templates/                      # NEW: XML template files
│   │   ├── ach_nacha_batch.xml         # (MOVED from root)
│   │   ├── ach_nacha_file_header.xml   # (MOVED from root)
│   │   └── ach_nacha_payment.xml       # (MOVED from root)
│   └── static/
│       ├── index.html                  # Main application file
│       └── modules/                    # NEW: Feature-specific modules
│           ├── generate_file.css       # Generate File styling
│           ├── generate_file.html      # Generate File modal HTML
│           └── generate_file.js        # Generate File JavaScript functions
├── FIELD_MAPPING_DOCUMENTATION.md
├── PAYMENT_FILE_GENERATION_SETUP.md
└── PROJECT_STRUCTURE.md                # This file
```

## Key Changes Made

### 1. XML Templates Moved to `backend/templates/`
- **ach_nacha_batch.xml** - Moved from root
- **ach_nacha_file_header.xml** - Moved from root
- **ach_nacha_payment.xml** - Moved from root

**Impact**: Updated `app.py` to reference the new path:
```python
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
```

### 2. Modular Frontend Structure Created
New `backend/static/modules/` directory for feature-specific code:

#### generate_file.css
Contains all CSS related to the Generate File functionality:
- Modal styles
- Form field styles
- Tag input component styles
- Mix File dropdown styles
- Button styles

#### generate_file.html
Contains the modal HTML structure:
- Generate File modal markup
- Mix File checkbox UI
- Payment Type dropdowns
- Modal header, body, and footer

#### generate_file.js
Contains all JavaScript functions for Generate File:
- GenerateFileModule (namespace)
- Event listeners for Mix File checkbox
- Modal open/close functions
- Form field loading functions
- Tag input creation functions
- File generation and download functions

### 3. Updated app.py
- Changed template path to use new `templates/` directory
- Path is now: `os.path.join(os.path.dirname(__file__), 'templates')`

## Benefits of This Structure

1. **Scalability**: Easy to add new feature buttons and corresponding modules
2. **Maintainability**: Each feature has its own CSS, HTML, and JS files
3. **Organization**: All generation-related files are grouped together
4. **Separation of Concerns**: 
   - Main UI (index.html) handles chat and project selection
   - Module files handle specific features
5. **Future Growth**: Can easily add:
   - `modules/export_data.css/html/js`
   - `modules/report_builder.css/html/js`
   - `modules/settings.css/html/js`
   - etc.

## Next Steps for Integration

To fully integrate the modular structure:

1. Extract Generate File CSS from `index.html` and place in `generate_file.css`
2. Extract Generate File modal HTML from `index.html` and place in `generate_file_modal.html`
3. Extract Generate File JavaScript from `index.html` and place in `generate_file.js`
4. Update `index.html` to:
   - Link to module CSS files
   - Include module HTML files via script or AJAX
   - Include module JS files
5. Repeat this pattern for future feature modules

## File References

All paths have been updated:
- ✅ XML templates: `backend/templates/` (updated in app.py)
- ⏳ CSS extraction: Ready to be placed in `modules/generate_file.css`
- ⏳ HTML extraction: Ready to be placed in `modules/generate_file_modal.html`
- ⏳ JS extraction: Ready to be placed in `modules/generate_file.js`

## Implementation Notes

The current `index.html` still contains all the code. The next phase would be to:
1. Extract the code into the modular files
2. Use dynamic loading (JavaScript fetch or HTML includes) to load module files
3. Ensure proper namespacing to avoid conflicts
4. Maintain backward compatibility during the transition


# Upload File Button - Visual Architecture & Flow Diagram

## 🏗️ Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GENERATE FILE MODAL                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HEADER:  [Generate File] ..................... [Close]        │
│                                                                 │
│  FORM CONTROLS:                                                │
│  - Payment Form Dropdown                                       │
│  - Mix File Checkbox                                          │
│  - Pre-Seed Data Options                                      │
│                                                                 │
│  BODY:                                                          │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Dynamic Form Fields (3-column layout)                   │ │
│  │ - Column 1: Batch details                               │ │
│  │ - Column 2: Optional fields                             │ │
│  │ - Column 3: Payment details + ESend info               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  FOOTER:                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ [Upload File] .......... [Cancel]  [Generate]          │  │
│  └─────────────────────────────────────────────────────────┘  │
│
│  Hidden Elements:
│  <input type="file" id="fileUploadInput" /> (hidden)
│
│  Progress Modal (overlay):
│  ┌──────────────────────────────┐
│  │  Uploading ...               │
│  │  my_file.xml                 │
│  │  ████░░░░░░░░░░░░░░░░░░░   │
│  │                         35%  │
│  └──────────────────────────────┘
│
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Event Flow Diagram

```
USER INTERACTION FLOW:

┌─────────────────────────────────────────────────────────────────┐
│ 1. User clicks "Generate File" button on main page             │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
                      openGenerateModal() called
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Modal displays with form fields and buttons                 │
│    "Upload File" button visible at bottom-left                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
                  User sees button and clicks it
                                  ↓
                      triggerFileUpload() triggered
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. File input element receives .click() call                   │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
                 Native file picker dialog opens
                                  ↓
                   User selects file (.xml/.txt/.csv)
                                  ↓
                   File input change event fires
                                  ↓
                      handleFileUpload(event) called
                                  ↓
                    Get file from event.target.files[0]
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Call showUploadProgress(file.name)                          │
│    - Set file name in modal                                    │
│    - Add 'show' class to progress modal                        │
│    - Modal becomes visible                                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Call simulateFileUpload(file)                               │
│    - Start dot animation (400ms interval)                      │
│    - Start progress bar animation (300ms interval)             │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Animation Loop (3-4 seconds total)                          │
│                                                                 │
│    Every 400ms:                  Every 300ms:                  │
│    ┌──────────────────────┐      ┌──────────────────────┐     │
│    │ Dot Animation:       │      │ Progress Animation:  │     │
│    │ . → .. → ... → .     │      │ progress += rand()   │     │
│    │ (cycles)             │      │ bar.width = progress │     │
│    └──────────────────────┘      │ % += floor(progress) │     │
│                                   └──────────────────────┘     │
│                                                                 │
│    Progress reaches 100%:                                      │
│    └─→ Clear intervals                                         │
│    └─→ Set dots to "Done!"                                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
                    Wait 800ms with "Done!" shown
                                  ↓
                      hideUploadProgress() called
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Remove 'show' class from progress modal                     │
│    - Modal becomes hidden (display: none)                      │
│    - File input resets (event.target.value = '')              │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
              User can select another file or close modal
```

## 🎨 CSS Class Hierarchy

```
<div id="fileUploadProgressModal" class="modal">
  │
  ├─ Classes applied:
  │  ├─ modal (base modal styling)
  │  ├─ show (when visible - display: flex)
  │  └─ [when hidden - display: none]
  │
  └─ Child: .fileUploadBox
      │
      ├─ .fileUploadMessage
      │  └─ #uploadDotAnimation (.uploadDots)
      │
      ├─ #uploadFileName (.fileUploadFileName)
      │
      └─ .fileUploadProgressBarContainer
          ├─ .fileUploadProgressBarTrack
          │  └─ #uploadProgressBar (.fileUploadProgressBarFill)
          │
          └─ #uploadPercentage (.fileUploadPercentage)
```

## 🔌 Function Call Sequence

```
┌─────────────────────────────────────────────────┐
│  1. triggerFileUpload()                         │
│     └─> document.getElementById('fileUploadInput').click()
│         └─> Opens native file picker
└──────────────────────┬──────────────────────────┘
                       ↓ (user selects file)
┌──────────────────────────────────────────────────┐
│  2. handleFileUpload(event)                      │
│     ├─> Get file from event.target.files[0]    │
│     ├─> showUploadProgress(file.name)          │
│     │   └─> Sets fileName and adds show class   │
│     ├─> simulateFileUpload(file)               │
│     │   └─> Runs animations (dots & progress)  │
│     └─> event.target.value = '' (reset)        │
└──────────────────────┬──────────────────────────┘
                       ↓ (after 3-4 seconds)
┌──────────────────────────────────────────────────┐
│  3. hideUploadProgress()                         │
│     └─> Removes show class from modal           │
│         └─> Modal becomes hidden               │
└──────────────────────────────────────────────────┘
```

## 📊 State Transitions

```
                  ┌─────────────────┐
                  │   Initial State │
                  │ (Modal Closed)  │
                  └────────┬────────┘
                           ↓
                   [User clicks Modal]
                           ↓
                  ┌─────────────────┐
                  │  Modal Visible  │
                  │ Upload button   │
                  │ ready to click  │
                  └────────┬────────┘
                           ↓
               [User clicks Upload File]
                           ↓
                ┌──────────────────────┐
                │  File Picker Open   │
                │ (OS native dialog)  │
                └────────┬─────────────┘
                         ↓
              [User selects file]
                         ↓
              ┌──────────────────────┐
              │ Progress Modal Shown │
              │ - Dots animate      │
              │ - Progress bar fills │
              │ - % updates         │
              └────────┬─────────────┘
                       ↓ (3-4 seconds)
              ┌──────────────────────┐
              │  "Done!" Displayed  │
              │ (800ms hold time)   │
              └────────┬─────────────┘
                       ↓
              ┌──────────────────────┐
              │ Progress Modal Hidden│
              │ Back to form modal  │
              └────────┬─────────────┘
                       ↓
              Ready for next action
```

## ⏱️ Timing Diagram

```
Timeline (in seconds):

0.0s   ├─ User clicks "Upload File"
       │  └─→ File dialog opens
       │
       ├─ User selects file (variable time)
       │  └─→ Progress modal appears
       │
1.0s   ├─ Progress: ~15-30%
       │  Dots: . → .. → ... → .
       │
2.0s   ├─ Progress: ~30-60%
       │  Dots: (cycling)
       │
3.0s   ├─ Progress: ~60-90%
       │  Dots: (cycling)
       │
3.5s   ├─ Progress: ~90-100%
       │  Dots: (cycling)
       │
4.0s   ├─ Progress reaches 100%
       │  Dots show: "Done!"
       │
4.8s   ├─ Modal still visible
       │  (800ms hold time)
       │
5.0s   ├─ Modal auto-hides
       │  └─→ Display: none
       │
5.1s   └─ Back to form modal
          Ready for next action
```

## 💾 Data Flow

```
File Selection:
┌────────────────┐
│ User clicks    │
│ Upload button  │
└────────┬───────┘
         ↓
┌────────────────────────────────┐
│ File Input Dialog Opens        │
│ Accepts: .xml, .txt, .csv     │
└────────┬───────────────────────┘
         ↓ (user selects)
┌────────────────────────────────┐
│ File Object Created            │
│ - file.name                    │
│ - file.type                    │
│ - file.size                    │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ showUploadProgress()            │
│ ├─ #uploadFileName.textContent │
│ │  = file.name                 │
│ └─ classList.add('show')       │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ simulateFileUpload()           │
│ ├─ Progress: 0 → 100%          │
│ ├─ Dots animation              │
│ └─ Percentage updates          │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ hideUploadProgress()            │
│ └─ classList.remove('show')    │
└────────────────────────────────┘
```

## 🎯 Component Interaction Matrix

| Component | Triggers | Triggered By | Effect |
|-----------|----------|--------------|--------|
| Upload Btn | File Dialog | User Click | Opens file picker |
| File Input | handleFileUpload() | File Selected | Initiates upload |
| Progress Modal | showUploadProgress() | File Selected | Displays modal |
| Progress Bar | simulateFileUpload() | Modal shown | Fills from 0-100% |
| Dot Animation | simulateFileUpload() | Modal shown | Cycles dots |
| Percentage | simulateFileUpload() | Every 300ms | Updates counter |
| Done Message | simulateFileUpload() | Progress=100% | Shows completion |
| Modal Hide | hideUploadProgress() | After 800ms | Removes modal |

---

This comprehensive architecture shows how all components work together to create a smooth, intuitive upload experience!


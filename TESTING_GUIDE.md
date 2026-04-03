# Testing Guide - Eye Icon Toggle Fix

## Step-by-Step Testing Instructions

### Prerequisites
- Flask server running at http://localhost:5000
- Browser opened to the application
- Browser DevTools available (F12)

### Test 1: Verify Eye Icon is Visible

**Steps:**
1. Click "Drop File" button to open the modal
2. Look at the password input field in the modal header
3. You should see a light gray eye icon (👁) to the right of the password field

**Expected Result:** 
- Eye icon is clearly visible in the password field
- Icon is light gray (#cccccc) in color
- Icon is positioned inside the password field, not outside

**If Icon is Not Visible:**
1. Open DevTools (F12)
2. Go to Console tab
3. You should see: `DOMContentLoaded fired, togglePassword: [object HTMLElement]`
4. If you see `togglePassword or password not found`, refresh the page
5. Right-click on the password field and "Inspect Element"
6. Look for `<i id="togglePassword" class="fas fa-eye eyeIcon"></i>`
7. Check the "Styles" panel for the `.eyeIcon` CSS rules
8. Verify `color: #cccccc` is applied
9. Check Font Awesome is loaded: Network tab → search for "font-awesome"

### Test 2: Test Eye Icon Hover Effect

**Steps:**
1. Hover your mouse over the eye icon
2. The icon should change to blue and slightly enlarge

**Expected Result:**
- Icon color changes to #007acc (blue)
- Icon appears to scale up slightly
- Cursor changes to pointer

### Test 3: Test Password Visibility Toggle

**Steps:**
1. Enter some text in the password field (e.g., "test123")
2. The text should appear as dots (hidden)
3. Click the eye icon
4. The text should now be visible

**Expected Result:**
- First click: Password becomes visible, icon changes to eye-with-slash (👁‍🗨)
- Second click: Password becomes hidden again, icon changes back to eye (👁)
- Console should show: `"Eye icon clicked, current type: password"` and `"Password now visible"` or `"Password now hidden"`

### Test 4: Test CONNECT Button Toggle

**Steps:**
1. Enter "admin" in Username field
2. Enter "password123" in Password field
3. Click CONNECT button
4. Button should change to green and say "CONNECTED"
5. Username and Password fields should become disabled (grayed out)
6. Click CONNECTED button again
7. Button should change back to blue and say "CONNECT"
8. Fields should be enabled again and cleared

**Expected Result:**
- First click CONNECT: 
  - Button text: "CONNECT" → "CONNECTED"
  - Button color: blue → green
  - Fields disabled (cannot type)
  - Console: `"Connected - fields disabled"`
  
- Second click CONNECTED:
  - Button text: "CONNECTED" → "CONNECT"
  - Button color: green → blue
  - Fields enabled (can type)
  - Fields cleared (empty)
  - Password type reset to hidden
  - Eye icon reset to eye (👁)
  - Console: `"Disconnected - fields enabled and cleared"`

### Test 5: Test Empty Field Validation

**Steps:**
1. Leave Username empty
2. Try to click CONNECT button
3. An alert should appear

**Expected Result:**
- Alert message: "Please enter both username and password"
- Fields remain enabled
- Button text remains "CONNECT"

### Test 6: Test with Password Visible

**Steps:**
1. Enter username and password
2. Click the eye icon to make password visible
3. Click CONNECT
4. Click CONNECTED to disconnect
5. Verify password field is reset to hidden

**Expected Result:**
- Eye icon automatically resets to show hidden password icon
- Password field type reverts to "password"
- Fields are cleared and enabled

## Browser Console Output - Expected Messages

### On Page Load
```
DOMContentLoaded fired, togglePassword: [object HTMLElement]
```

### On Eye Icon Click (First Time - Show Password)
```
Eye icon clicked, current type: password
Password now visible
```

### On Eye Icon Click (Second Time - Hide Password)
```
Eye icon clicked, current type: text
Password now hidden
```

### On CONNECT Click (With Valid Input)
```
Connect button clicked, text: CONNECT
Username: admin Password: password123
Connected - fields disabled
```

### On CONNECTED Click (To Disconnect)
```
Connect button clicked, text: CONNECTED
Disconnected - fields enabled and cleared
```

### If Elements Not Found (Requires Refresh)
```
togglePassword or password not found
connectBtn not found
```

## CSS Inspection Checklist

Right-click password field → Inspect → Check these CSS properties:

### .passwordContainer
- [ ] position: relative
- [ ] display: flex
- [ ] align-items: center
- [ ] flex: 1
- [ ] min-width: 0

### .passwordContainer input
- [ ] padding-right: 40px
- [ ] width: 100%
- [ ] flex: 1

### .eyeIcon
- [ ] position: absolute
- [ ] right: 12px
- [ ] top: 50%
- [ ] transform: translateY(-50%)
- [ ] color: #cccccc
- [ ] cursor: pointer
- [ ] z-index: 10
- [ ] pointer-events: auto
- [ ] display: inline-block

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Icon invisible | Clear cache (Ctrl+Shift+Delete), hard refresh (Ctrl+F5) |
| Icon not clickable | Check z-index in DevTools, ensure pointer-events: auto |
| Icon outside field | Check right: 12px and padding-right: 40px are applied |
| Toggle not working | Refresh page, check console for "DOMContentLoaded fired" message |
| Wrong icon displayed | Verify Font Awesome classes (fas fa-eye, fas fa-eye-slash) |
| Button toggle not working | Clear browser cache and refresh |

## Performance Notes

- Font Awesome loaded from CDN (external)
- All CSS rules are inline in `<style>` tag
- JavaScript uses event delegation (one listener per element)
- No external dependencies beyond Font Awesome

## Files Modified

1. `/backend/static/index.html`
   - Line 7: Added Font Awesome CDN
   - Lines 601-637: Updated CSS for password container and eye icon
   - Line 751: Changed eye icon HTML from span to i element
   - Lines 1564-1636: Updated JavaScript event listeners



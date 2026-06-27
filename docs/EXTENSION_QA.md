# Extension QA Checklist

## Pre-requisites
- [ ] Extension loaded as unpacked in Chrome
- [ ] Backend running locally
- [ ] User authenticated in web app (for token)

## Test Cases

### 1. Unauthenticated State
- [ ] Open extension popup on any page
- [ ] Should show API URL and token input fields
- [ ] Enter valid credentials
- [ ] Click Connect
- [ ] Should transition to next view

### 2. Invalid Page State
- [ ] Navigate to google.com
- [ ] Open extension popup
- [ ] Should show "Not a LinkedIn Profile" message
- [ ] Navigate to linkedin.com/company/google/
- [ ] Open extension popup
- [ ] Should show "Not a LinkedIn Profile" message

### 3. New Profile State
- [ ] Navigate to a LinkedIn profile not yet saved
- [ ] Open extension popup
- [ ] Should show name input (pre-filled from page title)
- [ ] Should show role, company, priority, action fields
- [ ] Fill in details
- [ ] Click Save Profile
- [ ] Should show success message
- [ ] Verify person appears in web app

### 4. Existing Profile State
- [ ] Navigate to a previously saved LinkedIn profile
- [ ] Open extension popup
- [ ] Should show person name, stage, priority
- [ ] Should show quick action buttons

### 5. Quick Actions
- [ ] Click "Accepted" button
- [ ] Should show success message
- [ ] Verify stage updates in web app
- [ ] Click "Message Sent" button
- [ ] Verify next action updates

### 6. Notes
- [ ] Type a note in the note field
- [ ] Click an action button
- [ ] Verify note appears in activity timeline

### 7. Templates
- [ ] Scroll to templates section
- [ ] Should load templates from web app
- [ ] Click "Copy" on a template
- [ ] Verify "Copied!" feedback
- [ ] Paste into LinkedIn message box
- [ ] Verify template renders correctly

### 8. Snooze and Archive
- [ ] Test snooze functionality (if implemented)
- [ ] Test archive functionality (if implemented)

## Edge Cases
- [ ] Network failure shows error state
- [ ] Invalid token shows unauthenticated view
- [ ] Very long names truncate correctly
- [ ] Special characters in notes render properly

## Notes
- Date: ___________
- Tester: ___________
- Issues Found: ___________

# Extension

React MV3 Chrome extension for NetworkPilot CRM.

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

The built extension will be in the `dist/` folder.

## Install (Unpacked)

### Prerequisites
- Google Chrome browser
- Backend API deployed and running
- Supabase Google OAuth enabled
- User account created in the web app or through the extension

### Steps
1. Run `npm run build` to build the extension
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked" button
5. Select the `dist/` folder from this directory
6. The extension icon should appear in your Chrome toolbar

### First Time Setup
1. Click the extension icon
2. Enter your API URL (e.g., `https://your-app.onrender.com/api/v1`)
3. Click "Continue with Google"
4. Pick an existing workspace or create the first one

The extension uses the same Supabase account as the frontend. Profiles saved
from the extension are stored through the backend API in the selected workspace,
so they appear in the frontend People list. Updates made in the frontend are
visible from the extension when viewing the same LinkedIn profile.

### Google OAuth Redirect
For Chrome extension OAuth, add this redirect URL in Supabase:

```text
https://[EXTENSION_ID].chromiumapp.org/auth
```

For unpacked local testing, find `[EXTENSION_ID]` at `chrome://extensions/`
after loading the built `dist/` folder.

## Usage

### Save a New Profile
1. Navigate to a LinkedIn profile page
2. Click the extension icon
3. Fill in the details (name, role, company, priority)
4. Select initial action (Invite Sent, Saved for Later, etc.)
5. Click "Save Profile"

### Update an Existing Profile
1. Navigate to a previously saved LinkedIn profile
2. Click the extension icon
3. Use quick action buttons (Accepted, Message Sent, Follow-up, etc.)
4. Add optional notes
5. Actions are recorded immediately

### Copy Templates
1. When viewing a saved profile in the extension
2. Scroll to the Templates section
3. Select a category filter if needed
4. Click "Copy" on any template
5. Paste into LinkedIn message box

## Permissions

This extension requests minimal permissions:
- `storage` - Store Supabase session and selected workspace
- `activeTab` - Read current tab URL for LinkedIn profile detection
- `identity` - Run Google OAuth in Chrome

The extension does NOT:
- Inject scripts into LinkedIn pages
- Scrape LinkedIn DOM
- Send automated messages
- Read LinkedIn inbox

## Troubleshooting

### "Not a LinkedIn Profile" error
- Ensure you're on a LinkedIn profile page (linkedin.com/in/username)
- Company pages, job listings, and feed are not supported

### Authentication errors
- Ensure Google OAuth is enabled in Supabase
- Ensure the Chrome extension redirect URL is allowed in Supabase
- Confirm the extension uses the same Supabase URL/anon key as the frontend

### Extension not saving
- Check that backend is running and accessible
- Verify API URL is correct
- Confirm the selected workspace exists in the web app
- Check browser console for errors

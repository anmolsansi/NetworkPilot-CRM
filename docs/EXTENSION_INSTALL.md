# Extension Installation Guide

## Quick Install (Unpacked)

### Step 1: Build the Extension
```bash
cd extension
npm install
npm run build
```

### Step 2: Load in Chrome
1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable **Developer mode** (top right toggle)
4. Click **Load unpacked**
5. Select the `extension/dist` folder
6. Extension icon appears in toolbar

### Step 3: Configure
1. Click extension icon
2. Enter API URL: `https://your-backend.onrender.com/api/v1`
3. Enter access token (from web app DevTools)
4. Enter workspace ID
5. Click **Connect**

## Getting Your Access Token

1. Log into the web app
2. Open browser DevTools (F12)
3. Go to **Application** tab
4. Expand **Local Storage**
5. Find your Supabase auth token
6. Copy the `access_token` value

## Getting Your Workspace ID

1. Log into the web app
2. Navigate to your workspace
3. Look at the URL: `https://your-app.vercel.app/?workspace=YOUR_WORKSPACE_ID`
4. Copy the workspace ID

## Verification

After installation:
1. Navigate to any LinkedIn profile
2. Click extension icon
3. Should show profile detection or "Not a LinkedIn Profile" for non-profiles
4. For saved profiles, should show quick actions
5. For new profiles, should show save form

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Not a LinkedIn Profile" | Navigate to linkedin.com/in/username |
| Authentication error | Re-enter token from DevTools |
| API connection error | Check backend URL is correct |
| Extension not saving | Verify backend is running |

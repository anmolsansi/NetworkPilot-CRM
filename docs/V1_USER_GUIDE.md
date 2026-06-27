# NetworkPilot CRM - V1 User Guide

## What is NetworkPilot CRM?

NetworkPilot CRM is a personal CRM for tracking LinkedIn outreach follow-ups. It helps you never lose track of who needs follow-up, what stage they're in, and what to say next.

## Quick Start

### 1. Sign Up
1. Go to the web app
2. Click "Sign up"
3. Enter email and password
4. You'll be redirected to the dashboard

### 2. Create a Workspace
1. Click "Create Workspace"
2. Enter a name (e.g., "My Outreach")
3. Your workspace is created with default settings

### 3. Install the Extension
1. Follow the [Extension Installation Guide](EXTENSION_INSTALL.md)
2. Enter your API URL and access token
3. Enter your workspace ID (from the web app URL)

## Daily Workflow

### Morning Check
1. Open the web app dashboard
2. See who needs follow-up today
3. Review overdue contacts

### Browsing LinkedIn
1. Navigate to a LinkedIn profile
2. Click the extension icon
3. If new: Save the profile with initial action
4. If saved: Apply quick action (Accepted, Message Sent, etc.)

### After Sending a Message
1. Go to the profile in the extension
2. Click "Message Sent"
3. Next follow-up is automatically scheduled

### When Someone Replies
1. Go to the profile in the extension
2. Click "Reply Received"
3. Follow-up sequence stops

### End of Day
1. Review dashboard for tomorrow's follow-ups
2. Snooze anyone you want to defer
3. Archive completed contacts

## Features

### Dashboard
- **Due Today**: Contacts requiring action today
- **Overdue**: Contacts past their follow-up date
- **Waiting for Reply**: Contacts you've messaged

### People List
- Search by name, company, or role
- Filter by stage, priority, or status
- Click any row to view details

### Person Detail
- Profile information (role, company, location)
- Activity timeline showing all actions
- Quick action buttons
- Edit profile fields

### Templates
- Pre-made message templates
- Copy with one click
- Variables like {{first_name}} render automatically

### Settings
- Workspace name and timezone
- Default follow-up delays
- Daily calendar reminder link

## Stage Flow

```
Invite Sent → Invite Pending → Accepted → Message Sent
                                              ↓
                                     Waiting for Reply → Replied
                                              ↓
                                     Follow-up 1 → Follow-up 2
```

## Priority Levels
- **A (High)**: Important contacts, follow up quickly
- **B (Medium)**: Standard follow-up cadence
- **C (Low)**: Low priority, longer delays

## Tips

1. **Be consistent**: Check dashboard daily
2. **Use templates**: Save time with reusable messages
3. **Set priorities**: Focus on high-value contacts
4. **Archive completed**: Keep dashboard clean
5. **Use the extension**: Quick actions while browsing LinkedIn

## Support

For issues or questions:
- Check the [Deployment Guide](DEPLOYMENT.md)
- Review the [Extension QA Checklist](EXTENSION_QA.md)
- See the [API Spec](API_SPEC.md) for technical details

## What's Not in V1

V1 intentionally does NOT include:
- Automated LinkedIn messaging
- Automated connection requests
- LinkedIn inbox scraping
- LinkedIn DOM scraping
- Gmail integration
- Google Calendar OAuth
- AI-generated messages
- CSV import/export
- Team features
- Billing

These may be added in future versions.

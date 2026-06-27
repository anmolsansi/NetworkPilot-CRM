# Product Overview

## What is NetworkPilot CRM?

NetworkPilot CRM is a personal CRM for tracking LinkedIn outreach follow-ups. It helps users manually track connections, follow-up stages, and never lose track of who needs attention.

## Core Problem

People send LinkedIn connection requests and messages but lose track of who responded, who needs follow-up, and when. Existing CRMs are too complex for personal use.

## V1 Solution

- Chrome extension to quickly save LinkedIn profiles
- Stage tracking (invite sent → accepted → messaged → replied)
- Dashboard showing who needs follow-up today
- Activity timeline for each person
- Message templates for quick copy
- Daily calendar reminder link

## V1 Rules

1. **Manual only** — No automation of LinkedIn actions
2. **No scraping** — No inbox, search results, or DOM scraping
3. **Manual extension** — User clicks buttons, no content scripts
4. **Backend as source of truth** — All stage transitions go through API

## User Workflow

1. Browse LinkedIn, send connection request manually
2. Click extension, save profile as "invite sent"
3. When accepted, mark as "accepted" in extension
4. Send first message manually, mark "message sent"
5. Dashboard shows follow-up due dates
6. Copy template from extension, paste into LinkedIn
7. Mark follow-ups as sent, track replies
8. Archive or snooze people as needed

## Success Criteria

- User can complete full tracking flow without leaving LinkedIn
- Dashboard accurately shows who needs follow-up today
- Activity timeline preserves full history
- No LinkedIn automation or scraping occurs

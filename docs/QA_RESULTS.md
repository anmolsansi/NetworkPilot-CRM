# V1 QA Results

## v0.0.11-v0.0.23 Release-Gate Audit (2026-07-14)

- Tester: Codex automated local validation
- Environment: macOS arm64, Python 3.11.15, Node 25.8.1, npm 11.11.0, SQLite integration database
- Audited base commit: `2c89dacc5f502b1e3bbca54b5ce3abc91182a4b8`
- Branch: `codex/issue-60-release-acceptance`
- Command: `backend/.venv/bin/pytest app/tests/integration/test_v011_v023_release_boundaries.py -q`
- Result: 21 passed, 5 expected failures
- Full backend suite: `backend/.venv/bin/pytest` — 107 passed, 5 expected failures
- Focused Ruff: passed
- Frontend suite: `frontend/npm test -- --run` — 26 passed
- Frontend production build: passed
- Release status: **Not complete**

The five expected failures are the analytics authorization boundary for v0.0.18, v0.0.19,
v0.0.21, and v0.0.22 (fixed in PR #61), and the invitation authorization boundary for v0.0.23
(fixed in PR #62). Expected failures do not count as acceptance passes. The explicit per-version
matrix and remaining user-workflow gaps are in
`releases/v0.0.11-v0.0.23-COMPLETION.md`.

## Test Environment
- Date: 2026-06-28
- Tester: AI Agent (Automated Smoke/Integration Tests only)
- Commit SHA: `f239d4a931a6b04de3dfe16a395c0a94c09067fc`
- Backend: Passed (`16 passed in 0.44s`)
- Frontend: Passed (`12 passed in 1.20s`)
- Extension: Passed (`12 passed in 249ms`)
- Deployed URLs: N/A (Tested locally)
- Extension Artifact: `dist/` directory generated via `vite build`

## Test Flow

### 1. Authentication
- [ ] Sign up with email/password
- [ ] Log in with credentials
- [ ] Session persists on refresh
- [ ] Logout clears session

### 2. Workspace Setup
- [ ] Create new workspace
- [ ] Workspace appears in list
- [ ] Can update workspace settings
- [ ] Timezone saves correctly

### 3. Extension Setup
- [ ] Install extension as unpacked
- [ ] Configure API URL and token
- [ ] Extension detects LinkedIn profiles
- [ ] Extension shows "Not a LinkedIn Profile" for non-profiles

### 4. Save New Profile
- [ ] Navigate to LinkedIn profile
- [ ] Open extension
- [ ] Fill in name, role, company
- [ ] Set priority (A/B/C)
- [ ] Select initial action (Invite Sent)
- [ ] Save profile
- [ ] Profile appears in web app people list

### 5. Mark Accepted
- [ ] Navigate to saved profile
- [ ] Click "Accepted" in extension
- [ ] Stage updates to "Accepted"
- [ ] Next action shows "Send First Message"

### 6. Send First Message
- [ ] Navigate to profile
- [ ] Click "Message Sent"
- [ ] Stage updates to "Waiting for Reply"
- [ ] Next action shows "Follow-up 1"
- [ ] Due date set based on default delay

### 7. Follow-up Sequence
- [ ] Click "Follow-up 1 Sent"
- [ ] Next action shows "Follow-up 2"
- [ ] Due date updated

### 8. Reply Received
- [ ] Click "Reply Received"
- [ ] Stage updates to "Replied"
- [ ] No more follow-up due

### 9. Dashboard
- [ ] Due today shows correct count
- [ ] Overdue section shows old items
- [ ] Waiting for reply count accurate

### 10. Snooze
- [ ] Snooze person in extension
- [ ] Next action date updates
- [ ] Person moves out of due list

### 11. Archive
- [ ] Archive person in extension
- [ ] Person status changes to archived
- [ ] Person disappears from dashboard

### 12. Templates
- [ ] Default templates created with workspace
- [ ] Can create new template
- [ ] Can edit template
- [ ] Can delete template
- [ ] Copy button works
- [ ] Variables render correctly

### 13. Calendar Link
- [ ] Generate calendar reminder link
- [ ] Link opens Google Calendar
- [ ] Event has correct title and description

### 14. People List
- [ ] Search by name works
- [ ] Filter by stage works
- [ ] Filter by priority works
- [ ] Pagination works

### 15. Person Detail
- [ ] Profile info displays correctly
- [ ] Can edit profile fields
- [ ] Activity timeline shows all actions
- [ ] Quick actions work from detail page

## Issues Found

### Critical (Blocks V1)
| Issue | Description | Status |
|-------|-------------|--------|
| Circular Imports | Backend failed to start due to circular import in workspace_service.py and deps.py | Fixed |
| Test Auth Mock | Tests were hitting real DB without valid mock auth tokens. | Fixed |
| Route Collisions | me router duplicated prefix resulting in /api/v1/me/me | Fixed |
| Missing Env/SQLite | Tests required SQLite engine with JSON array polyfills. | Fixed |

### Important (Should Fix)
| Issue | Description | Status |
|-------|-------------|--------|
| Missing Manifest Icons | Extension build failed due to missing icon files | Fixed |
| TS Compiler Errors | Unused variables in frontend and extension blocking build | Fixed |
| Action Type Match | acceptance_checked was an invalid action type. Fixed to accepted. | Fixed |

### Nice to Have (V2)
| Issue | Description | Status |
|-------|-------------|--------|
| E2E Testing | Needs full playwright tests | Open |

## Sign-off
- [ ] All critical issues resolved
- [ ] Full flow tested end-to-end
- [ ] Ready for V1 launch

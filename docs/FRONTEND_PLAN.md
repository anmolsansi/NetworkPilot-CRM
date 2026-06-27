# Frontend Plan

## Tech Stack

- React 18+ with TypeScript
- Vite for build
- Tailwind CSS for styling
- Zustand for state management
- React Router for navigation
- Supabase JS client for auth

## Pages

### Login Page (`/login`)
- Email/password sign up and in
- Supabase auth
- Redirect to dashboard on success

### Dashboard (`/`)
- Summary cards (due today, overdue, waiting)
- Due follow-up list with quick actions
- Priority filters
- Date selector

### People List (`/people`)
- Searchable table
- Filters: stage, priority, status, due status
- Pagination
- Row click → person detail

### Person Detail (`/people/:id`)
- Profile header (name, role, company, LinkedIn)
- Stage panel
- Next action panel
- Activity timeline
- Quick action buttons
- Profile edit form

### Templates (`/templates`)
- Template list by category
- Create/edit/delete
- Preview with variable rendering
- Copy-to-clipboard

### Settings (`/settings`)
- Workspace name
- Timezone
- Default follow-up delays
- Daily reminder time
- Calendar reminder link

## Components

### Layout
- `AppLayout` — Shell with sidebar + topbar
- `Sidebar` — Navigation links
- `Topbar` — User info, workspace selector

### Common (Ticket 37)
- `Button` — Primary, secondary, danger variants
- `Input` — Text input with label/error
- `Textarea` — Multi-line input
- `Select` — Dropdown select
- `Modal` — Dialog overlay
- `Toast` — Success/error notifications
- `Badge` — Status/priority badges
- `Skeleton` — Loading placeholder
- `ErrorAlert` — Error message display
- `EmptyState` — No data placeholder
- `ConfirmDialog` — Destructive action confirmation

### People
- `DuePersonCard` — Dashboard card for due person
- `QuickActionMenu` — Action buttons for person
- `SnoozeModal` — Snooze date picker
- `ArchiveDialog` — Archive confirmation
- `PeopleFilters` — Filter controls
- `PeopleTable` — People list table
- `PersonTableRow` — Single table row
- `StageBadge` — Stage indicator
- `PriorityBadge` — Priority indicator
- `NextActionBadge` — Next action indicator

### Activities
- `ActivityTimeline` — Activity history list
- `AddActivityForm` — Log new activity

### Templates
- `TemplateList` — Template list
- `TemplateEditor` — Create/edit form
- `TemplatePreview` — Rendered preview
- `TemplateVariablePreview` — Variable substitution
- `TemplateCopyButton` — Copy to clipboard

### Settings
- `WorkspaceSettingsForm` — Workspace settings
- `ReminderSettingsForm` — Reminder config
- `CalendarReminderLinkCard` — Calendar link display

## State Management (Zustand)

```typescript
// Stores
useAuthStore       — User session, login/logout
useWorkspaceStore  — Current workspace, workspace list
useDashboardStore  — Due people, summary counts
usePeopleStore     — People list, filters, pagination
useTemplateStore   — Templates list
```

## API Client

Central `httpClient` that:
- Attaches Supabase access token
- Normalizes errors
- Handles 401 redirect
- Parses JSON responses

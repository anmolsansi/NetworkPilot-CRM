# Database Schema

## Tables

### app_users
Internal user record bootstrapped from Supabase Auth.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| supabase_user_id | uuid | Unique, from Supabase Auth |
| email | text | Not null |
| display_name | text | Nullable |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |
| deleted_at | timestamptz | Nullable, soft delete |

### workspaces
Container for people and settings.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| name | text | Not null |
| owner_id | uuid | FK → app_users.id |
| default_follow_up_delay_days | integer | Default 3 |
| default_acceptance_check_delay_days | integer | Default 1 |
| daily_reminder_time | time | Default 09:00 |
| timezone | text | Default UTC |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |
| deleted_at | timestamptz | Nullable |

### workspace_members
User-workspace membership.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| workspace_id | uuid | FK → workspaces.id |
| user_id | uuid | FK → app_users.id |
| role | text | 'owner' or 'member' |
| created_at | timestamptz | Default now() |
| deleted_at | timestamptz | Nullable |

Unique constraint: (workspace_id, user_id) WHERE deleted_at IS NULL

### people
LinkedIn contacts being tracked.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| workspace_id | uuid | FK → workspaces.id |
| name | text | Not null |
| linkedin_url | text | Normalized URL |
| linkedin_slug | text | Extracted slug |
| role | text | Nullable |
| company | text | Nullable |
| location | text | Nullable |
| priority | text | 'A', 'B', or 'C' |
| stage | text | Current stage |
| status | text | 'active', 'archived' |
| next_action_type | text | What to do next |
| next_action_date | date | When to do it |
| last_action_type | text | Last recorded action |
| last_action_date | date | When last action happened |
| connection_note | text | Nullable |
| notes | text | Nullable |
| tags | text[] | Array of tags |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |
| deleted_at | timestamptz | Nullable |

Indexes: workspace_id, stage, status, priority, next_action_date

### activities
Action history for each person.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| person_id | uuid | FK → people.id |
| workspace_id | uuid | FK → workspaces.id |
| actor_user_id | uuid | FK → app_users.id |
| action_type | text | Not null |
| source | text | 'web_app', 'chrome_extension', 'system' |
| previous_stage | text | Stage before action |
| new_stage | text | Stage after action |
| message | text | Nullable |
| notes | text | Nullable |
| created_at | timestamptz | Default now() |

### message_templates
Reusable message templates.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| workspace_id | uuid | FK → workspaces.id |
| name | text | Not null |
| category | text | 'connection_request', 'first_message', 'follow_up' |
| body | text | Not null |
| variables | text[] | Supported variables |
| is_default | boolean | Default false |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |
| deleted_at | timestamptz | Nullable |

Unique constraint: (workspace_id, name) WHERE deleted_at IS NULL

### user_settings
Per-user preferences.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| user_id | uuid | FK → app_users.id, unique |
| default_workspace_id | uuid | FK → workspaces.id, nullable |
| settings_json | jsonb | Flexible settings |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |

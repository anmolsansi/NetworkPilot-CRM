# Contract Change Record: CCR-004

Contract: `Import Job Centre`

Current shape: Imports are processed synchronously or via simple background tasks without durability, progress reporting, or retry capabilities. The `import_batches` table only records the fact that a batch occurred.

New shape:

## Database Schema

New table: `import_jobs` (replacing/upgrading `import_batches`)
- `id` (UUID, primary key)
- `workspace_id` (UUID, foreign key, index, not null)
- `created_by_user_id` (UUID, foreign key, not null)
- `status` (String: 'pending', 'processing', 'completed', 'failed', not null, default 'pending')
- `file_content` (Text, not null) - Raw CSV data to process.
- `total_rows` (Integer, default 0)
- `processed_rows` (Integer, default 0)
- `error_log` (JSONB, nullable) - Array of row-level errors for download.
- `created_at` (Timestamp, not null)
- `completed_at` (Timestamp, nullable)

## APIs

### POST `/api/v1/imports/people/commit` (Updated)
Instead of processing inline, it inserts a new `import_jobs` row with status `pending` and `file_content` containing the CSV.
Returns `{ "job_id": "uuid", "status": "pending" }`.

### GET `/api/v1/imports`
Returns a list of import jobs for the workspace, ordered by `created_at` descending.
Includes status, progress (`processed_rows` / `total_rows`), and error counts.

### GET `/api/v1/imports/{job_id}`
Returns details for a specific import job.

### POST `/api/v1/imports/{job_id}/retry`
If status is `failed`, resets status to `pending`, `processed_rows` to 0, clears `error_log`, and `completed_at` to null.

## Background Worker

A durable Postgres-backed queue worker `backend/app/worker.py`.
- Runs as a separate process.
- Queries `import_jobs` where `status = 'pending'`.
- Uses `SELECT ... FOR UPDATE SKIP LOCKED` to acquire a job safely in multi-worker environments.
- Updates status to `processing`.
- Parses `file_content`, batches inserts/updates to `people`, and updates `processed_rows` periodically.
- Records any row-level errors in `error_log`.
- On completion, updates status to `completed` or `failed` and sets `completed_at`.

Migration plan: Create `import_jobs`. We can drop `import_batches` or rename it, but since we are iterating rapidly in alpha, we'll create `import_jobs` and deprecate `import_batches`.

Downstream impact:
- Tickets: MAS-4.1 (Worker/DB), MAS-4.2 (API), MAS-4.3 (UI)
- UI affected: `PeopleListPage` will move the import button to a new "Imports" page or slide-over, which lists history and progress.

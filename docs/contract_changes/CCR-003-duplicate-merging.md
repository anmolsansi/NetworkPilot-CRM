# Contract Change Record: CCR-003

Contract: `Duplicate Detection and Merging`

Current shape: The system allows creating people with the same name, although it prevents creating people with the exact same LinkedIn URL within a workspace. However, variations of names or empty LinkedIn URLs can lead to duplicates. There is no way to merge them.

New shape:

## Database Schema

New table: `person_merges`
- `id` (UUID, primary key)
- `workspace_id` (UUID, foreign key to workspaces, index, not null)
- `target_person_id` (UUID, foreign key to people, index, not null) - The person that was kept.
- `source_person_id` (UUID, index, not null) - The person that was soft-deleted. No strict FK constraint to `people` because it might be deleted entirely later, or use soft-delete FK. We'll use a standard UUID column.
- `merged_by_user_id` (UUID, foreign key to app_users, not null)
- `merge_data` (JSONB, nullable) - Snapshots of what was merged (e.g. which fields were taken from source).
- `created_at` (Timestamp, not null)

## APIs

### GET `/api/v1/people/duplicates`
Query: `?workspace_id=<uuid>`
Returns potential duplicates. It looks for people with the exact same `first_name` and `last_name` in the workspace, or exact same `email` (if email exists).
```json
[
  {
    "group_id": "string (e.g. John Doe)",
    "people": [
      { /* Person representation */ },
      { /* Person representation */ }
    ]
  }
]
```

### POST `/api/v1/people/merge`
Query: `?workspace_id=<uuid>`
Request:
```json
{
  "target_person_id": "uuid",
  "source_person_id": "uuid",
  "fields_to_keep_from_source": ["email", "phone"] 
}
```
Validation: 
- `target_person_id` and `source_person_id` must exist, belong to `workspace_id`, and not be deleted.
- They must be different IDs.

Action:
1. Update `target_person_id` with any fields requested from source.
2. Re-assign all `activities` where `person_id == source_person_id` to `target_person_id`.
3. Soft-delete `source_person_id` (`deleted_at = now()`).
4. Record audit trail in `person_merges`.

Returns: `200 OK` with the updated `target_person` object.

Compatibility plan: Fully additive.

Migration plan: Additive Alembic migration.

Downstream impact:
- Tickets: MAS-3.1 (Backend), MAS-3.2 (Frontend).
- UI affected: `PeopleListPage.tsx` or a new `DuplicatesPage.tsx`.

Updated artifacts: [x] architecture plan [ ] affected tickets [x] repo_context.md

# Contract Change Record: CCR-005

Contract: `Custom Tags`

Current shape: People have implicit categorization via `stage` or `priority`, but no arbitrary, user-defined orthogonal categories.

New shape:

## Database Schema

New table: `tags`
- `id` (UUID, primary key)
- `workspace_id` (UUID, foreign key, index)
- `name` (String, not null, unique per workspace)
- `color` (String, nullable) - Hex code or standard color name.

New table: `person_tags` (Join table)
- `person_id` (UUID, foreign key, index)
- `tag_id` (UUID, foreign key, index)
- Primary Key (person_id, tag_id)

## APIs

### GET `/api/v1/tags`
Query params: `workspace_id`
Returns a list of tags for a workspace.

### POST `/api/v1/tags`
Body: `{ workspace_id, name, color }`
Creates a tag.

### DELETE `/api/v1/tags/{tag_id}`
Deletes a tag and all associated `person_tags`.

### Modifications to existing APIs
- `GET /api/v1/people` and `GET /api/v1/people/{id}` will return a list of tags associated with the person.
- `POST /api/v1/people` and `PUT /api/v1/people/{id}` will accept an array of `tag_ids` to associate with the person. The backend will sync `person_tags` to match the given list.

Migration plan: Create `tags` and `person_tags`.

Downstream impact:
- UI affected: `PeopleListPage` (show tags), `PersonFormPage` (multi-select for tags).
- Filtering: Update the `people` list endpoint to allow filtering by `tag_ids`.

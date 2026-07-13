# Contract Change Record: CCR-006

Contract: `POST /api/v1/people/bulk-actions` tag and stage payload compatibility.

Current shape: CCR-001 documents `{tags: string[]}` and `{stage: legacy_stage}`, while merged backend code accepts only `{tag_ids: uuid[]}` and `{stage_id: uuid|null}`. The current frontend still submits string tags.

New shape:
- `add_tags` and `remove_tags` accept exactly one of `{tags: string[1..20]}` or `{tag_ids: uuid[1..20]}`.
- `set_stage` accepts exactly one of `{stage: legacy_stage}` or `{stage_id: uuid|null}`. An explicit null clears the custom stage.
- Tag IDs and custom stage IDs must belong to the request workspace. Cross-workspace or missing IDs return 404 without mutations.
- String tags retain the CCR-001 normalization behavior; `add_tags` creates missing workspace tags and `remove_tags` treats missing names as no-ops.

Reason: preserve the shipped v0.0.1 contract while allowing additive v0.0.5 and v0.0.9 identifiers.

Breaking? no — both historical shapes remain accepted.

Compatibility plan: frontend may migrate from names to IDs without a flag day; both are tested.

Migration plan: none.

Downstream impact:
- Tickets affected: MAS-1.1, MAS-1.2, MAS-5, MAS-9.
- Code affected: People schemas/service, bulk UI, tests, API specification.
- Tickets already merged that must be re-opened: MAS-1.1.

Updated artifacts: [x] architecture plan [x] affected tickets [x] repo context

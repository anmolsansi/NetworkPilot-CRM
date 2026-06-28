# V1 Bug Tracker

## Bug Template
```
### Bug: [Title]
- **Severity**: Critical / Important / Nice to Have
- **Component**: Backend / Frontend / Extension
- **Steps to Reproduce**:
  1. ...
  2. ...
- **Expected**: ...
- **Actual**: ...
- **Status**: Open / In Progress / Fixed
```

## Critical Bugs
### Bug: Pending V1 QA Validation
- **Severity**: Critical
- **Component**: QA / Testing
- **Steps to Reproduce**:
  1. Review `QA_RESULTS.md`.
  2. Notice the checkboxes for manual testing flow are unchecked.
- **Expected**: A human or automated E2E system validates the extension and frontend UI against the real backend.
- **Actual**: Only unit/integration backend smoke tests have run; real V1 QA is incomplete.
- **Status**: Open

## Important Bugs
_No important bugs found yet._

## Nice to Have
_No nice-to-have bugs found yet._

---

## Fixed Bugs
1. **Circular Import**: Fixed circular import between `backend/app/services/workspace_service.py` and `backend/app/api/deps.py`.
2. **Missing Manifest Icons**: Removed `icons` from `extension/manifest.json` which blocked build.
3. **Route Collisions**: Fixed `/api/v1/me/me` duplicated prefix to `/api/v1/me`.
4. **Integration Test Environment**: Refactored `backend/app/tests/integration/conftest.py` to use in-memory SQLite and mock auth dynamically.
5. **Typescript Errors**: Fixed strict unused parameter errors in frontend `LoginPage.test.tsx` and extension `activeTab.ts`.
6. **Action Type**: Fixed invalid `acceptance_checked` action to `accepted` in test payload.
7. **Extension POST Workspace ID Mismatch**: Extension quick-create and quick-action endpoints failed authorization because `workspace_id` was expected as a query parameter but sent in the JSON body. Fixed backend to parse from body and test suite to match extension client.
8. **Doc and Task Status Inconsistency**: Updated `TASKS.md`, `QA_RESULTS.md`, and `API_SPEC.md` to accurately reflect the implemented state, resolving the mismatch between the project documents and the actual codebase.

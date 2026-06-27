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
_No critical bugs found yet._

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

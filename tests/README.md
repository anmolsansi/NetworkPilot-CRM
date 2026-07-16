# NetworkPilot browser tests

The Playwright suite starts the local frontend and intercepts `/api/v1` with a
stateful test API. Authentication uses a synthetic `@networkpilot.test` user and
non-production tokens defined in `fixtures/networkpilot.ts`; no repository or
GitHub secret is required.

Run the suite from the repository root:

```bash
npx playwright test
```

Set `E2E_BASE_URL` to point the same controlled suite at an already-running
frontend. The API remains intercepted so tests cannot mutate production data.
Traces, screenshots, and video are retained only for failures.

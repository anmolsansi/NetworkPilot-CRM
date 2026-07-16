import { expect, test as base, type Page, type Route } from '@playwright/test';

export const TEST_USER_ID = '10000000-0000-4000-8000-000000000001';
export const TEST_WORKSPACE_ID = '20000000-0000-4000-8000-000000000001';
export const TEST_PERSON_ID = '30000000-0000-4000-8000-000000000001';

const testSession = {
  access_token: 'networkpilot-e2e-token',
  refresh_token: 'networkpilot-e2e-refresh',
  token_type: 'bearer',
  expires_in: 3600,
  expires_at: 4_102_444_800,
  user: {
    id: TEST_USER_ID,
    email: 'e2e-owner@networkpilot.test',
    aud: 'authenticated',
    role: 'authenticated',
    app_metadata: { provider: 'e2e' },
    user_metadata: { name: 'NetworkPilot E2E Owner' },
    created_at: '2026-01-01T00:00:00.000Z',
  },
};

export const test = base.extend({
  context: async ({ context }, use) => {
    await context.addInitScript((session) => {
      localStorage.setItem('sb-localhost-auth-token', JSON.stringify(session));
    }, testSession);
    await use(context);
  },
});

export { expect };

type ApiOptions = { emptyWorkspace?: boolean };

export interface MockApi {
  requests: Array<{ method: string; path: string; authorization: string | null; body: unknown }>;
}

const workspace = {
  id: TEST_WORKSPACE_ID,
  name: 'E2E Workspace',
  owner_id: TEST_USER_ID,
  default_follow_up_delay_days: 3,
  default_acceptance_check_delay_days: 7,
  daily_reminder_time: '09:00',
  timezone: 'UTC',
  quiet_hours_start: null,
  quiet_hours_end: null,
  email_reminders_enabled: false,
  daily_digest_enabled: false,
  overdue_alerts_enabled: true,
};

const person = {
  id: TEST_PERSON_ID,
  name: 'Ada Lovelace',
  first_name: 'Ada',
  last_name: 'Lovelace',
  linkedin_url: 'https://www.linkedin.com/in/ada-lovelace',
  role: 'Staff Engineer',
  company: 'Analytical Engines',
  location: 'London',
  email: 'ada@example.test',
  phone_number: null,
  premium: false,
  company_website: null,
  processed_at: '2026-07-14T00:00:00Z',
  processed_at_millis: null,
  invite_accepted_at: null,
  invite_accepted_at_millis: null,
  is_favorite: false,
  favorite_notes: null,
  notes: '',
  stage: 'saved',
  stage_id: null,
  pipeline_stage: null,
  priority: 'B',
  status: 'active',
  next_action_type: null,
  next_action_date: null,
  tags: [],
  custom_fields_data: {},
  manual_warmth: null,
  calculated_freshness: 100,
  last_engaged_at: null,
};

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

export async function installMockApi(page: Page, options: ApiOptions = {}): Promise<MockApi> {
  const state = {
    workspaces: options.emptyWorkspace ? [] : [{ ...workspace }],
    people: [{ ...person }],
    activities: [] as Record<string, unknown>[],
    imports: [] as Record<string, unknown>[],
    invites: [] as Record<string, unknown>[],
  };
  const requests: MockApi['requests'] = [];

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace('/api/v1', '');
    const method = request.method();
    let body: unknown = null;
    if (request.postData() && request.headers()['content-type']?.includes('application/json')) {
      body = request.postDataJSON();
    }
    requests.push({ method, path, authorization: request.headers().authorization || null, body });

    if (path === '/workspaces' && method === 'GET') return json(route, state.workspaces);
    if (path === '/workspaces' && method === 'POST') {
      const created = { ...workspace, name: (body as { name: string }).name };
      state.workspaces = [created];
      return json(route, created, 201);
    }
    if (path.endsWith('/members/me')) return json(route, { dashboard_config: {} });
    if (path === '/dashboard/summary') {
      return json(route, {
        due_today: 0,
        overdue: 0,
        waiting_for_reply: 0,
        active_total: state.people.length,
      });
    }
    if (path === '/dashboard/due' || path === '/dashboard/tags') return json(route, []);
    if (
      path === '/tags' ||
      path === '/pipeline-stages/' ||
      path === '/custom-fields/' ||
      path === '/saved-views'
    ) {
      return json(route, []);
    }

    if (path === '/people' && method === 'GET') {
      return json(route, { items: state.people, total: state.people.length, page: 1, limit: 20 });
    }
    if (path === '/people' && method === 'POST') {
      const created = { ...person, ...(body as object), id: TEST_PERSON_ID };
      state.people = [created];
      return json(route, created, 201);
    }
    if (path === `/people/${TEST_PERSON_ID}` && method === 'GET')
      return json(route, state.people[0]);
    if (path === `/people/${TEST_PERSON_ID}` && method === 'PATCH') {
      state.people[0] = { ...state.people[0], ...(body as object) };
      return json(route, state.people[0]);
    }
    if (path === `/people/${TEST_PERSON_ID}` && method === 'DELETE') {
      return route.fulfill({ status: 204 });
    }
    if (path === `/people/${TEST_PERSON_ID}/restore`) return json(route, state.people[0]);

    if (path === `/people/${TEST_PERSON_ID}/activities` && method === 'GET') {
      return json(route, state.activities);
    }
    if (path === `/people/${TEST_PERSON_ID}/activities` && method === 'POST') {
      const activity = {
        id: '40000000-0000-4000-8000-000000000001',
        person_id: TEST_PERSON_ID,
        actor_user_id: TEST_USER_ID,
        created_at: '2026-07-14T00:00:00Z',
        ...(body as object),
      };
      state.activities.unshift(activity);
      return json(route, activity, 201);
    }

    if (path === '/imports' && method === 'GET') return json(route, state.imports);
    if (path === '/imports/people/commit' && method === 'POST') {
      const job = {
        id: '50000000-0000-4000-8000-000000000001',
        status: 'completed',
        filename: 'people.csv',
        total_rows: 1,
        processed_rows: 1,
        created_count: 1,
        updated_count: 0,
        failed_count: 0,
        created_at: '2026-07-14T00:00:00Z',
      };
      state.imports = [job];
      return json(route, job, 202);
    }

    if (path.endsWith('/analytics/funnel')) {
      return json(route, { stages: [{ stage: 'saved', count: 1, conversion_rate: 100 }] });
    }
    if (path.endsWith('/analytics/performance')) return json(route, []);
    if (path.endsWith('/analytics/goals')) {
      return json(route, { target: 10, current: 1, percentage: 10, week_start: '2026-07-13' });
    }
    if (path.endsWith('/analytics/export')) {
      return route.fulfill({
        status: 200,
        contentType: 'text/csv',
        body: 'stage,count\nsaved,1\n',
      });
    }

    if (path.endsWith('/invites') && method === 'GET') return json(route, state.invites);
    if (path.endsWith('/invites') && method === 'POST') {
      const invite = {
        id: '60000000-0000-4000-8000-000000000001',
        email: (body as { email: string }).email,
        role: (body as { role: string }).role,
        status: 'pending',
        expires_at: '2026-07-21T00:00:00Z',
      };
      state.invites = [invite];
      return json(route, invite, 201);
    }
    if (path.includes('/invites/') && method === 'DELETE') return route.fulfill({ status: 204 });
    if (path === '/invites/accept' && method === 'POST') {
      return json(route, {
        workspace_id: TEST_WORKSPACE_ID,
        user_id: TEST_USER_ID,
        role: 'member',
      });
    }

    if (path === '/tasks' && method === 'POST') {
      return json(route, { id: '70000000-0000-4000-8000-000000000001', ...(body as object) }, 201);
    }
    if (path === '/tasks' && method === 'GET')
      return json(route, { items: [], total: 0, page: 1, limit: 50 });

    return json(
      route,
      { error: { code: 'UNMOCKED_E2E_ROUTE', message: `${method} ${path}` } },
      501
    );
  });

  return { requests };
}

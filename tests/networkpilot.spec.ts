import {
  expect,
  installMockApi,
  test,
  TEST_PERSON_ID,
  TEST_USER_ID,
  TEST_WORKSPACE_ID,
} from './fixtures/networkpilot';

test('creates the first workspace in an authenticated session', async ({ page }) => {
  const api = await installMockApi(page, { emptyWorkspace: true });
  await page.goto('/');

  await page.getByLabel('Workspace name').fill('Recruiting Team');
  await page.getByRole('button', { name: 'Create workspace' }).click();

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  expect(api.requests).toContainEqual(
    expect.objectContaining({ method: 'POST', path: '/workspaces' })
  );
});

test('creates, updates, and removes a person', async ({ page }) => {
  const api = await installMockApi(page);
  await page.goto('/people/new');

  await page.getByLabel('Name').fill('Ada Lovelace');
  await page.getByLabel('LinkedIn URL').fill('https://linkedin.com/in/ada-lovelace');
  await page.getByRole('button', { name: 'Add Person' }).click();
  await expect(page).toHaveURL(new RegExp(`/people/${TEST_PERSON_ID}$`));

  await page.getByRole('button', { name: 'Edit' }).click();
  await page.getByLabel('Name').fill('Ada Byron');
  await page.getByRole('button', { name: 'Save' }).click();
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Move to Trash' }).click();
  await expect(page.getByRole('button', { name: 'Undo' })).toBeVisible();

  expect(api.requests).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ method: 'POST', path: '/people' }),
      expect.objectContaining({ method: 'PATCH', path: `/people/${TEST_PERSON_ID}` }),
      expect.objectContaining({ method: 'DELETE', path: `/people/${TEST_PERSON_ID}` }),
    ])
  );
});

test('imports a CSV and records timeline activity', async ({ page }) => {
  const api = await installMockApi(page);
  await page.goto('/imports');
  await page.locator('input[type=file]').setInputFiles({
    name: 'people.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('name,linkedin_url\nGrace Hopper,https://linkedin.com/in/grace-hopper\n'),
  });
  await expect
    .poll(() => api.requests.some((request) => request.path === '/imports/people/commit'))
    .toBe(true);

  await page.goto(`/people/${TEST_PERSON_ID}`);
  await page
    .getByPlaceholder('Add a note to this action (optional)')
    .fill('Discussed platform roadmap');
  await page.getByRole('button', { name: 'Message Sent' }).click();
  await expect
    .poll(() =>
      api.requests.some(
        (request) => request.path.endsWith('/activities') && request.method === 'POST'
      )
    )
    .toBe(true);
});

test('loads analytics and downloads a report', async ({ page }) => {
  const api = await installMockApi(page);
  await page.goto('/analytics');

  await expect(page.getByRole('heading', { name: 'Analytics' })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export Report (CSV)' }).click();
  await download;

  expect(api.requests).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ path: `/workspaces/${TEST_WORKSPACE_ID}/analytics/funnel` }),
      expect.objectContaining({ path: `/workspaces/${TEST_WORKSPACE_ID}/analytics/export` }),
    ])
  );
});

test('sends an invitation and exercises authenticated task ownership and acceptance contracts', async ({
  page,
}) => {
  const api = await installMockApi(page);
  await page.goto('/settings');

  await page.getByLabel('Email Address').fill('member@networkpilot.test');
  await page.getByRole('button', { name: 'Send Invite' }).click();
  await expect(page.getByText('member@networkpilot.test')).toBeVisible();

  const contracts = await page.evaluate(
    async ({ workspaceId, personId, userId }) => {
      const session = JSON.parse(localStorage.getItem('sb-localhost-auth-token') || '{}');
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`,
      };
      const task = await fetch(`/api/v1/tasks?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ person_id: personId, title: 'Follow up', assigned_to: userId }),
      });
      const acceptance = await fetch('/api/v1/invites/accept', {
        method: 'POST',
        headers,
        body: JSON.stringify({ token: 'e2e-invite-token' }),
      });
      return { taskStatus: task.status, acceptanceStatus: acceptance.status };
    },
    { workspaceId: TEST_WORKSPACE_ID, personId: TEST_PERSON_ID, userId: TEST_USER_ID }
  );

  expect(contracts).toEqual({ taskStatus: 201, acceptanceStatus: 200 });
  expect(
    api.requests.filter((request) => ['/tasks', '/invites/accept'].includes(request.path))
  ).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ authorization: 'Bearer networkpilot-e2e-token' }),
    ])
  );
});

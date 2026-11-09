import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AppRoutes } from './App'

const STUDENT = { email: 'asha@iitgn.ac.in', name: 'Asha', is_admin: false, unread_notifications: 0 }

/** Fake the Django API: `me` is the logged-in user, or null for a logged-out visitor. */
function fakeApi(me: object | null) {
  const calls: string[] = []
  vi.stubGlobal('fetch', async (url: string) => {
    calls.push(url)
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/me') return me ? json(me) : json({ detail: 'Not logged in.' }, 401)
    if (url === '/api/auth/config') return json({ google_client_id: '', dev_login: true })
    return json([])
  })
  return calls
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('S23: logged-out visitors only see the login page', () => {
  it.each(['/', '/reports', '/claims', '/notifications', '/admin', '/admin/items/1'])(
    'sends %s to the login page',
    async (path) => {
      const calls = fakeApi(null)
      renderAt(path)
      expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeTruthy()
      expect(calls.filter((url) => !url.startsWith('/api/auth/'))).toEqual([])
    },
  )
})

it('logging out does not send the next person to the previous page', async () => {
  let me: object | null = { ...STUDENT, email: 'guard@iitgn.ac.in', is_admin: true }
  vi.stubGlobal('fetch', async (url: string) => {
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/logout') me = null
    if (url === '/api/auth/dev-login') me = STUDENT
    if (url === '/api/auth/me') return me ? json(me) : json({ detail: 'Not logged in.' }, 401)
    if (url === '/api/auth/config') return json({ google_client_id: '', dev_login: true })
    if (url === '/api/auth/logout') return new Response(null, { status: 204 })
    return json(url === '/api/auth/dev-login' ? me : [])
  })
  renderAt('/admin/handovers')
  fireEvent.click(await screen.findByText('Log out'))
  fireEvent.change(await screen.findByLabelText('IITGN email'), { target: { value: STUDENT.email } })
  fireEvent.click(screen.getByText('Dev login'))
  expect(await screen.findByRole('heading', { name: 'How IITGN Lost & Found works' })).toBeTruthy()
  expect(screen.queryByText('403 · Not allowed')).toBeNull()
})

describe('S3: students get 403 on every admin page', () => {
  it.each(['/admin', '/admin/items/new', '/admin/items/1', '/admin/handovers', '/admin/admins'])('shows 403 on %s', async (path) => {
    const calls = fakeApi(STUDENT)
    renderAt(path)
    expect(await screen.findByText('403 · Not allowed')).toBeTruthy()
    expect(calls.filter((url) => url.startsWith('/api/admin/'))).toEqual([])
  })
})

describe('S24: the login page offers student and admin sign-in', () => {
  it('shows both options and sends the chosen role', async () => {
    const bodies: unknown[] = []
    vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
      const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
      if (url === '/api/auth/me') return json({ detail: 'Not logged in.' }, 401)
      if (url === '/api/auth/config') return json({ google_client_id: '', dev_login: true })
      if (url === '/api/auth/dev-login') {
        bodies.push(JSON.parse(String(init?.body)))
        return json({ detail: 'This account is not a security office admin.' }, 403)
      }
      return json([])
    })
    renderAt('/login')
    expect(await screen.findByRole('tab', { name: 'Sign in as student' })).toBeTruthy()
    fireEvent.click(screen.getByRole('tab', { name: 'Sign in as admin' }))
    fireEvent.change(screen.getByLabelText('IITGN email'), { target: { value: 'asha@iitgn.ac.in' } })
    fireEvent.click(screen.getByText('Dev login'))
    expect(await screen.findByText('This account is not a security office admin.')).toBeTruthy()
    expect(bodies).toEqual([{ email: 'asha@iitgn.ac.in', role: 'admin' }])
  })
})

describe('guide comes first', () => {
  it('opens the guide first, with the student steps', async () => {
    fakeApi(STUDENT)
    renderAt('/')
    expect(await screen.findByRole('heading', { name: 'How IITGN Lost & Found works' })).toBeTruthy()
    expect(screen.getByText('File a lost report', { selector: 'strong' })).toBeTruthy()
    expect(screen.getAllByRole('link')[1].textContent).toBe('Guide')
  })

  it('shows guards the security office steps', async () => {
    fakeApi({ ...STUDENT, email: 'guard@iitgn.ac.in', is_admin: true })
    renderAt('/guide')
    expect(await screen.findByText('For the security office')).toBeTruthy()
    expect(screen.getByText('Check the person, then approve')).toBeTruthy()
  })
})

const SAVED_REPORT = {
  id: 7,
  category: 'Bag',
  title: 'Blue bag',
  date_lost: '2026-10-05',
  place_lost: 'Mess',
  private_details: 'Name tag',
  created_at: '2026-10-05T10:00:00Z',
  status: 'OPEN',
  closed_at: null,
  item: null,
  matches: [],
  security_contact: 'Security Office, Main Gate',
}

it('S32: files a lost report only once however often the button is clicked', async () => {
  let posts = 0
  vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/me') return json(STUDENT)
    if (url === '/api/reports' && init?.method === 'POST') {
      posts += 1
      return json({ id: 7 }, 201)
    }
    // After saving, the app opens the new report: answer like the real server does.
    if (url === '/api/reports/7') return json(SAVED_REPORT)
    return json([])
  })
  renderAt('/reports/new')
  const button = await screen.findByText('File report')
  const form = button.closest('form')!
  fireEvent.submit(form)
  fireEvent.submit(form)
  fireEvent.submit(form)
  // Wait until the saved report's page has fully loaded, so nothing is left running.
  expect(await screen.findByRole('heading', { name: /Blue bag/ })).toBeTruthy()
  expect(posts).toBe(1)
})

it('S6: students see every found item with where it was found and who to contact', async () => {
  vi.stubGlobal('fetch', async (url: string) => {
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/me') return json(STUDENT)
    if (url === '/api/items')
      return json({
        items: [
          { id: 1, category: 'Bottle', title: 'Steel bottle', date_found: '2026-10-09', general_area: 'Mess', contact: 'guard@iitgn.ac.in' },
        ],
        security_contact: 'Security Office, Main Gate',
      })
    return json([])
  })
  renderAt('/found')
  expect(await screen.findByText('Steel bottle')).toBeTruthy()
  expect(screen.getByText('Mess')).toBeTruthy()
  expect(screen.getByText('guard@iitgn.ac.in')).toBeTruthy()
  expect(screen.getByRole('link', { name: 'Found items' })).toBeTruthy()
})

it('S17: after approving someone, the guard is told their pickup code was emailed to them', async () => {
  const ADMIN = { ...STUDENT, email: 'guard@iitgn.ac.in', is_admin: true }
  const detail = {
    item: {
      id: 1, category: 'Bag', title: 'Blue bag', date_found: '2026-10-06', general_area: 'Mess',
      exact_location: 'Counter', description: 'Zip pocket', has_photo: false, status: 'AVAILABLE',
      added_by: 'guard@iitgn.ac.in', created_at: '2026-10-06T10:00:00Z',
    },
    claims: [], awaiting_pickup_by: null, handover: null, candidates: [],
  }
  vi.stubGlobal('fetch', async (url: string) => {
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/me') return json(ADMIN)
    if (url === '/api/admin/items/1/approve') return new Response(null, { status: 204 })
    if (url === '/api/admin/items/1') return json(detail)
    return json([])
  })
  renderAt('/admin/items/1')
  fireEvent.change(await screen.findByLabelText('Email to approve'), { target: { value: 'Walk.In@iitgn.ac.in' } })
  fireEvent.click(screen.getByText('Approve'))
  expect(await screen.findByText(/We emailed walk.in@iitgn.ac.in their pickup code/)).toBeTruthy()
})

it('S16: a refused approval is explained right under the Approve box', async () => {
  const ADMIN = { ...STUDENT, email: 'guard@iitgn.ac.in', is_admin: true }
  const detail = {
    item: {
      id: 1, category: 'Bag', title: 'Blue bag', date_found: '2026-10-06', general_area: 'Mess',
      exact_location: 'Counter', description: 'Zip pocket', has_photo: false, status: 'AVAILABLE',
      added_by: 'guard@iitgn.ac.in', created_at: '2026-10-06T10:00:00Z',
    },
    claims: [], awaiting_pickup_by: null, handover: null, candidates: [],
  }
  vi.stubGlobal('fetch', async (url: string) => {
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/me') return json(ADMIN)
    if (url === '/api/admin/items/1/approve') return json({ detail: 'Security office accounts cannot collect items.' }, 400)
    if (url === '/api/admin/items/1') return json(detail)
    return json([])
  })
  renderAt('/admin/items/1')
  fireEvent.change(await screen.findByLabelText('Email to approve'), { target: { value: 'amisha@iitgn.ac.in' } })
  fireEvent.click(screen.getByText('Approve'))
  expect(await screen.findByText('Not approved: Security office accounts cannot collect items.')).toBeTruthy()
})

it('S1: the sign-in page offers Google sign-in only, with no password or code forms', async () => {
  vi.stubGlobal('fetch', async (url: string) => {
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
    if (url === '/api/auth/me') return json({ detail: 'Not logged in.' }, 401)
    if (url === '/api/auth/config') return json({ google_client_id: 'test-client', dev_login: false })
    return json([])
  })
  renderAt('/login')
  expect(await screen.findByText(/Google account/)).toBeTruthy()
  expect(screen.queryByLabelText('Password')).toBeNull()
  expect(screen.queryByText('Forgot password?')).toBeNull()
  expect(screen.queryByText(/Create a password/)).toBeNull()
})

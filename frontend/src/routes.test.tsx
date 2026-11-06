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
      expect(await screen.findByText(/Log in or sign up/)).toBeTruthy()
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
  fireEvent.click(screen.getByText('Log in'))
  expect(await screen.findByRole('heading', { name: 'Found items' })).toBeTruthy()
  expect(screen.queryByText('403 · Not allowed')).toBeNull()
})

describe('S3: students get 403 on every admin page', () => {
  it.each(['/admin', '/admin/items/new', '/admin/items/1', '/admin/handovers'])('shows 403 on %s', async (path) => {
    const calls = fakeApi(STUDENT)
    renderAt(path)
    expect(await screen.findByText('403 · Not allowed')).toBeTruthy()
    expect(calls.filter((url) => url.startsWith('/api/admin/'))).toEqual([])
  })
})

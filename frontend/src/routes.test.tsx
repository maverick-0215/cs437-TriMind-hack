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

describe('S29, S30: password sign-in and forgot password', () => {
  it('signs in with email and password, and resets a forgotten password with an emailed code', async () => {
    const calls: [string, unknown][] = []
    vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
      const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
      if (init?.body) calls.push([url, JSON.parse(String(init.body))])
      if (url === '/api/auth/me') return json({ detail: 'Not logged in.' }, 401)
      if (url === '/api/auth/config') return json({ google_client_id: '', dev_login: false })
      if (url === '/api/auth/login') return json({ detail: 'Wrong email or password.' }, 400)
      if (url === '/api/auth/password/code') return json({ detail: 'We sent a 6-digit code to asha@iitgn.ac.in.' })
      if (url === '/api/auth/password/reset') return json({ detail: 'Password set. You can sign in now.' })
      return json([])
    })
    renderAt('/login')
    fireEvent.change(await screen.findByLabelText('Email'), { target: { value: 'asha@iitgn.ac.in' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByText('Sign in as student', { selector: 'form button' }))
    expect(await screen.findByText('Wrong email or password.')).toBeTruthy()

    fireEvent.click(screen.getByText('Forgot password?'))
    fireEvent.click(screen.getByText('Send code'))
    expect(await screen.findByText(/We sent a 6-digit code/)).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Code from your email'), { target: { value: '123456' } })
    fireEvent.change(screen.getByLabelText(/^New password/), { target: { value: 'lantern-violet-42' } })
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'lantern-violet-42' } })
    fireEvent.click(screen.getByText('Set password'))
    expect(await screen.findByText('Password set. You can sign in now.')).toBeTruthy()
    expect(calls).toEqual([
      ['/api/auth/login', { email: 'asha@iitgn.ac.in', password: 'wrong', role: 'student' }],
      ['/api/auth/password/code', { email: 'asha@iitgn.ac.in' }],
      ['/api/auth/password/reset', { email: 'asha@iitgn.ac.in', code: '123456', password: 'lantern-violet-42' }],
    ])
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

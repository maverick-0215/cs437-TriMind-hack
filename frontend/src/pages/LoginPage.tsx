import { useCallback, useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router'
import { api, useApi } from '../api'
import { useAuth } from '../auth'
import GoogleButton from '../GoogleButton'

type AuthConfig = { google_client_id: string; dev_login: boolean }
type Role = 'student' | 'admin'

const ROLES: { role: Role; label: string }[] = [
  { role: 'student', label: 'Sign in as student' },
  { role: 'admin', label: 'Sign in as admin' },
]

/** S1: sign-in is with an IITGN Google account only; the app has no passwords. */
export default function LoginPage() {
  const { user, loading, refresh } = useAuth()
  const location = useLocation()
  const { data: config, error: configError } = useApi<AuthConfig>('auth/config')
  const [role, setRole] = useState<Role>('student')
  const [devEmail, setDevEmail] = useState('')
  const [error, setError] = useState<string | null>(null)

  const logIn = useCallback(
    async (path: string, body: object) => {
      setError(null)
      try {
        // S24: the backend checks the chosen role against the admin list.
        await api(path, { method: 'POST', body: { ...body, role } })
        await refresh()
      } catch (e) {
        setError((e as Error).message)
      }
    },
    [refresh, role],
  )

  const onGoogleCredential = useCallback((credential: string) => logIn('auth/google', { credential }), [logIn])

  function onDevLogin(event: FormEvent) {
    event.preventDefault()
    logIn('auth/dev-login', { email: devEmail })
  }

  function pick(next: Role) {
    setRole(next)
    setError(null)
  }

  if (loading) return null
  if (user) {
    // Back to the page that sent them here, if any. Otherwise the guide comes first.
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={from ?? '/guide'} replace />
  }

  return (
    <main className="login">
      <div className="card login-card">
        <div className="login-head">
          <p className="login-org">IIT Gandhinagar</p>
          <h1>Lost &amp; Found</h1>
        </div>
        <h2 className="login-title">Sign in</h2>
        <p className="muted">
          Use your <strong>@iitgn.ac.in</strong> Google account.
        </p>

        <div className="role-tabs" role="tablist">
          {ROLES.map((r) => (
            <button
              key={r.role}
              type="button"
              role="tab"
              aria-selected={role === r.role}
              className={role === r.role ? 'active' : 'secondary'}
              onClick={() => pick(r.role)}
            >
              {r.label}
            </button>
          ))}
        </div>

        {configError && <p className="error">{configError}</p>}
        {config?.google_client_id && (
          <div className="login-alt">
            <GoogleButton key={role} clientId={config.google_client_id} onCredential={onGoogleCredential} />
          </div>
        )}
        {config && !config.google_client_id && !config.dev_login && (
          <p className="error">Google sign-in is not set up yet. Add GOOGLE_CLIENT_ID to backend/.env.</p>
        )}

        {config?.dev_login && (
          <form className="stack dev-login" onSubmit={onDevLogin}>
            <p className="tag">Development login: no Google check</p>
            <label>
              IITGN email
              <input type="email" required value={devEmail} onChange={(e) => setDevEmail(e.target.value)} />
            </label>
            <button>Dev login</button>
          </form>
        )}

        {error && <p className="error">{error}</p>}
      </div>
      <p className="login-note">Run by the Security Office, IIT Gandhinagar</p>
    </main>
  )
}

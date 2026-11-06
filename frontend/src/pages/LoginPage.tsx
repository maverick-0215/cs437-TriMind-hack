import { useCallback, useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router'
import { api, useApi } from '../api'
import { useAuth } from '../auth'
import GoogleButton from '../GoogleButton'

type AuthConfig = { google_client_id: string; dev_login: boolean }

export default function LoginPage() {
  const { user, loading, refresh } = useAuth()
  const location = useLocation()
  const { data: config, error: configError } = useApi<AuthConfig>('auth/config')
  const [error, setError] = useState<string | null>(null)
  const [devEmail, setDevEmail] = useState('')

  const logIn = useCallback(
    async (path: string, body: object) => {
      setError(null)
      try {
        await api(path, { method: 'POST', body })
        await refresh()
      } catch (e) {
        setError((e as Error).message)
      }
    },
    [refresh],
  )

  const onGoogleCredential = useCallback((credential: string) => logIn('auth/google', { credential }), [logIn])

  function onDevLogin(event: FormEvent) {
    event.preventDefault()
    logIn('auth/dev-login', { email: devEmail })
  }

  if (loading) return null
  if (user) {
    // Back to the page that sent them here, if any.
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={from ?? (user.is_admin ? '/admin' : '/')} replace />
  }

  return (
    <main className="login">
      <div className="card login-card">
        <h1>IITGN Lost &amp; Found</h1>
        <p className="muted">
          Log in or sign up with your <strong>@iitgn.ac.in</strong> Google account to see found items, report something
          you lost, or claim an item.
        </p>

        {configError && <p className="error">{configError}</p>}
        {config?.google_client_id && <GoogleButton clientId={config.google_client_id} onCredential={onGoogleCredential} />}
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
            <button>Log in</button>
          </form>
        )}

        {error && <p className="error">{error}</p>}
      </div>
    </main>
  )
}

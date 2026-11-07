import { useCallback, useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router'
import { api, useApi } from '../api'
import { useAuth } from '../auth'
import GoogleButton from '../GoogleButton'

type AuthConfig = { google_client_id: string; dev_login: boolean }
type Role = 'student' | 'admin'
/** signin: email + password. code: ask for an emailed code, then set a new password (S30). */
type Mode = 'signin' | 'code'

const ROLES: { role: Role; label: string }[] = [
  { role: 'student', label: 'Sign in as student' },
  { role: 'admin', label: 'Sign in as admin' },
]

export default function LoginPage() {
  const { user, loading, refresh } = useAuth()
  const location = useLocation()
  const { data: config, error: configError } = useApi<AuthConfig>('auth/config')
  const [role, setRole] = useState<Role>('student')
  const [mode, setMode] = useState<Mode>('signin')
  const [codeTitle, setCodeTitle] = useState('Reset your password')
  const [codeSent, setCodeSent] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [devEmail, setDevEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)

  const logIn = useCallback(
    async (path: string, body: object) => {
      setError(null)
      setInfo(null)
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

  function onSignIn(event: FormEvent) {
    event.preventDefault()
    logIn('auth/login', { email, password })
  }

  function onDevLogin(event: FormEvent) {
    event.preventDefault()
    logIn('auth/dev-login', { email: devEmail })
  }

  function openCodeForm(title: string) {
    setMode('code')
    setCodeTitle(title)
    setCodeSent(false)
    setCode('')
    setNewPassword('')
    setConfirm('')
    setError(null)
    setInfo(null)
  }

  function backToSignIn(message: string | null = null) {
    setMode('signin')
    setPassword('')
    setError(null)
    setInfo(message)
  }

  async function onSendCode(event?: FormEvent) {
    event?.preventDefault()
    setError(null)
    try {
      const result = await api<{ detail: string }>('auth/password/code', { method: 'POST', body: { email } })
      setCodeSent(true)
      setInfo(result.detail)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function onSetPassword(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (newPassword !== confirm) {
      setError('The two passwords do not match.')
      return
    }
    try {
      const result = await api<{ detail: string }>('auth/password/reset', {
        method: 'POST',
        body: { email, code, password: newPassword },
      })
      backToSignIn(result.detail)
    } catch (e) {
      setError((e as Error).message)
    }
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

  const current = ROLES.find((r) => r.role === role)!

  return (
    <main className="login">
      <div className="card login-card">
        <div className="login-head">
          <p className="login-org">IIT Gandhinagar</p>
          <h1>Lost &amp; Found</h1>
        </div>
        <h2 className="login-title">Sign in</h2>
        <p className="muted">
          Use your <strong>@iitgn.ac.in</strong> account.
        </p>

        {mode === 'signin' ? (
          <>
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

            {/* S29: email and password. */}
            <form className="stack" onSubmit={onSignIn}>
              <label>
                Email
                <input
                  type="email"
                  required
                  autoComplete="username"
                  placeholder="name@iitgn.ac.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              <button>{current.label}</button>
            </form>
            <p className="login-links">
              <button type="button" className="link" onClick={() => openCodeForm('Reset your password')}>
                Forgot password?
              </button>
              <button type="button" className="link" onClick={() => openCodeForm('Create a password')}>
                New here? Create a password
              </button>
            </p>

            {configError && <p className="error">{configError}</p>}
            {config?.google_client_id && (
              <div className="login-alt">
                <p className="muted">or</p>
                <GoogleButton key={role} clientId={config.google_client_id} onCredential={onGoogleCredential} />
              </div>
            )}

            {config?.dev_login && (
              <form className="stack dev-login" onSubmit={onDevLogin}>
                <p className="tag">Development login: no password check</p>
                <label>
                  IITGN email
                  <input type="email" required value={devEmail} onChange={(e) => setDevEmail(e.target.value)} />
                </label>
                <button>Dev login</button>
              </form>
            )}
          </>
        ) : (
          <>
            {/* S30: a random code is emailed; entering it lets them set a password. */}
            <h2>{codeTitle}</h2>
            {!codeSent ? (
              <form className="stack" onSubmit={onSendCode}>
                <p className="muted">We'll email a 6-digit code to your IITGN address.</p>
                <label>
                  Email
                  <input
                    type="email"
                    required
                    autoComplete="username"
                    placeholder="name@iitgn.ac.in"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
                <button>Send code</button>
              </form>
            ) : (
              <form className="stack" onSubmit={onSetPassword}>
                <label>
                  Code from your email
                  <input
                    required
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    autoComplete="one-time-code"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                </label>
                <label>
                  New password
                  <small className="muted">At least 8 characters, not too common, not only numbers.</small>
                  <input
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </label>
                <label>
                  Confirm new password
                  <input
                    type="password"
                    required
                    autoComplete="new-password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                  />
                </label>
                <button>Set password</button>
                <button type="button" className="link" onClick={() => onSendCode()}>
                  Didn't get it? Send a new code
                </button>
              </form>
            )}
            <p className="login-links">
              <button type="button" className="link" onClick={() => backToSignIn()}>
                Back to sign in
              </button>
            </p>
          </>
        )}

        {info && <p className="info">{info}</p>}
        {error && <p className="error">{error}</p>}
      </div>
      <p className="login-note">Run by the Security Office, IIT Gandhinagar</p>
    </main>
  )
}

import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router'
import { api, useApi } from '../api'
import { useAuth } from '../auth'
import GoogleButton from '../GoogleButton'

type AuthConfig = { google_client_id: string; dev_login: boolean }
type Role = 'student' | 'admin'
/** signin: email + password. code: ask for an emailed code, then set a new password (S30). */
type Mode = 'signin' | 'code'

/** Matches the backend: a new code can be asked for once a minute. */
const RESEND_SECONDS = 60

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
  // One code request at a time, then a short wait before asking again.
  const [sending, setSending] = useState(false)
  const [resendIn, setResendIn] = useState(0)
  const [settingPassword, setSettingPassword] = useState(false)
  // Shown under "Confirm new password" as soon as the two differ.
  const passwordsDiffer = confirm.length > 0 && newPassword !== confirm

  useEffect(() => {
    if (resendIn <= 0) return
    const tick = setTimeout(() => setResendIn((seconds) => seconds - 1), 1000)
    return () => clearTimeout(tick)
  }, [resendIn])

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
    if (sending || resendIn > 0) return
    setError(null)
    setSending(true)
    try {
      const result = await api<{ detail: string }>('auth/password/code', { method: 'POST', body: { email } })
      setCodeSent(true)
      setInfo(result.detail)
      setResendIn(RESEND_SECONDS)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSending(false)
    }
  }

  async function onSetPassword(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (newPassword !== confirm) {
      setError('The two passwords do not match.')
      return
    }
    setSettingPassword(true)
    try {
      const result = await api<{ detail: string }>('auth/password/reset', {
        method: 'POST',
        body: { email, code, password: newPassword, password_confirm: confirm },
      })
      // Back to sign in, with the email already filled in.
      backToSignIn(result.detail)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSettingPassword(false)
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
                <button disabled={sending}>{sending ? 'Sending…' : 'Send code'}</button>
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
                    // Pasted codes often carry spaces; keep only the digits.
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
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
                    aria-invalid={passwordsDiffer}
                  />
                  {passwordsDiffer && <small className="field-error">The two passwords do not match.</small>}
                </label>
                {/* Errors from the server (wrong code, weak password) right where the user is looking. */}
                {error && <p className="error">{error}</p>}
                <button disabled={settingPassword || passwordsDiffer || !confirm}>
                  {settingPassword ? 'Setting password…' : 'Set password'}
                </button>
                <button
                  type="button"
                  className="link"
                  disabled={sending || resendIn > 0}
                  onClick={() => onSendCode()}
                >
                  {sending
                    ? 'Sending…'
                    : resendIn > 0
                      ? `Didn't get it? You can ask for a new code in ${resendIn}s`
                      : "Didn't get it? Send a new code"}
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
        {/* The set-password form shows its own errors above its button. */}
        {error && !(mode === 'code' && codeSent) && <p className="error">{error}</p>}
      </div>
      <p className="login-note">Run by the Security Office, IIT Gandhinagar</p>
    </main>
  )
}

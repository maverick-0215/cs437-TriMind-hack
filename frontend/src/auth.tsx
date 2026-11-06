import { createContext, startTransition, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router'
import { api, ApiError } from './api'
import type { User } from './types'

type AuthState = {
  user: User | null
  loading: boolean
  refresh: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const refresh = useCallback(async () => {
    try {
      setUser(await api<User>('auth/me'))
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 401)) throw e
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    await api('auth/logout', { method: 'POST' })
    // Go to login in the same render as clearing the user, so the login page doesn't
    // remember this page and send the next person who logs in back to it.
    // React Router navigates inside a transition, so clear the user in one too.
    startTransition(() => {
      navigate('/login', { replace: true })
      setUser(null)
    })
  }, [navigate])

  useEffect(() => {
    refresh()
  }, [refresh])

  return <AuthContext.Provider value={{ user, loading, refresh, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}

/** S23: every page except login sends logged-out visitors to the login page. */
export function RequireLogin() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <p className="muted center">Loading…</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}

/** S3: students get a 403 page on every admin page. */
export function RequireAdmin() {
  const { user } = useAuth()
  return user?.is_admin ? <Outlet /> : <Forbidden />
}

/** Reports and claims are for students; admins review them instead. */
export function RequireStudent() {
  const { user } = useAuth()
  return user && !user.is_admin ? <Outlet /> : <Forbidden />
}

export function Forbidden() {
  return (
    <section>
      <h1>403 · Not allowed</h1>
      <p className="muted">You don't have permission to open this page.</p>
    </section>
  )
}

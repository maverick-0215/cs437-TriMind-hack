import { NavLink, Outlet } from 'react-router'
import { useAuth } from './auth'

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <>
      <header className="topbar">
        <div className="wrap topbar-inner">
          <NavLink to="/" className="brand">
            IITGN Lost &amp; Found
          </NavLink>
          <nav>
            <NavLink to="/" end>
              Found items
            </NavLink>
            {user?.is_admin ? (
              <>
                <NavLink to="/admin" end>
                  Security desk
                </NavLink>
                <NavLink to="/admin/items/new">Add found item</NavLink>
                <NavLink to="/admin/handovers">Handovers</NavLink>
              </>
            ) : (
              <>
                <NavLink to="/reports">My lost reports</NavLink>
                <NavLink to="/claims">My claims</NavLink>
              </>
            )}
            <NavLink to="/notifications">
              Notifications
              {user && user.unread_notifications > 0 && <span className="badge">{user.unread_notifications}</span>}
            </NavLink>
            <button className="link" onClick={logout}>
              Log out
            </button>
          </nav>
        </div>
      </header>
      <main className="wrap">
        <Outlet />
      </main>
    </>
  )
}

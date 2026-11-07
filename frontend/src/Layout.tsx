import { useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import { useAuth } from './auth'

export default function Layout() {
  const { user, logout } = useAuth()
  // Phones and tablets: the links fold into a menu (see .menu-toggle in index.css).
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <>
      <header className="topbar">
        <div className="wrap topbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-org">IIT Gandhinagar</span>
            <span className="brand-name">Lost &amp; Found</span>
          </NavLink>
          <button
            type="button"
            className="menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="main-nav"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? 'Close' : 'Menu'}
          </button>
          {/* Clicking any link closes the menu again. */}
          <nav id="main-nav" className={menuOpen ? 'open' : ''} onClick={() => setMenuOpen(false)}>
            <NavLink to="/guide">Guide</NavLink>
            {user?.is_admin ? (
              <>
                <NavLink to="/admin" end>
                  Security desk
                </NavLink>
                <NavLink to="/admin/items/new">Add found item</NavLink>
                <NavLink to="/admin/handovers">Handovers</NavLink>
                <NavLink to="/admin/admins">Admins</NavLink>
              </>
            ) : (
              <>
                <NavLink to="/reports">My lost reports</NavLink>
                <NavLink to="/claims">Pickup codes</NavLink>
              </>
            )}
            <NavLink to="/notifications">
              Notifications
              {user && user.unread_notifications > 0 && <span className="badge">{user.unread_notifications}</span>}
            </NavLink>
            <button className="logout" onClick={logout}>
              Log out
            </button>
          </nav>
        </div>
      </header>
      <main className="wrap main">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="wrap">IITGN Lost &amp; Found · Security Office</div>
      </footer>
    </>
  )
}

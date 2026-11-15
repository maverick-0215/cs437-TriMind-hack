import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { useAuth } from './auth'

type Tile = { to: string; title: string; text: string; icon: ReactNode; primary?: boolean; badge?: number }

// Simple line icons, drawn in the tile's text colour.
const icon = (path: ReactNode) => (
  <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {path}
  </svg>
)
const ICONS = {
  plus: icon(<><circle cx="12" cy="12" r="9" /><path d="M12 8v8M8 12h8" /></>),
  list: icon(<><path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4.5" cy="6" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="18" r="1" /></>),
  search: icon(<><circle cx="11" cy="11" r="6.5" /><path d="m20 20-4.4-4.4" /></>),
  key: icon(<><circle cx="8" cy="15" r="4" /><path d="m11 12 8-8M16 7l2 2M14 9l2 2" /></>),
  bell: icon(<><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" /><path d="M10 20a2 2 0 0 0 4 0" /></>),
  desk: icon(<><rect x="3" y="5" width="18" height="12" rx="1" /><path d="M8 21h8M12 17v4" /></>),
  box: icon(<><path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z" /><path d="m3 7.5 9 4.5 9-4.5M12 12v9" /></>),
  log: icon(<><rect x="5" y="3" width="14" height="18" rx="1" /><path d="M9 8h6M9 12h6M9 16h3" /></>),
  people: icon(<><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6" /></>),
}

/** Big links to every tab on the first page, so people do not miss the menu at the top. */
export default function QuickLinks() {
  const { user } = useAuth()
  if (!user) return null
  const notifications: Tile = {
    to: '/notifications',
    title: 'Notifications',
    text: user.is_admin ? 'Updates from the app.' : 'Matches and approvals show up here.',
    icon: ICONS.bell,
    badge: user.unread_notifications,
  }
  const tiles: Tile[] = user.is_admin
    ? [
        { to: '/admin/items/new', title: 'Add found item', text: 'Log something handed in to the office.', icon: ICONS.plus, primary: true },
        { to: '/admin', title: 'Security desk', text: 'Found items and pickups waiting.', icon: ICONS.desk },
        { to: '/admin/reports', title: 'Lost reports', text: 'Every report students have filed.', icon: ICONS.list },
        { to: '/admin/handovers', title: 'Handovers', text: 'Who collected what, and when.', icon: ICONS.log },
        { to: '/admin/admins', title: 'Admins', text: 'Give other guards access.', icon: ICONS.people },
        notifications,
      ]
    : [
        { to: '/reports/new', title: 'Report a lost item', text: 'Tell the security office what you lost.', icon: ICONS.plus, primary: true },
        { to: '/reports', title: 'My lost reports', text: 'Your reports and the items that match them.', icon: ICONS.list },
        { to: '/found', title: 'Found items', text: 'Everything waiting at the security office.', icon: ICONS.search },
        { to: '/claims', title: 'Pickup codes', text: 'Your code to collect an approved item.', icon: ICONS.key },
        notifications,
      ]

  return (
    <nav className="tiles" aria-label="Quick links">
      {tiles.map((t) => (
        <Link key={t.to} to={t.to} className={t.primary ? 'tile primary' : 'tile'}>
          <span className="tile-icon">{t.icon}</span>
          <span className="tile-title">
            {t.title}
            {!!t.badge && <span className="badge">{t.badge}</span>}
          </span>
          <span className="tile-text">{t.text}</span>
        </Link>
      ))}
    </nav>
  )
}

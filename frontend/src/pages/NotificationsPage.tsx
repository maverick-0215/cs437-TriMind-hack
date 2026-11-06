import { useEffect } from 'react'
import { Link } from 'react-router'
import { api, useApi } from '../api'
import { useAuth } from '../auth'
import { formatDateTime } from '../format'
import type { Notification } from '../types'

export default function NotificationsPage() {
  const { refresh } = useAuth()
  const { data: notifications, error } = useApi<Notification[]>('notifications')

  // Once shown, mark them read and update the unread badge.
  useEffect(() => {
    if (notifications?.some((n) => !n.is_read)) {
      api('notifications/read', { method: 'POST' }).then(refresh)
    }
  }, [notifications, refresh])

  return (
    <>
      <h1>Notifications</h1>
      {error && <p className="error">{error}</p>}
      {notifications?.length === 0 && <p className="empty">No notifications yet.</p>}
      <ul className="cards">
        {notifications?.map((n) => (
          <li key={n.id} className={`card${n.is_read ? '' : ' unread'}`}>
            <p>{n.message}</p>
            <p className="muted">
              {formatDateTime(n.created_at)}
              {n.link && (
                <>
                  {' · '}
                  <Link to={n.link}>Open</Link>
                </>
              )}
            </p>
          </li>
        ))}
      </ul>
    </>
  )
}

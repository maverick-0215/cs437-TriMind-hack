import { Link } from 'react-router'
import { useApi } from '../../api'
import { formatDate, formatDateTime } from '../../format'
import type { AdminClaim, AdminItem } from '../../types'

export default function AdminDashboardPage() {
  const { data: pending } = useApi<AdminClaim[]>('admin/pickups')
  const { data: items, error } = useApi<AdminItem[]>('admin/items')

  return (
    <>
      <div className="page-head">
        <h1>Security desk</h1>
        <Link className="button" to="/admin/items/new">
          Add found item
        </Link>
      </div>

      <h2>Waiting for pickup</h2>
      <p className="muted">Approved people who haven't collected yet. Ask them for their pickup code.</p>
      {pending?.length === 0 && <p className="empty">No one is waiting for pickup.</p>}
      <ul className="cards">
        {pending?.map((c) => (
          <li key={c.id} className="card item-card">
            <div>
              <Link to={`/admin/items/${c.item.id}`}>
                <strong>{c.item.title}</strong>
              </Link>
              <p className="muted">
                {c.student} · approved {formatDateTime(c.created_at)}
              </p>
            </div>
            <Link to={`/admin/items/${c.item.id}`}>Hand over</Link>
          </li>
        ))}
      </ul>

      <h2>All found items</h2>
      {error && <p className="error">{error}</p>}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Date found</th>
              <th>Category</th>
              <th>Title</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items?.map((item) => (
              <tr key={item.id}>
                <td>{formatDate(item.date_found)}</td>
                <td>{item.category}</td>
                <td>
                  <Link to={`/admin/items/${item.id}`}>{item.title}</Link>
                </td>
                <td>
                  <span className={`status ${item.status.toLowerCase()}`}>{item.status.toLowerCase()}</span>
                </td>
              </tr>
            ))}
            {items?.length === 0 && (
              <tr>
                <td colSpan={4} className="empty">
                  No items yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}

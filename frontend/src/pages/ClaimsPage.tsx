import { useApi } from '../api'
import { formatDate, formatDateTime } from '../format'
import type { MyClaim } from '../types'

const STATUS_TEXT = {
  PENDING: 'Waiting for the security office to review',
  REJECTED: 'Rejected',
}

export default function ClaimsPage() {
  const { data: claims, error } = useApi<MyClaim[]>('claims')

  return (
    <>
      <h1>My claims</h1>
      {error && <p className="error">{error}</p>}
      {claims?.length === 0 && <p className="empty">You haven't claimed any items.</p>}
      <ul className="cards">
        {claims?.map((c) => (
          <li key={c.id} className="card">
            <strong>{c.item.title}</strong>
            <p className="muted">
              {c.item.category} · claimed {formatDate(c.created_at)}
            </p>
            {c.pickup_code ? (
              <>
                <p>Approved. Show this pickup code at the security office:</p>
                <p className="code">{c.pickup_code}</p>
              </>
            ) : c.code_used_at ? (
              <p>Collected on {formatDateTime(c.code_used_at)}.</p>
            ) : (
              <p>{STATUS_TEXT[c.status as keyof typeof STATUS_TEXT]}</p>
            )}
          </li>
        ))}
      </ul>
    </>
  )
}

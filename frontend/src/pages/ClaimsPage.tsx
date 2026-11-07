import { useApi } from '../api'
import { formatDate, formatDateTime } from '../format'
import type { MyClaim } from '../types'

const STATUS_TEXT = {
  PENDING: 'Waiting for the security office',
  REJECTED: 'Approval cancelled by the security office',
}

export default function ClaimsPage() {
  const { data: claims, error } = useApi<MyClaim[]>('claims')

  return (
    <>
      <h1>Pickup codes</h1>
      <p className="muted">
        When the security office checks you and approves you for an item, your pickup code appears here. Tell it to the
        guard to collect the item.
      </p>
      {error && <p className="error">{error}</p>}
      {claims?.length === 0 && <p className="empty">No pickup codes yet.</p>}
      <ul className="cards">
        {claims?.map((c) => (
          <li key={c.id} className="card">
            <strong>{c.item.title}</strong>
            <p className="muted">
              {c.item.category} · approved {formatDate(c.created_at)}
            </p>
            {c.pickup_code ? (
              <>
                <p>Approved. Tell this pickup code to the guard:</p>
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

import { Link } from 'react-router'
import { useApi } from '../../api'
import { formatDate, formatDateTime } from '../../format'
import { REPORT_STATUS, type AdminLostReport } from '../../types'

/** S34: every student's lost report, with the found items that match the open ones. */
export default function AdminReportsPage() {
  const { data: reports, error } = useApi<AdminLostReport[]>('admin/reports')

  return (
    <>
      <h1>Lost reports</h1>
      <p className="muted">
        Every lost report students have filed, newest first. Reports are deleted 60 days after their item is
        collected; the handover log keeps the record.
      </p>
      {error && <p className="error">{error}</p>}
      {reports?.length === 0 && <p className="empty">No lost reports yet.</p>}
      <ul className="cards">
        {reports?.map((r) => (
          <li key={r.id} className="card">
            <p>
              <strong>{r.title}</strong>{' '}
              <span className={`status ${REPORT_STATUS[r.status].className}`}>{REPORT_STATUS[r.status].label}</span>
            </p>
            <p className="muted">
              {r.student} · {r.category} · lost {formatDate(r.date_lost)} · {r.place_lost || 'place not given'} ·
              filed {formatDateTime(r.created_at)}
            </p>
            <p className="pre">{r.private_details}</p>
            {r.has_photo && <img className="photo" src={`/api/reports/${r.id}/photo`} alt={`${r.student}'s photo of ${r.title}`} />}

            {r.item && (
              <p>
                {r.status === 'CLOSED' ? 'Collected' : 'Approved for'}:{' '}
                <Link to={`/admin/items/${r.item.id}`}>{r.item.title}</Link>
                {r.closed_at && <> on {formatDateTime(r.closed_at)}</>}
              </p>
            )}
            {r.status === 'OPEN' &&
              (r.matches.length === 0 ? (
                <p className="muted">No matching found item yet.</p>
              ) : (
                <>
                  <p>Matching found items:</p>
                  <ul>
                    {r.matches.map((m) => (
                      <li key={m.id}>
                        <Link to={`/admin/items/${m.id}`}>{m.title}</Link> · {m.score}% match · found{' '}
                        {formatDate(m.date_found)} at {m.general_area}
                      </li>
                    ))}
                  </ul>
                </>
              ))}
          </li>
        ))}
      </ul>
    </>
  )
}

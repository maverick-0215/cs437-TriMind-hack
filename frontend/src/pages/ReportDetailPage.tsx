import { useParams } from 'react-router'
import { useApi } from '../api'
import { formatDate, formatDateTime } from '../format'
import { REPORT_STATUS, type ReportDetail } from '../types'

export default function ReportDetailPage() {
  const { id } = useParams()
  const { data: report, error } = useApi<ReportDetail>(`reports/${id}`)

  if (error) return <p className="error">{error}</p>
  if (!report) return null

  return (
    <>
      <h1>
        {report.title}{' '}
        <span className={`status ${REPORT_STATUS[report.status].className}`}>{REPORT_STATUS[report.status].label}</span>
      </h1>
      <dl className="card details">
        <dt>Category</dt>
        <dd>{report.category}</dd>
        <dt>Date lost</dt>
        <dd>{formatDate(report.date_lost)}</dd>
        <dt>Place lost</dt>
        <dd>{report.place_lost}</dd>
        <dt>Identifying details</dt>
        <dd className="pre">{report.private_details}</dd>
      </dl>

      {/* S27: once approved or collected, the report needs no more matches. */}
      {report.status === 'CLOSED' && report.item && (
        <p className="card">
          Closed. You collected <strong>{report.item.title}</strong> from the security office
          {report.closed_at && <> on {formatDateTime(report.closed_at)}</>}.
        </p>
      )}
      {report.status === 'APPROVED' && report.item && (
        <p className="card">
          You were approved to collect <strong>{report.item.title}</strong>. Tell the guard your code from{' '}
          <strong>Pickup codes</strong> to collect it.
        </p>
      )}

      {/* S25: found items matching by 60% or more, where they were found and who to meet. */}
      {report.status === 'OPEN' && <h2>Found items that may be yours</h2>}
      {report.status !== 'OPEN' ? null : report.matches.length === 0 ? (
        <p className="empty">No such item is here yet. We'll notify you as soon as a matching item is found.</p>
      ) : (
        <>
          <p className="muted">
            If one of these is yours, go to the security office ({report.security_contact}) and meet the person listed.
            They will check the item with you and approve you, and your pickup code will appear on{' '}
            <strong>Pickup codes</strong>.
          </p>
          <ul className="cards">
            {report.matches.map((item) => (
              <li key={item.id} className="card item-card">
                <div>
                  <strong>{item.title}</strong>
                  <p className="muted">
                    {item.category} · found {formatDate(item.date_found)}
                  </p>
                  <p>
                    <strong>Found at:</strong> {item.general_area}
                    <br />
                    <strong>Meet:</strong> <a href={`mailto:${item.contact}`}>{item.contact}</a>,{' '}
                    {report.security_contact}
                  </p>
                </div>
                <span className="status available">{item.score}% match</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  )
}

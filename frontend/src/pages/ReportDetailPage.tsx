import { Link, useParams } from 'react-router'
import { useApi } from '../api'
import { formatDate } from '../format'
import type { Report } from '../types'

export default function ReportDetailPage() {
  const { id } = useParams()
  const { data: report, error } = useApi<Report>(`reports/${id}`)

  if (error) return <p className="error">{error}</p>
  if (!report) return null

  const item = report.linked_item
  return (
    <>
      <h1>{report.title}</h1>
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

      <h2>Matched found item</h2>
      {item ? (
        <div className="card item-card">
          <div>
            <strong>{item.title}</strong>
            <p className="muted">
              {item.category} · found {formatDate(item.date_found)} · {item.general_area}
            </p>
          </div>
          <Link className="button" to={`/items/${item.id}/claim`}>
            Claim this item
          </Link>
        </div>
      ) : (
        <p className="empty">Not matched to a found item yet. We'll notify you when it is.</p>
      )}
    </>
  )
}

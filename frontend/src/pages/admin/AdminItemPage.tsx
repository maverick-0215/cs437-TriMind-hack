import { useState, type FormEvent, type ReactNode } from 'react'
import { useParams } from 'react-router'
import { api, useApi } from '../../api'
import { formatDate, formatDateTime } from '../../format'
import type { AdminItemDetail, AdminReport } from '../../types'

function ReportCard({ report, action }: { report: AdminReport; action?: ReactNode }) {
  return (
    <div className="card">
      <strong>{report.title}</strong>
      <p className="muted">
        {report.student} · {report.category} · lost {formatDate(report.date_lost)} at {report.place_lost}
      </p>
      <p className="pre">{report.private_details}</p>
      {action}
    </div>
  )
}

export default function AdminItemPage() {
  const { id } = useParams()
  const { data, error, reload } = useApi<AdminItemDetail>(`admin/items/${id}`)
  const [actionError, setActionError] = useState<string | null>(null)
  const [handoverError, setHandoverError] = useState<string | null>(null)

  async function act(path: string, body?: object, setError = setActionError) {
    setError(null)
    try {
      await api(path, { method: 'POST', body })
      reload()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  function linkReport(reportId: number) {
    act(`admin/items/${id}/link`, { report_id: reportId })
  }

  function onLinkAny(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    linkReport(Number(new FormData(event.currentTarget).get('report_id')))
  }

  function onHandover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    act(`admin/items/${id}/handover`, { code: new FormData(event.currentTarget).get('code') }, setHandoverError)
  }

  if (error) return <p className="error">{error}</p>
  if (!data) return null
  const { item } = data

  return (
    <>
      <h1>
        {item.title} <span className={`status ${item.status.toLowerCase()}`}>{item.status.toLowerCase()}</span>
      </h1>
      {actionError && <p className="error">{actionError}</p>}

      <div className="item-grid">
        <dl className="card details">
          <dt>Category</dt>
          <dd>{item.category}</dd>
          <dt>Date found</dt>
          <dd>{formatDate(item.date_found)}</dd>
          <dt>General area</dt>
          <dd>{item.general_area}</dd>
          <dt>
            Exact location <span className="tag">private</span>
          </dt>
          <dd>{item.exact_location}</dd>
          <dt>
            Description <span className="tag">private</span>
          </dt>
          <dd className="pre">{item.description}</dd>
          <dt>Added by</dt>
          <dd>
            {item.added_by} on {formatDateTime(item.created_at)}
          </dd>
        </dl>
        {item.has_photo && <img className="photo" src={`/api/admin/items/${item.id}/photo`} alt={`Photo of ${item.title}`} />}
      </div>

      <h2>Claims</h2>
      {data.claims.length === 0 && <p className="empty">No claims.</p>}
      {data.claims.map((c) => (
        <div key={c.id} className="card">
          <p>
            <strong>{c.student}</strong> <span className="muted">· {formatDateTime(c.created_at)} · {c.status.toLowerCase()}</span>
          </p>
          <p className="pre">{c.description}</p>
          {c.status === 'PENDING' && (
            <div className="row">
              <button onClick={() => act(`admin/claims/${c.id}/approve`)}>Approve</button>
              <button className="secondary" onClick={() => act(`admin/claims/${c.id}/reject`)}>
                Reject
              </button>
            </div>
          )}
        </div>
      ))}

      {data.awaiting_pickup_by && (
        <>
          <h2>Hand over</h2>
          <form className="card stack narrow" onSubmit={onHandover}>
            <label>
              Pickup code from {data.awaiting_pickup_by}
              <input name="code" required inputMode="numeric" pattern="[0-9]{6}" maxLength={6} autoComplete="off" />
            </label>
            {handoverError && <p className="error">{handoverError}</p>}
            <button>Confirm handover</button>
          </form>
        </>
      )}

      {data.handover && (
        <p className="card">
          Returned to {data.handover.student} by {data.handover.admin} on {formatDateTime(data.handover.handed_over_at)}.
        </p>
      )}

      {item.status !== 'RETURNED' && (
        <>
          <h2>Suggested lost reports</h2>
          <p className="muted">Unlinked reports in the same category, lost on or before {formatDate(item.date_found)}.</p>
          {data.suggestions.length === 0 && <p className="empty">No suggestions.</p>}
          {data.suggestions.map((r) => (
            <ReportCard key={r.id} report={r} action={<button onClick={() => linkReport(r.id)}>Link and notify</button>} />
          ))}
        </>
      )}

      <h2>Linked reports</h2>
      {data.linked_reports.length === 0 && <p className="empty">None linked.</p>}
      {data.linked_reports.map((r) => (
        <ReportCard key={r.id} report={r} />
      ))}

      {item.status !== 'RETURNED' && data.link_options.length > 0 && (
        <>
          <h3>Link any report</h3>
          <form className="row" onSubmit={onLinkAny}>
            <select name="report_id" required defaultValue="">
              <option value="" disabled>
                Choose a lost report…
              </option>
              {data.link_options.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.category}: {r.title} ({r.student}){r.linked_item ? ' · linked elsewhere' : ''}
                </option>
              ))}
            </select>
            <button>Link and notify</button>
          </form>
        </>
      )}
    </>
  )
}

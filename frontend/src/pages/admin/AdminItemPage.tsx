import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router'
import { api, useApi } from '../../api'
import { formatDate, formatDateTime } from '../../format'
import type { AdminItemDetail } from '../../types'

const CLAIM_TEXT = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'approval cancelled',
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

  function approve(who: { report_id: number } | { email: string }) {
    act(`admin/items/${id}/approve`, who)
  }

  function onApproveEmail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    approve({ email: String(new FormData(event.currentTarget).get('email')) })
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

      {/* S16: the guard checks the person in person, then approves them. */}
      {item.status === 'AVAILABLE' && (
        <>
          <h2>Who may own this</h2>
          <p className="muted">
            Students whose lost reports match this item by 60% or more. When one comes to the office, check their
            identifying details against the item, then approve them.
          </p>
          {data.candidates.length === 0 && <p className="empty">No matching lost reports yet.</p>}
          {data.candidates.map((r) => (
            <div key={r.id} className="card">
              <p>
                <strong>{r.student}</strong> <span className="status available">{r.score}% match</span>
              </p>
              <p className="muted">
                {r.title} · {r.category} · lost {formatDate(r.date_lost)} at {r.place_lost}
              </p>
              <p className="pre">{r.private_details}</p>
              <button onClick={() => approve({ report_id: r.id })}>Approve {r.student}</button>
            </div>
          ))}

          <h3>Approve someone else</h3>
          <form className="row" onSubmit={onApproveEmail}>
            <input name="email" type="email" required placeholder="name@iitgn.ac.in" aria-label="Email to approve" />
            <button>Approve</button>
          </form>
        </>
      )}

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

      {data.claims.length > 0 && (
        <>
          <h2>Approvals</h2>
          {data.claims.map((c) => (
            <div key={c.id} className="card item-card">
              <p>
                <strong>{c.student}</strong>{' '}
                <span className="muted">
                  · {formatDateTime(c.created_at)} · {CLAIM_TEXT[c.status]}
                </span>
              </p>
              {c.status === 'APPROVED' && data.awaiting_pickup_by === c.student && (
                <button className="secondary" onClick={() => act(`admin/claims/${c.id}/cancel`)}>
                  Cancel approval
                </button>
              )}
            </div>
          ))}
        </>
      )}
    </>
  )
}

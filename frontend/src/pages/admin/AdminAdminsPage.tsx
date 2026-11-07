import { useState, type FormEvent } from 'react'
import { api, useApi } from '../../api'
import { useAuth } from '../../auth'
import { formatDate } from '../../format'
import type { AdminList } from '../../types'

/** S28: admins add and remove other admins. */
export default function AdminAdminsPage() {
  const { user } = useAuth()
  const { data, error, reload } = useApi<AdminList>('admin/admins')
  const [actionError, setActionError] = useState<string | null>(null)
  const [email, setEmail] = useState('')

  async function act(path: string, body?: object) {
    setActionError(null)
    try {
      await api(path, { method: 'POST', body })
      reload()
      return true
    } catch (e) {
      setActionError((e as Error).message)
      return false
    }
  }

  async function onAdd(event: FormEvent) {
    event.preventDefault()
    if (await act('admin/admins', { email })) setEmail('')
  }

  return (
    <>
      <h1>Admins</h1>
      <p className="muted">
        Admins can add found items, approve people and hand items over. Someone who becomes an admin can no longer file
        lost reports.
      </p>

      <form className="card row" onSubmit={onAdd}>
        <input
          type="email"
          required
          placeholder="name@iitgn.ac.in"
          aria-label="Email of new admin"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button>Add admin</button>
      </form>
      {actionError && <p className="error">{actionError}</p>}
      {error && <p className="error">{error}</p>}

      {data?.added.length === 0 && <p className="empty">No admins added yet.</p>}
      {data && (
        <ul className="cards">
          {data.added.map((a) => (
            <li key={a.id} className="card item-card">
              <div>
                <strong>{a.email}</strong>
                <p className="muted">
                  Added by {a.added_by} on {formatDate(a.created_at)}
                </p>
              </div>
              {a.email !== user?.email.toLowerCase() && (
                <button className="secondary" onClick={() => act(`admin/admins/${a.id}/remove`)}>
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

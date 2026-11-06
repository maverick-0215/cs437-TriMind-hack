import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useApi } from '../api'
import { useAuth } from '../auth'
import { formatDate } from '../format'
import { CATEGORIES, type PublicItem } from '../types'

const FILTERS = ['q', 'category', 'date_from', 'date_to']

export default function FoundListPage() {
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const { data: items, error } = useApi<PublicItem[]>(`items?${params}`)

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const next = new URLSearchParams()
    for (const name of FILTERS) {
      const value = String(form.get(name) ?? '').trim()
      if (value) next.set(name, value)
    }
    setParams(next)
  }

  return (
    <>
      <h1>Found items</h1>
      <p className="muted">
        Items held at the IITGN security office.
        {!user?.is_admin && (
          <>
            {' '}
            Lost something that isn't here? <Link to="/reports/new">File a lost report</Link>.
          </>
        )}
      </p>

      {/* key: reset the inputs when the URL changes, e.g. after "Clear". */}
      <form className="filters" onSubmit={applyFilters} key={params.toString()}>
        <label>
          Search
          <input name="q" type="search" placeholder="bottle, wallet…" defaultValue={params.get('q') ?? ''} />
        </label>
        <label>
          Category
          <select name="category" defaultValue={params.get('category') ?? ''}>
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Found from
          <input name="date_from" type="date" defaultValue={params.get('date_from') ?? ''} />
        </label>
        <label>
          to
          <input name="date_to" type="date" defaultValue={params.get('date_to') ?? ''} />
        </label>
        <button>Apply</button>
        <button type="button" className="secondary" onClick={() => setParams({})}>
          Clear
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {items?.length === 0 && <p className="empty">No found items match.</p>}
      <ul className="cards">
        {items?.map((item) => (
          <li key={item.id} className="card item-card">
            <div>
              <strong>{item.title}</strong>
              <p className="muted">
                {item.category} · found {formatDate(item.date_found)} · {item.general_area}
              </p>
            </div>
            {user?.is_admin ? (
              <Link to={`/admin/items/${item.id}`}>Manage</Link>
            ) : (
              <Link className="button" to={`/items/${item.id}/claim`}>
                This is mine
              </Link>
            )}
          </li>
        ))}
      </ul>
    </>
  )
}

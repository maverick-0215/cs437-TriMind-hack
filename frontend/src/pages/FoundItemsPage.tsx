import { useApi } from '../api'
import { formatDate } from '../format'
import type { FoundList } from '../types'

/** S6: every found item at the security office, with where it was found. Students contact the office. */
export default function FoundItemsPage() {
  const { data, error } = useApi<FoundList>('items')

  return (
    <>
      <h1>Found items</h1>
      <p className="muted">
        Items currently held at the security office. If one is yours, go to the security office
        {data && <> ({data.security_contact})</>}.
      </p>

      {error && <p className="error">{error}</p>}
      {data?.items.length === 0 && <p className="empty">No found items at the moment.</p>}
      <ul className="cards">
        {data?.items.map((item) => (
          <li key={item.id} className="card">
            <strong>{item.title}</strong>
            <p className="muted">
              {item.category} · found {formatDate(item.date_found)}
            </p>
            <p>
              <strong>Found at:</strong> {item.general_area}
            </p>
          </li>
        ))}
      </ul>
    </>
  )
}

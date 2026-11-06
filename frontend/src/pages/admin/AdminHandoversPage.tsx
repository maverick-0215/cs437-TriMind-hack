import { Link } from 'react-router'
import { useApi } from '../../api'
import { formatDateTime } from '../../format'
import type { Handover } from '../../types'

export default function AdminHandoversPage() {
  const { data: handovers, error } = useApi<Handover[]>('admin/handovers')

  return (
    <>
      <h1>Handover log</h1>
      {error && <p className="error">{error}</p>}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Date and time</th>
              <th>Item</th>
              <th>Student</th>
              <th>Handed over by</th>
            </tr>
          </thead>
          <tbody>
            {handovers?.map((h) => (
              <tr key={h.id}>
                <td>{formatDateTime(h.handed_over_at)}</td>
                <td>
                  <Link to={`/admin/items/${h.item.id}`}>{h.item.title}</Link>
                </td>
                <td>{h.student}</td>
                <td>{h.admin}</td>
              </tr>
            ))}
            {handovers?.length === 0 && (
              <tr>
                <td colSpan={4} className="empty">
                  No handovers yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}

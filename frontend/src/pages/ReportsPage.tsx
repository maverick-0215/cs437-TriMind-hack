import { Link } from 'react-router'
import { useApi } from '../api'
import { formatDate } from '../format'
import { REPORT_STATUS, type Report } from '../types'

export default function ReportsPage() {
  const { data: reports, error } = useApi<Report[]>('reports')

  return (
    <>
      <h1>My lost reports</h1>
      <p>
        <Link className="button" to="/reports/new">
          File a lost report
        </Link>
      </p>
      {error && <p className="error">{error}</p>}
      {reports?.length === 0 && <p className="empty">You haven't filed any lost reports.</p>}
      <ul className="cards">
        {reports?.map((r) => (
          <li key={r.id} className="card item-card">
            <div>
              <Link to={`/reports/${r.id}`}>
                <strong>{r.title}</strong>
              </Link>
              <p className="muted">
                {r.category} · lost {formatDate(r.date_lost)} · {r.place_lost}
              </p>
            </div>
            <span className={`status ${REPORT_STATUS[r.status].className}`}>{REPORT_STATUS[r.status].label}</span>
          </li>
        ))}
      </ul>
    </>
  )
}

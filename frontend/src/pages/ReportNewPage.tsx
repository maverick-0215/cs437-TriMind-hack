import { useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../api'
import { todayISO } from '../format'
import { CATEGORIES, type Report } from '../types'

export default function ReportNewPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  // S32: one save at a time. The ref blocks a second click instantly, before React re-renders.
  const saving = useRef(false)
  const [isSaving, setIsSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving.current) return
    saving.current = true
    setIsSaving(true)
    setError(null)
    try {
      const report = await api<Report>('reports', {
        method: 'POST',
        body: Object.fromEntries(new FormData(event.currentTarget)),
      })
      navigate(`/reports/${report.id}`)
    } catch (e) {
      setError((e as Error).message)
      saving.current = false
      setIsSaving(false)
    }
  }

  return (
    <section className="form-page">
      <h1>File a lost report</h1>
      <form className="card stack" onSubmit={submit}>
        <label>
          Category
          <select name="category" required defaultValue="">
            <option value="" disabled>
              Choose…
            </option>
            {CATEGORIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Title
          <input name="title" required maxLength={120} placeholder="Black Samsung phone" />
        </label>
        <label>
          Date lost
          <input name="date_lost" type="date" required max={todayISO()} />
        </label>
        <label>
          Place lost
          <input name="place_lost" required maxLength={200} placeholder="Library reading hall" />
        </label>
        <label>
          Identifying details
          <small className="muted">Marks, stickers, contents, serial number… Only you and the security office see this.</small>
          <textarea name="private_details" required rows={4} />
        </label>
        {error && <p className="error">{error}</p>}
        <button disabled={isSaving}>{isSaving ? 'Saving…' : 'File report'}</button>
      </form>
    </section>
  )
}

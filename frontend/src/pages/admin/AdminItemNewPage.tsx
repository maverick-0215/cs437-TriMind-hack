import { useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../../api'
import { todayISO } from '../../format'
import { CATEGORIES, type AdminItem } from '../../types'

export default function AdminItemNewPage() {
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
    const form = new FormData(event.currentTarget)
    if (!(form.get('photo') as File).size) form.delete('photo')
    try {
      const item = await api<AdminItem>('admin/items', { method: 'POST', body: form })
      // S13: the item page shows the suggested lost reports right away.
      navigate(`/admin/items/${item.id}`)
    } catch (e) {
      setError((e as Error).message)
      saving.current = false
      setIsSaving(false)
    }
  }

  return (
    <section className="form-page">
      <h1>Add found item</h1>
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
          <input name="title" required maxLength={120} placeholder="Black phone" />
        </label>
        <label>
          Date found
          <input name="date_found" type="date" required max={todayISO()} />
        </label>
        <label>
          General area
          <input name="general_area" required maxLength={120} placeholder="Library" />
        </label>

        <p className="form-note">Only admins can see the details below.</p>
        <label>
          Exact location
          <input name="exact_location" required maxLength={200} placeholder="Reading hall, desk 14" />
        </label>
        <label>
          Description
          <textarea name="description" required rows={3} />
        </label>
        <label>
          Photo (optional, up to 5 MB)
          <input name="photo" type="file" accept="image/*" />
        </label>
        {error && <p className="error">{error}</p>}
        <button disabled={isSaving}>{isSaving ? 'Saving…' : 'Add item'}</button>
      </form>
    </section>
  )
}

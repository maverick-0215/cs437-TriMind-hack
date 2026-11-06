import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, useApi } from '../api'
import { formatDate } from '../format'
import type { PublicItem } from '../types'

export default function ClaimPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: items } = useApi<PublicItem[]>('items')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const item = items?.find((i) => String(i.id) === id)

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      await api(`items/${id}/claim`, { method: 'POST', body: { description } })
      navigate('/claims')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (!items) return null
  if (!item) return <p className="empty">This item is not available to claim.</p>

  return (
    <>
      <h1>Claim: {item.title}</h1>
      <p className="muted">
        {item.category} · found {formatDate(item.date_found)} · {item.general_area}
      </p>
      <form className="card stack" onSubmit={submit}>
        <label>
          Describe features that prove it is yours
          <small className="muted">
            Marks, stickers, contents, lock screen… The security office compares this with the item.
          </small>
          <textarea required rows={4} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        {error && <p className="error">{error}</p>}
        <button>Send claim</button>
      </form>
    </>
  )
}

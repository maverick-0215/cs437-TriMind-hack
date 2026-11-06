import { useCallback, useEffect, useState } from 'react'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function csrfToken(): string {
  const cookie = document.cookie.split('; ').find((c) => c.startsWith('csrftoken='))
  return cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
}

function errorMessage(data: unknown): string {
  if (data && typeof data === 'object') {
    if ('detail' in data) return String(data.detail)
    // Django REST Framework field errors look like { field: ["message"] }.
    return Object.entries(data)
      .map(([field, messages]) => `${field.replace(/_/g, ' ')}: ${[messages].flat().join(' ')}`)
      .join(' ')
  }
  return 'Something went wrong. Try again.'
}

/** Call the Django API at /api/<path>. JSON in, JSON out; FormData is sent as-is (for photos). */
export async function api<T = void>(path: string, options: { method?: string; body?: unknown } = {}): Promise<T> {
  const { method = 'GET', body } = options
  const headers: Record<string, string> = {}
  let payload: BodyInit | undefined
  if (body instanceof FormData) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (method !== 'GET') headers['X-CSRFToken'] = csrfToken()

  const response = await fetch(`/api/${path}`, { method, headers, body: payload, credentials: 'same-origin' })
  if (response.status === 204) return undefined as T
  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(response.status, errorMessage(data))
  return data as T
}

/** Load `path` on mount (and whenever it changes). */
export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(() => {
    api<T>(path)
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
  }, [path])

  useEffect(reload, [reload])
  return { data, error, reload }
}

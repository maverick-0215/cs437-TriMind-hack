import { useEffect, useRef, useState } from 'react'

// The small part of Google Identity Services (https://developers.google.com/identity/gsi/web) we use.
type GoogleIdentity = {
  initialize(options: { client_id: string; callback: (response: { credential: string }) => void }): void
  renderButton(element: HTMLElement, options: Record<string, string>): void
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdentity } }
  }
}

let scriptLoading: Promise<void> | null = null

function loadGoogleScript(): Promise<void> {
  scriptLoading ??= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => {
      scriptLoading = null
      reject(new Error('Could not load Google sign-in.'))
    }
    document.head.appendChild(script)
  })
  return scriptLoading
}

/** Renders Google's own "Sign in with Google" button and hands back the signed ID token. */
export default function GoogleButton({
  clientId,
  onCredential,
}: {
  clientId: string
  onCredential: (credential: string) => void
}) {
  const container = useRef<HTMLDivElement>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    loadGoogleScript()
      .then(() => {
        const google = window.google
        if (cancelled || !container.current || !google) return
        google.accounts.id.initialize({ client_id: clientId, callback: (r) => onCredential(r.credential) })
        google.accounts.id.renderButton(container.current, { theme: 'outline', size: 'large', text: 'signin_with' })
      })
      .catch(() => setFailed(true))
    return () => {
      cancelled = true
    }
  }, [clientId, onCredential])

  if (failed) return <p className="error">Couldn't load Google sign-in. Check your connection and reload.</p>
  return <div ref={container} />
}

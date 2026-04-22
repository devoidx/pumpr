import { useEffect, useState } from 'react'

export default function VerifyEmailPage() {
  const [status, setStatus]   = useState('verifying')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token')
    if (!token) { setStatus('error'); setMessage('No verification token found.'); return }
    fetch(`/api/v1/auth/verify/${token}`)
      .then(r => r.json())
      .then(d => { if (d.message) { setStatus('success'); setMessage(d.message) } else { setStatus('error'); setMessage(d.detail || 'Verification failed.') } })
      .catch(() => { setStatus('error'); setMessage('An error occurred. Please try again.') })
  }, [])

  const card = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, maxWidth: 420, padding: '2.5rem 2rem', textAlign: 'center', width: '100%' }
  return (
    <div style={{ alignItems: 'center', background: 'var(--bg)', display: 'flex', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
      <div style={card}>
        <div style={{ fontSize: '2.5rem' }}>⛽</div>
        {status === 'verifying' && <><h2 style={{ color: 'var(--text)' }}>Verifying your email…</h2><p style={{ color: '#888' }}>Just a moment.</p></>}
        {status === 'success'   && <><h2 style={{ color: '#6dbf7e' }}>Email verified ✓</h2><p style={{ color: '#888' }}>{message}</p><a href="/" style={{ color: 'var(--amber)' }}>Go to Pumpr →</a></>}
        {status === 'error'     && <><h2 style={{ color: '#f08080' }}>Verification failed</h2><p style={{ color: '#888' }}>{message}</p><a href="/" style={{ color: 'var(--amber)' }}>Back to Pumpr</a></>}
      </div>
    </div>
  )
}

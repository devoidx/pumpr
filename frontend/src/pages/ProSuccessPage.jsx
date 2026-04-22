import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function ProSuccessPage() {
  const navigate = useNavigate()
  const [countdown, setCountdown] = useState(5)

  useEffect(() => {
    const t = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { clearInterval(t); navigate('/'); return 0 }
        return c - 1
      })
    }, 1000)
    return () => clearInterval(t)
  }, [navigate])

  return (
    <div style={{ alignItems: 'center', background: 'var(--bg)', display: 'flex', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, maxWidth: 460, padding: '2.5rem 2rem', textAlign: 'center', width: '100%' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⛽✓</div>
        <h2 style={{ color: 'var(--amber)', fontSize: '1.6rem', fontWeight: 800, margin: '0 0 0.75rem' }}>Welcome to Pumpr Pro!</h2>
        <p style={{ color: '#a0a0a8', marginBottom: '1.5rem', lineHeight: 1.6 }}>
          Your subscription is now active. You now have access to all Pro features.
        </p>
        <p style={{ color: 'var(--text3)', fontSize: '0.85rem' }}>Redirecting to the map in {countdown}s…</p>
        <button
          onClick={() => navigate('/')}
          style={{ marginTop: '1rem', background: 'var(--amber)', border: 'none', borderRadius: 8, color: '#000', cursor: 'pointer', fontWeight: 700, padding: '0.7rem 1.5rem' }}
        >
          Go to map now
        </button>
      </div>
    </div>
  )
}

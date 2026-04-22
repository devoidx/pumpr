import { useState } from 'react'
import './AuthModal.css'

export default function ResetPasswordPage() {
  const token = new URLSearchParams(window.location.search).get('token') ?? ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault(); setError('')
    if (password !== confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/v1/auth/password-reset/confirm', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Reset failed')
      setSuccess(data.message)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div style={{ alignItems: 'center', background: 'var(--bg)', display: 'flex', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
      <div className="auth-modal" style={{ position: 'static', maxWidth: 420, width: '100%' }}>
        <div className="auth-header"><span className="auth-logo">⛽</span><h2>Reset your password</h2></div>
        {success ? (
          <div className="auth-success-block"><p className="auth-success">{success}</p><a href="/" style={{ color: 'var(--amber)' }}>Sign in →</a></div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {error && <p className="auth-error">{error}</p>}
            {!token && <p className="auth-error">Invalid reset link — please request a new one.</p>}
            <label>New password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" minLength={8} required autoComplete="new-password" />
            <small className="auth-hint">Min 8 chars, one uppercase, one number</small>
            <label>Confirm password</label>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="••••••••" required autoComplete="new-password" />
            <button type="submit" className="auth-btn-primary" disabled={loading || !token}>{loading ? 'Updating…' : 'Set new password'}</button>
          </form>
        )}
      </div>
    </div>
  )
}

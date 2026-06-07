import { useState } from 'react'
import './AuthModal.css'

export default function ResetPasswordPage() {
  const token = new URLSearchParams(window.location.search).get('token') ?? ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [showPassword, setShowPassword] = useState(false)

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
            <div style={{position:'relative'}}>
              <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" minLength={8} required autoComplete="new-password" style={{paddingRight:'2.2rem', width:'100%', boxSizing:'border-box'}} />
              <button type="button" onClick={() => setShowPassword(v => !v)} style={{position:'absolute', right:'0.5rem', top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', color:'var(--text3)', padding:'0', lineHeight:1}} tabIndex={-1} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                {showPassword
                  ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                }
              </button>
            </div>
            <small className="auth-hint">Min 8 chars, one uppercase, one number</small>
            <label>Confirm password</label>
            <div style={{position:'relative'}}>
              <input type={showPassword ? 'text' : 'password'} value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="••••••••" required autoComplete="new-password" style={{paddingRight:'2.2rem', width:'100%', boxSizing:'border-box'}} />
            </div>
            <button type="submit" className="auth-btn-primary" disabled={loading || !token}>{loading ? 'Updating…' : 'Set new password'}</button>
          </form>
        )}
      </div>
    </div>
  )
}

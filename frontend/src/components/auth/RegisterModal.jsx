import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import './AuthModal.css'

export default function RegisterModal({ onClose, onSwitchToLogin }) {
  const { register } = useAuth()
  const [email, setEmail]       = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault(); setError('')
    if (password !== confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    try { const r = await register(email, username, password); setSuccess(r.message || 'Account created! Check your email.') }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="auth-close" onClick={onClose}>✕</button>
        <div className="auth-header"><span className="auth-logo">⛽</span><h2>Create your account</h2></div>
        {success ? (
          <div className="auth-success-block">
            <p className="auth-success">{success}</p>
            <p className="auth-switch"><button className="auth-link" onClick={onSwitchToLogin}>Back to sign in</button></p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {error && <p className="auth-error">{error}</p>}
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" />
            <label>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="pumpr_user" pattern="[a-zA-Z0-9_\-]+" minLength={3} maxLength={30} required autoComplete="username" />
            <small className="auth-hint">Letters, numbers, _ and - only</small>
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" minLength={8} required autoComplete="new-password" />
            <small className="auth-hint">Min 8 chars, one uppercase, one number</small>
            <label>Confirm password</label>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="••••••••" required autoComplete="new-password" />
            <button type="submit" className="auth-btn-primary" disabled={loading}>{loading ? 'Creating account…' : 'Create account'}</button>
          </form>
        )}
        {!success && <p className="auth-switch">Already have an account? <button className="auth-link" onClick={onSwitchToLogin}>Sign in</button></p>}
      </div>
    </div>
  )
}

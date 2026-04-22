import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import './AuthModal.css'

export default function LoginModal({ onClose, onSwitchToRegister }) {
  const { login, requestPasswordReset } = useAuth()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [showReset, setShowReset] = useState(false)
  const [resetEmail, setResetEmail] = useState('')
  const [resetSent, setResetSent]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try { await login(email, password); onClose() }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function handleReset(e) {
    e.preventDefault()
    await requestPasswordReset(resetEmail)
    setResetSent(true)
  }

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="auth-close" onClick={onClose}>✕</button>
        <div className="auth-header"><span className="auth-logo">⛽</span><h2>Sign in to Pumpr</h2></div>
        <form onSubmit={handleSubmit} className="auth-form">
          {error && <p className="auth-error">{error}</p>}
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" />
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required autoComplete="current-password" />
          <button type="submit" className="auth-btn-primary" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <button className="auth-link" style={{marginTop:'0.75rem',display:'block',textAlign:'center'}} onClick={() => setShowReset(v => !v)}>Forgot your password?</button>
        {showReset && !resetSent && (
          <form onSubmit={handleReset} className="auth-form auth-reset-inline">
            <label>Enter your email to reset</label>
            <input type="email" value={resetEmail} onChange={e => setResetEmail(e.target.value)} placeholder="you@example.com" required />
            <button type="submit" className="auth-btn-secondary">Send reset link</button>
          </form>
        )}
        {resetSent && <p className="auth-success" style={{textAlign:'center'}}>Reset link sent — check your inbox.</p>}
        <p className="auth-switch">Don't have an account? <button className="auth-link" onClick={onSwitchToRegister}>Create one</button></p>
      </div>
    </div>
  )
}

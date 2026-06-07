import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import './AuthModal.css'

export default function LoginModal({ onClose, onSwitchToRegister = null }) {
  const { login, requestPasswordReset } = useAuth()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [showReset, setShowReset] = useState(false)
  const [resetEmail, setResetEmail] = useState('')
  const [resetSent, setResetSent]   = useState(false)
  const [showPassword, setShowPassword] = useState(false)

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
          <div style={{position:'relative'}}>
            <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required autoComplete="current-password" style={{paddingRight:'2.2rem', width:'100%', boxSizing:'border-box'}} />
            <button type="button" onClick={() => setShowPassword(v => !v)} style={{position:'absolute', right:'0.5rem', top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', color:'var(--text3)', padding:'0', lineHeight:1}} tabIndex={-1} aria-label={showPassword ? 'Hide password' : 'Show password'}>
              {showPassword
                ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              }
            </button>
          </div>
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
        <p className="auth-switch">Don't have an account? <a className="auth-link" href="/pro">Get Pro access</a></p>
      </div>
    </div>
  )
}

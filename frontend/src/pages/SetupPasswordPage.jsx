import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './SetupPasswordPage.css'

export default function SetupPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const navigate = useNavigate()
  const { login } = useAuth()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)

  if (!token) return (
    <div className="setup-page">
      <div className="setup-inner">
        <h1>Invalid Link</h1>
        <p>This setup link is invalid or has expired.</p>
      </div>
    </div>
  )

  async function handleSubmit(e) {
    e.preventDefault()
    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    if (password !== confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/v1/auth/setup-password?token=${encodeURIComponent(token)}&password=${encodeURIComponent(password)}`, {
        method: 'POST',
        credentials: 'include',
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Setup failed')

      // Auto-login with returned token
      setDone(true)
      setTimeout(() => navigate('/'), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (done) return (
    <div className="setup-page">
      <div className="setup-inner">
        <h1>⛽ Welcome to Pumpr Pro!</h1>
        <p>Your password has been set. Redirecting you to the app…</p>
      </div>
    </div>
  )

  return (
    <div className="setup-page">
      <div className="setup-inner">
        <h1>⛽ Welcome to Pumpr!</h1>
        <p className="setup-sub">Set your password to complete your Pro account setup.</p>
        <form onSubmit={handleSubmit} className="setup-form">
          <label>Password
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              minLength={8}
              required
            />
          </label>
          <label>Confirm password
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat password"
              required
            />
          </label>
          {error && <p className="setup-error">{error}</p>}
          <button type="submit" className="setup-btn" disabled={loading}>
            {loading ? 'Setting up…' : 'Set password & go Pro →'}
          </button>
        </form>
      </div>
    </div>
  )
}

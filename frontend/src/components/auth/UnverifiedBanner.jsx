import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'

export default function UnverifiedBanner() {
  const { user, accessToken } = useAuth()
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  if (!user || user.is_verified) return null

  async function handleResend() {
    setLoading(true)
    try {
      await fetch('/api/v1/auth/resend-verification', {
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      setSent(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="unverified-banner">
      📧 Please verify your email address to access all features.
      {sent ? (
        <span> Verification email sent — check your inbox.</span>
      ) : (
        <button onClick={handleResend} disabled={loading}>
          {loading ? 'Sending…' : 'Resend verification email'}
        </button>
      )}
    </div>
  )
}

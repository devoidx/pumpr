import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './ProfilePage.css'

export default function ProfilePage() {
  const { user, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const isPro = user?.role === 'pro' || user?.role === 'admin'

  useEffect(() => {
    if (!loading && !isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  return (
    <div className="profile-page">
      <div className="profile-inner">
        <h1 className="profile-title">My Profile</h1>

        <div className="profile-section">
          <h2>Account</h2>
          <div className="profile-info-row"><span>Email</span><strong>{user?.email}</strong></div>
          <div className="profile-info-row"><span>Username</span><strong>{user?.username}</strong></div>
          <div className="profile-info-row">
            <span>Plan</span>
            <strong style={{ color: isPro ? 'var(--amber)' : 'var(--text2)' }}>
              {isPro ? '⚡ Pro' : 'Free'}
            </strong>
          </div>
          {user?.subscription_status === 'canceling' && (
            <p className="profile-warn">Your subscription will cancel at the end of the current period.</p>
          )}
          {!isPro && (
            <a href="/pro" className="profile-upgrade-btn">Upgrade to Pro →</a>
          )}
        </div>

        <div className="profile-section">
          <h2>Actions</h2>
          <div style={{display:'flex', flexDirection:'column', gap:'0.5rem'}}>
            <a href="/my-places" className="profile-upgrade-btn" style={{textAlign:'center'}}>📍 My Places →</a>
          </div>
        </div>
      </div>
    </div>
  )
}

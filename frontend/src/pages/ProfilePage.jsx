import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './ProfilePage.css'

export default function ProfilePage() {
  const { user, isAuthenticated, loading, updateProfile, accessToken } = useAuth()
  const [subLoading, setSubLoading] = useState(false)
  const [subMsg, setSubMsg] = useState(null)
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

        {isPro && (
          <div className="profile-section">
            <h2>Preferences</h2>
            <div className="profile-info-row">
              <span>
                <strong style={{color:'var(--text)'}}>Driving distance</strong>
                <div style={{fontSize:'0.78rem',color:'var(--text3)',marginTop:'2px'}}>
                  Show real driving distance for top 10 results instead of straight-line
                </div>
              </span>
              <label className="profile-toggle">
                <input
                  type="checkbox"
                  checked={user?.use_driving_distance || false}
                  onChange={async e => {
                    try { await updateProfile({ use_driving_distance: e.target.checked }) }
                    catch { alert('Failed to save preference') }
                  }}
                />
                <span className="profile-toggle-slider" />
              </label>
            </div>
            <div className="profile-info-row">
              <span>
                <strong style={{color:'var(--text)'}}>Fuel economy units</strong>
                <div style={{fontSize:'0.78rem',color:'var(--text3)',marginTop:'2px'}}>
                  Units used for economy figures and savings calculations. Only applies when you have an active vehicle set.
                </div>
              </span>
              <select
                className="profile-select"
                value={user?.economy_units || 'mpg'}
                onChange={async e => {
                  try { await updateProfile({ economy_units: e.target.value }) }
                  catch { alert('Failed to save preference') }
                }}
              >
                <option value="mpg">MPG</option>
                <option value="l100km">L/100km</option>
              </select>
            </div>
          </div>
        )}

        {isPro && (
          <div className="profile-section">
            <h2>Subscription</h2>
            <div className="profile-info-row">
              <span>Plan</span>
              <strong style={{color:'var(--amber)'}}>
                {user?.price_id === 'price_1TU6vtFThYVN7wEdDTNWtnKe' ? 'Monthly' : 'Annual'}
              </strong>
            </div>
            <div className="profile-info-row">
              <span>Status</span>
              <strong style={{color: user?.subscription_status === 'active' ? 'var(--green)' : 'var(--amber)'}}>
                {user?.subscription_status === 'active' ? 'Active' :
                 user?.subscription_status === 'canceling' ? 'Cancels at period end' :
                 user?.subscription_status === 'past_due' ? 'Past due' : 'Inactive'}
              </strong>
            </div>
            {user?.current_period_end && (
              <div className="profile-info-row">
                <span>{user?.subscription_status === 'canceling' ? 'Access until' : 'Renews'}</span>
                <strong>{new Date(user.current_period_end).toLocaleDateString('en-GB', {day:'numeric', month:'long', year:'numeric'})}</strong>
              </div>
            )}
            {subMsg && <p style={{fontSize:'0.8rem', color:'var(--text2)', margin:'8px 0 0'}}>{subMsg}</p>}
            <div style={{marginTop:'12px', display:'flex', gap:'8px'}}>
              {user?.subscription_status === 'active' && (
                <button
                  className="profile-danger-btn"
                  disabled={subLoading}
                  onClick={async () => {
                    setSubLoading(true); setSubMsg(null)
                    try {
                      const r = await fetch('/api/v1/stripe/cancel', {method:'POST', headers:{Authorization:}})
                      await updateProfile({subscription_status:'canceling'})
                      setSubMsg('Subscription will cancel at the end of the current period.')
                    } catch { setSubMsg('Something went wrong. Please try again.') }
                    finally { setSubLoading(false) }
                  }}
                >{subLoading ? 'Cancelling…' : 'Cancel subscription'}</button>
              )}
              {user?.subscription_status === 'canceling' && (
                <button
                  className="profile-upgrade-btn"
                  disabled={subLoading}
                  onClick={async () => {
                    setSubLoading(true); setSubMsg(null)
                    try {
                      const r = await fetch('/api/v1/stripe/resume', {method:'POST', headers:{Authorization:}})
                      await updateProfile({subscription_status:'active'})
                      setSubMsg('Subscription resumed successfully.')
                    } catch { setSubMsg('Something went wrong. Please try again.') }
                    finally { setSubLoading(false) }
                  }}
                >{subLoading ? 'Resuming…' : 'Resume subscription'}</button>
              )}
            </div>
          </div>
        )}
        {isPro && (
          <div className="profile-section">
            <h2>Subscription</h2>
            <div className="profile-info-row">
              <span>Plan</span>
              <strong style={{color:'var(--amber)'}}>
                {user?.price_id === 'price_1TU6vtFThYVN7wEdDTNWtnKe' ? 'Monthly' : 'Annual'}
              </strong>
            </div>
            <div className="profile-info-row">
              <span>Status</span>
              <strong style={{color: user?.subscription_status === 'active' ? 'var(--green)' : 'var(--amber)'}}>
                {user?.subscription_status === 'active' ? 'Active' :
                 user?.subscription_status === 'canceling' ? 'Cancels at period end' :
                 user?.subscription_status === 'past_due' ? 'Past due' : 'Inactive'}
              </strong>
            </div>
            {user?.current_period_end && (
              <div className="profile-info-row">
                <span>{user?.subscription_status === 'canceling' ? 'Access until' : 'Renews'}</span>
                <strong>{new Date(user.current_period_end).toLocaleDateString('en-GB', {day:'numeric', month:'long', year:'numeric'})}</strong>
              </div>
            )}
            {subMsg && <p style={{fontSize:'0.8rem', color:'var(--text2)', margin:'8px 0 0'}}>{subMsg}</p>}
            <div style={{marginTop:'12px', display:'flex', gap:'8px'}}>
              {user?.subscription_status === 'active' && (
                <button
                  className="profile-danger-btn"
                  disabled={subLoading}
                  onClick={async () => {
                    if (!window.confirm('Cancel your Pro subscription? You will keep access until the end of the current period.')) return
                    setSubLoading(true); setSubMsg(null)
                    try {
                      const r = await fetch('/api/v1/stripe/cancel', {method:'POST', headers:{Authorization:'Bearer ' + accessToken}})
                      if (!r.ok) throw new Error()
                      await updateProfile({subscription_status:'canceling'})
                      setSubMsg('Subscription will cancel at the end of the current period.')
                    } catch { setSubMsg('Something went wrong. Please try again.') }
                    finally { setSubLoading(false) }
                  }}
                >{subLoading ? 'Cancelling…' : 'Cancel subscription'}</button>
              )}
              {user?.subscription_status === 'canceling' && (
                <button
                  className="profile-upgrade-btn"
                  disabled={subLoading}
                  onClick={async () => {
                    setSubLoading(true); setSubMsg(null)
                    try {
                      const r = await fetch('/api/v1/stripe/resume', {method:'POST', headers:{Authorization:'Bearer ' + accessToken}})
                      if (!r.ok) throw new Error()
                      await updateProfile({subscription_status:'active'})
                      setSubMsg('Subscription resumed successfully.')
                    } catch { setSubMsg('Something went wrong. Please try again.') }
                    finally { setSubLoading(false) }
                  }}
                >{subLoading ? 'Resuming…' : 'Resume subscription'}</button>
              )}
            </div>
          </div>
        )}
        <div className="profile-section">
          <h2>Notifications</h2>
          <div className="profile-info-row">
            <span>
              <strong style={{color:'var(--text)'}}>Blog newsletter</strong>
              <div style={{fontSize:'0.78rem',color:'var(--text3)',marginTop:'2px'}}>
                Get an email when new fuel price insights are published
              </div>
            </span>
            <label className="profile-toggle">
              <input
                type="checkbox"
                checked={user?.blog_newsletter || false}
                onChange={async e => {
                  try { await updateProfile({ blog_newsletter: e.target.checked }) }
                  catch { alert('Failed to save preference') }
                }}
              />
              <span className="profile-toggle-slider" />
            </label>
          </div>
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

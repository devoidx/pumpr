import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function MyAlertsPage() {
  const { user, accessToken, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const isPro = user?.role === 'pro' || user?.role === 'admin'
  const [alerts, setAlerts] = useState([])
  const [fetching, setFetching] = useState(true)

  useEffect(() => { if (typeof umami !== 'undefined') umami.track('my-alerts-viewed') }, [])
  useEffect(() => {
    if (!loading && !isAuthenticated) navigate('/')
  }, [isAuthenticated, loading, navigate])

  useEffect(() => {
    if (!accessToken || !isPro) { setFetching(false); return }
    fetch('/api/v1/alerts/', { headers: { Authorization: 'Bearer ' + accessToken } })
      .then(r => r.ok ? r.json() : [])
      .then(data => { setAlerts(data); setFetching(false) })
      .catch(() => setFetching(false))
  }, [accessToken, isPro])

  const handleToggle = async (id) => {
    const r = await fetch('/api/v1/alerts/' + id + '/toggle', {
      method: 'PATCH', headers: { Authorization: 'Bearer ' + accessToken }
    })
    if (r.ok) setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_active: !a.is_active } : a))
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this alert?')) return
    const r = await fetch('/api/v1/alerts/' + id, {
      method: 'DELETE', headers: { Authorization: 'Bearer ' + accessToken }
    })
    if (r.ok) setAlerts(prev => prev.filter(a => a.id !== id))
  }

  if (loading || fetching) return <div style={{padding:'40px', color:'var(--text2)'}}>Loading...</div>

  if (!isPro) return (
    <div style={{padding:'40px', maxWidth:'480px', margin:'0 auto', textAlign:'center'}}>
      <h1 style={{color:'var(--amber)', marginBottom:'8px'}}>Price Alerts</h1>
      <p style={{color:'var(--text2)', marginBottom:'24px'}}>Price alerts are a Pro feature. Upgrade to get notified when fuel prices drop or change.</p>
      <a href="/pro" style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'12px 28px', borderRadius:'8px', textDecoration:'none'}}>Go Pro</a>
    </div>
  )

  return (
    <div style={{maxWidth:'640px', margin:'0 auto', padding:'24px 16px'}}>
      <h1 style={{color:'var(--text)', fontSize:'22px', marginBottom:'4px'}}>Price Alerts</h1>
      <p style={{color:'var(--text3)', fontSize:'13px', marginBottom:'24px'}}>
        Alerts fire once per 24 hours. Set them up from any station page.
      </p>

      {alerts.length === 0 ? (
        <div style={{textAlign:'center', padding:'48px 24px', color:'var(--text3)', fontSize:'14px'}}>
          <p>No alerts set up yet.</p>
          <p style={{marginTop:'8px', fontSize:'13px'}}>Visit a station page to add your first alert.</p>
        </div>
      ) : (
        <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
          {alerts.map(a => (
            <div key={a.id} style={{
              background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:'10px', padding:'14px 16px',
              opacity: a.is_active ? 1 : 0.55,
            }}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'12px'}}>
                <div>
                  <div style={{fontWeight:600, color:'var(--text)', fontSize:'14px', marginBottom:'2px'}}>
                    {a.station_name}
                  </div>
                  <div style={{fontSize:'13px', color:'var(--text2)'}}>
                    <strong>{a.fuel_type}</strong> -{' '}
                    {a.alert_type === 'below_pence'
                      ? 'notify when below ' + a.threshold.toFixed(1) + 'p'
                      : 'notify when price changes by >' + a.threshold.toFixed(1) + '%'}
                  </div>
                  <div style={{fontSize:'11px', color:'var(--text3)', marginTop:'4px', fontFamily:'var(--font-mono)'}}>
                    {a.triggered_count > 0
                      ? 'Triggered ' + a.triggered_count + 'x - last ' + new Date(a.last_triggered_at).toLocaleDateString('en-GB', {day:'numeric', month:'short'})
                      : 'Never triggered'}
                    {' - '}
                    {a.is_active ? 'Active' : 'Paused'}
                  </div>
                </div>
                <div style={{display:'flex', gap:'6px', flexShrink:0}}>
                  <button
                    onClick={() => navigate('/stations/' + a.station_id)}
                    style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px',
                      border:'1px solid var(--border2)', background:'var(--surface2)',
                      color:'var(--text2)', cursor:'pointer'}}
                  >View</button>
                  <button
                    onClick={() => handleToggle(a.id)}
                    style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px',
                      border:'1px solid var(--border2)', background:'var(--surface2)',
                      color:'var(--text2)', cursor:'pointer'}}
                  >{a.is_active ? 'Pause' : 'Resume'}</button>
                  <button
                    onClick={() => handleDelete(a.id)}
                    style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px',
                      border:'1px solid #e74c3c', background:'transparent',
                      color:'#e74c3c', cursor:'pointer'}}
                  >Delete</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

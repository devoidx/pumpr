import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import Portal from './Portal'

function ModalOverlay({ children, onClose }) {
  return (
    <Portal>
      <div
        style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', zIndex:10000, display:'flex', alignItems:'center', justifyContent:'center', padding:'16px'}}
        onClick={e => e.target === e.currentTarget && onClose()}
      >
        <div style={{background:'var(--bg)', border:'1px solid var(--border)', borderRadius:'16px', width:'100%', maxWidth:'560px', maxHeight:'90vh', display:'flex', flexDirection:'column', overflow:'hidden'}}>
          {children}
        </div>
      </div>
    </Portal>
  )
}

export default function MyAlertsModal({ onClose }) {
  const { user, accessToken } = useAuth()
  const isPro = user?.role === 'pro' || user?.role === 'admin'
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const headers = { Authorization: 'Bearer ' + accessToken }

  useEffect(() => {
    if (!isPro) { setLoading(false); return }
    fetch('/api/v1/alerts/', { headers })
      .then(r => r.ok ? r.json() : [])
      .then(data => { setAlerts(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [isPro])

  const handleToggle = async (id) => {
    const r = await fetch('/api/v1/alerts/' + id + '/toggle', { method: 'PATCH', headers })
    if (r.ok) setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_active: !a.is_active } : a))
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this alert?')) return
    const r = await fetch('/api/v1/alerts/' + id, { method: 'DELETE', headers })
    if (r.ok) setAlerts(prev => prev.filter(a => a.id !== id))
  }

  return (
    <ModalOverlay onClose={onClose}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border)', flexShrink:0}}>
        <div>
          <h2 style={{color:'var(--text)', fontSize:'18px', margin:0}}>Price Alerts</h2>
          <p style={{color:'var(--text3)', fontSize:'12px', margin:'2px 0 0', fontFamily:'var(--font-mono)'}}>Pro feature · alerts fire once per 24 hours</p>
        </div>
        <button onClick={onClose} style={{background:'none', border:'none', color:'var(--text2)', fontSize:'20px', cursor:'pointer'}}>X</button>
      </div>
      <div style={{flex:1, overflowY:'auto', padding:'20px'}}>
        {!isPro ? (
          <div style={{textAlign:'center', padding:'32px 0'}}>
            <p style={{color:'var(--text2)', marginBottom:'16px'}}>Price alerts are a Pro feature.</p>
            <a href="/pro" style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px 24px', borderRadius:'8px', textDecoration:'none'}}>Go Pro</a>
          </div>
        ) : loading ? (
          <p style={{color:'var(--text3)'}}>Loading...</p>
        ) : alerts.length === 0 ? (
          <div style={{textAlign:'center', padding:'32px 0', color:'var(--text3)', fontSize:'14px'}}>
            <p>No alerts set up yet.</p>
            <p style={{marginTop:'8px', fontSize:'13px'}}>Visit a station page to add your first alert.</p>
          </div>
        ) : (
          <>
          <div style={{background:'var(--surface2)', border:'1px solid var(--border)', borderRadius:'8px', padding:'10px 14px', marginBottom:'12px', fontSize:'12px', color:'var(--text3)'}}>
            To add new alerts, visit a station detail page and use the Price Alerts section.
          </div>
          <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
            {alerts.map(a => (
              <div key={a.id} style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'12px 14px', opacity: a.is_active ? 1 : 0.55}}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'12px'}}>
                  <div style={{minWidth:0}}>
                    <div style={{fontWeight:600, color:'var(--text)', fontSize:'14px', marginBottom:'2px', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>
                      {a.station_name}
                    </div>
                    <div style={{fontSize:'13px', color:'var(--text2)'}}>
                      {a.fuel_type} - {a.alert_type === 'below_pence' ? 'below ' + a.threshold.toFixed(1) + 'p' : 'change >' + a.threshold.toFixed(1) + '%'}
                    </div>
                    <div style={{fontSize:'11px', color:'var(--text3)', marginTop:'3px', fontFamily:'var(--font-mono)'}}>
                      {a.triggered_count > 0 ? 'Triggered ' + a.triggered_count + 'x' : 'Never triggered'} · {a.is_active ? 'Active' : 'Paused'}
                    </div>
                  </div>
                  <div style={{display:'flex', gap:'6px', flexShrink:0}}>
                    <button onClick={() => handleToggle(a.id)}
                      style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid var(--border2)', background:'var(--surface2)', color:'var(--text2)', cursor:'pointer'}}>
                      {a.is_active ? 'Pause' : 'Resume'}
                    </button>
                    <button onClick={() => handleDelete(a.id)}
                      style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid #e74c3c', background:'transparent', color:'#e74c3c', cursor:'pointer'}}>
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          </>
        )}
      </div>
    </ModalOverlay>
  )
}

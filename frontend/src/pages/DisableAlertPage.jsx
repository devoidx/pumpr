import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

export default function DisableAlertPage() {
  const location = useLocation()
  const token = new URLSearchParams(location.search).get('token')
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    if (!token) { setStatus('invalid'); return }
    fetch('/api/v1/alerts/disable?token=' + encodeURIComponent(token))
      .then(r => r.ok ? setStatus('success') : setStatus('error'))
      .catch(() => setStatus('error'))
  }, [token])

  const messages = {
    loading: { icon: '⏳', title: 'Disabling alert...', body: 'Please wait.' },
    success: { icon: '✅', title: 'Alert disabled', body: 'You will no longer receive emails for this alert. You can re-enable it any time from My Alerts.' },
    error:   { icon: '⚠️', title: 'Something went wrong', body: 'This link may have expired or already been used. Visit My Alerts to manage your alerts.' },
    invalid: { icon: '⚠️', title: 'Invalid link', body: 'This disable link is not valid.' },
  }

  const m = messages[status]

  return (
    <div style={{maxWidth:'480px', margin:'80px auto', padding:'0 16px', textAlign:'center'}}>
      <div style={{fontSize:'48px', marginBottom:'16px'}}>{m.icon}</div>
      <h1 style={{color:'var(--text)', fontSize:'22px', marginBottom:'8px'}}>{m.title}</h1>
      <p style={{color:'var(--text2)', fontSize:'14px', lineHeight:1.7, marginBottom:'24px'}}>{m.body}</p>
      <a href="/my-alerts" style={{background:'var(--amber)', color:'#000', fontWeight:700,
        padding:'10px 24px', borderRadius:'8px', textDecoration:'none', fontSize:'14px'}}>
        My Alerts
      </a>
    </div>
  )
}

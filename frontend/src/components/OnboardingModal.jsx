import Portal from './Portal'

const FEATURES = [
  {
    icon: '🚗',
    title: 'My Vehicles',
    desc: 'Add your vehicles and get personalised fuel cost estimates. DVLA lookup fills in the details automatically.',
    action: 'openVehicles',
    cta: 'Add a vehicle',
  },
  {
    icon: '📍',
    title: 'My Places',
    desc: 'Save home, work, or any location and jump straight to cheap fuel nearby with one tap.',
    action: 'openPlaces',
    cta: 'Save a place',
  },
  {
    icon: '🔔',
    title: 'Price Alerts',
    desc: 'Get emailed when your favourite station drops below a price threshold.',
    action: 'openAlerts',
    cta: 'Set an alert',
  },
  {
    icon: '⛽',
    title: 'Fuel Tracker',
    desc: 'Log every fill-up and track your spending, MPG vs spec, and monthly fuel costs over time.',
    action: 'openTracker',
    cta: 'Log a fill-up',
  },
]

export default function OnboardingModal({ onClose, openTracker, openPlaces, openAlerts, openVehicles }) {
  const handlers = { openTracker, openPlaces, openAlerts, openVehicles }

  return (
    <Portal>
      <div style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.7)',zIndex:10000,display:'flex',alignItems:'center',justifyContent:'center',padding:'16px'}}>
        <div style={{background:'var(--surface,#1a1a1a)',border:'1px solid var(--border,#2d2d2d)',borderRadius:'14px',padding:'28px 24px',maxWidth:'480px',width:'100%',maxHeight:'90vh',overflowY:'auto',position:'relative'}}>
          <button onClick={onClose} style={{position:'absolute',top:'14px',right:'16px',background:'none',border:'none',color:'var(--text3)',fontSize:'20px',cursor:'pointer',lineHeight:1}}>×</button>
          <div style={{textAlign:'center',marginBottom:'24px'}}>
            <div style={{fontSize:'28px',marginBottom:'8px'}}>⚡</div>
            <h2 style={{color:'var(--amber)',fontSize:'20px',fontWeight:700,margin:'0 0 6px'}}>Welcome to Pumpr Pro</h2>
            <p style={{color:'var(--text2)',fontSize:'13px',margin:0}}>Here's everything included in your subscription.</p>
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:'12px'}}>
            {FEATURES.map(f => (
              <div key={f.title} style={{background:'var(--bg,#111)',border:'1px solid var(--border,#2d2d2d)',borderRadius:'10px',padding:'14px 16px',display:'flex',gap:'14px',alignItems:'flex-start'}}>
                <span style={{fontSize:'22px',flexShrink:0,marginTop:'2px'}}>{f.icon}</span>
                <div style={{flex:1}}>
                  <div style={{fontWeight:700,color:'var(--text)',fontSize:'14px',marginBottom:'4px'}}>{f.title}</div>
                  <div style={{color:'var(--text2)',fontSize:'12px',lineHeight:1.5,marginBottom:'10px'}}>{f.desc}</div>
                  <button
                    onClick={handlers[f.action]}
                    style={{background:'rgba(245,158,11,0.12)',border:'1px solid rgba(245,158,11,0.3)',borderRadius:'6px',color:'var(--amber)',cursor:'pointer',fontSize:'12px',fontWeight:600,padding:'5px 12px'}}
                  >{f.cta} →</button>
                </div>
              </div>
            ))}
          </div>
          <div style={{marginTop:'20px',background:'rgba(245,158,11,0.07)',border:'1px solid rgba(245,158,11,0.2)',borderRadius:'8px',padding:'12px 14px',display:'flex',gap:'10px',alignItems:'center'}}>
            <span style={{fontSize:'18px',flexShrink:0}}>💡</span>
            <div style={{fontSize:'12px',color:'var(--text2)',lineHeight:1.5}}>
              You can return to this guide any time by clicking your{' '}
              <span style={{display:'inline-flex',alignItems:'center',gap:'3px',background:'rgba(245,158,11,0.1)',border:'1px solid rgba(245,158,11,0.3)',borderRadius:'12px',padding:'1px 8px',fontSize:'11px',fontWeight:600,color:'var(--amber)'}}>
                name <span style={{fontSize:'8px',fontWeight:700,background:'var(--amber)',color:'#000',borderRadius:'3px',padding:'1px 3px'}}>PRO</span>
              </span>{' '}
              button in the top right, then tap <strong style={{color:'var(--amber)'}}>⚡ Pro features</strong>.
            </div>
          </div>
          <button onClick={onClose} style={{marginTop:'12px',width:'100%',background:'var(--amber)',border:'none',borderRadius:'8px',color:'#000',cursor:'pointer',fontSize:'14px',fontWeight:700,padding:'11px'}}>Got it, let’s go!</button>
        </div>
      </div>
    </Portal>
  )
}

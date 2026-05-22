import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import Portal from './Portal'

function ModalOverlay({ children, onClose }) {
  return (
    <Portal>
      <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', zIndex:10000, display:'flex', alignItems:'center', justifyContent:'center', padding:'16px'}}
        onClick={e => e.target === e.currentTarget && onClose()}>
        <div style={{background:'var(--bg)', border:'1px solid var(--border)', borderRadius:'16px', width:'100%', maxWidth:'480px', maxHeight:'90vh', display:'flex', flexDirection:'column', overflow:'hidden'}}>
          {children}
        </div>
      </div>
    </Portal>
  )
}

export default function ProfileModal({ onClose }) {
  const { user, updateProfile, accessToken } = useAuth()
  const isPro = user?.role === 'pro' || user?.role === 'admin'
  const [subLoading, setSubLoading] = useState(false)
  const [subMsg, setSubMsg] = useState(null)
  const [editingName, setEditingName] = useState(false)
  const [nameVal, setNameVal] = useState(user?.username || '')
  const [nameError, setNameError] = useState('')

  async function saveName() {
    try {
      await updateProfile({ username: nameVal.trim() || null })
      setEditingName(false)
      setNameError('')
    } catch {
      setNameError('That name may already be taken.')
    }
  }

  const rowStyle = {display:'flex', alignItems:'center', justifyContent:'space-between', padding:'12px 0', borderBottom:'1px solid var(--border)'}
  const labelStyle = {fontSize:'14px', color:'var(--text)', fontWeight:500}
  const subLabelStyle = {fontSize:'12px', color:'var(--text3)', marginTop:'2px'}
  const sectionTitleStyle = {fontSize:'12px', color:'var(--text3)', fontFamily:'var(--font-mono)', fontWeight:700, letterSpacing:'0.05em', padding:'16px 0 8px', textTransform:'uppercase'}

  const Toggle = ({ checked, onChange }) => (
    <label style={{position:'relative', display:'inline-block', width:'44px', height:'24px', flexShrink:0}}>
      <input type="checkbox" checked={checked} onChange={onChange} style={{opacity:0, width:0, height:0}} />
      <span style={{position:'absolute', inset:0, background: checked ? 'var(--amber)' : 'var(--border2)',
        borderRadius:'24px', cursor:'pointer', transition:'0.2s'}} />
      <span style={{position:'absolute', top:'3px', left: checked ? '23px' : '3px', width:'18px', height:'18px',
        background:'#fff', borderRadius:'50%', transition:'0.2s'}} />
    </label>
  )

  return (
    <ModalOverlay onClose={onClose}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border)', flexShrink:0}}>
        <h2 style={{color:'var(--text)', fontSize:'18px', margin:0}}>My Profile</h2>
        <button onClick={onClose} style={{background:'none', border:'none', color:'var(--text2)', fontSize:'20px', cursor:'pointer'}}>✕</button>
      </div>

      <div style={{flex:1, overflowY:'auto', padding:'0 20px 20px'}}>

        {/* Account */}
        <div style={sectionTitleStyle}>Account</div>
        <div style={rowStyle}>
          <div><div style={labelStyle}>Email</div></div>
          <div style={{fontSize:'13px', color:'var(--text2)', fontFamily:'var(--font-mono)'}}>{user?.email}</div>
        </div>
        <div style={rowStyle}>
          <div><div style={labelStyle}>Name</div></div>
          {editingName ? (
            <div style={{display:'flex',flexDirection:'column',gap:'4px',alignItems:'flex-end'}}>
              <div style={{display:'flex',gap:'6px'}}>
                <input value={nameVal} onChange={e => setNameVal(e.target.value)} onKeyDown={e => e.key === 'Enter' && saveName()} placeholder="Your name" style={{background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'6px',color:'var(--text)',fontSize:'13px',padding:'4px 8px',outline:'none',width:'130px'}} />
                <button onClick={saveName} style={{background:'var(--amber)',border:'none',borderRadius:'6px',color:'#000',cursor:'pointer',fontSize:'12px',fontWeight:700,padding:'4px 10px'}}>Save</button>
                <button onClick={() => { setEditingName(false); setNameError('') }} style={{background:'none',border:'1px solid var(--border)',borderRadius:'6px',color:'var(--text3)',cursor:'pointer',fontSize:'12px',padding:'4px 8px'}}>Cancel</button>
              </div>
              {nameError && <div style={{fontSize:'11px',color:'#e74c3c'}}>{nameError}</div>}
            </div>
          ) : (
            <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
              <span style={{fontSize:'13px',color:'var(--text2)'}}>{user?.username || '—'}</span>
              <button onClick={() => { setNameVal(user?.username || ''); setEditingName(true) }} style={{background:'none',border:'none',color:'var(--text3)',cursor:'pointer',fontSize:'11px',textDecoration:'underline',padding:0}}>Edit</button>
            </div>
          )}
        </div>
        <div style={{...rowStyle, borderBottom:'none'}}>
          <div><div style={labelStyle}>Plan</div></div>
          <div style={{fontSize:'13px', fontWeight:700, color: isPro ? 'var(--amber)' : 'var(--text2)'}}>
            {isPro ? 'Pro' : 'Free'}
          </div>
        </div>
        {!isPro && (
          <a href="/pro" onClick={onClose} style={{display:'block', textAlign:'center', padding:'8px', background:'var(--amber)', color:'#000', fontWeight:700, borderRadius:'8px', textDecoration:'none', fontSize:'13px', marginBottom:'8px'}}>
            Upgrade to Pro →
          </a>
        )}

        {/* Subscription */}
        {isPro && (
          <>
            <div style={sectionTitleStyle}>Subscription</div>
            <div style={rowStyle}>
              <div><div style={labelStyle}>Plan</div></div>
              <div style={{fontSize:'13px', color:'var(--text2)'}}>
                {user?.price_id === 'price_1TU6vtFThYVN7wEdDTNWtnKe' ? 'Monthly' : 'Annual'}
              </div>
            </div>
            <div style={rowStyle}>
              <div><div style={labelStyle}>Status</div></div>
              <div style={{fontSize:'13px', fontWeight:600, color: user?.subscription_status === 'active' ? '#2ecc71' : 'var(--amber)'}}>
                {user?.subscription_status === 'active' ? 'Active' :
                 user?.subscription_status === 'canceling' ? 'Cancels at period end' :
                 user?.subscription_status === 'past_due' ? 'Past due' : 'Inactive'}
              </div>
            </div>
            {user?.current_period_end && (
              <div style={rowStyle}>
                <div><div style={labelStyle}>{user?.subscription_status === 'canceling' ? 'Access until' : 'Renews'}</div></div>
                <div style={{fontSize:'13px', color:'var(--text2)'}}>
                  {new Date(user.current_period_end).toLocaleDateString('en-GB', {day:'numeric', month:'long', year:'numeric'})}
                </div>
              </div>
            )}
            {subMsg && <p style={{fontSize:'12px', color:'var(--text3)', margin:'4px 0'}}>{subMsg}</p>}
            <div style={{padding:'8px 0', borderBottom:'1px solid var(--border)'}}>
              {user?.subscription_status === 'active' && (
                <button disabled={subLoading} onClick={async () => {
                  if (!window.confirm('Cancel your Pro subscription? You will keep access until the end of the current period.')) return
                  setSubLoading(true); setSubMsg(null)
                  try {
                    const r = await fetch('/api/v1/stripe/cancel', {method:'POST', headers:{Authorization:'Bearer ' + accessToken}})
                    const data = await r.json()
                    if (!r.ok) throw new Error(data.detail || 'Request failed')
                    await updateProfile({subscription_status:'canceling'})
                    setSubMsg('Subscription will cancel at the end of the current period.')
                  } catch(e) { setSubMsg('Error: ' + e.message) }
                  finally { setSubLoading(false) }
                }} style={{fontSize:'12px', padding:'6px 14px', borderRadius:'6px', border:'1px solid #e74c3c', background:'transparent', color:'#e74c3c', cursor:'pointer'}}>
                  {subLoading ? 'Cancelling...' : 'Cancel subscription'}
                </button>
              )}
              {user?.subscription_status === 'canceling' && (
                <button disabled={subLoading} onClick={async () => {
                  setSubLoading(true); setSubMsg(null)
                  try {
                    const r = await fetch('/api/v1/stripe/resume', {method:'POST', headers:{Authorization:'Bearer ' + accessToken}})
                    if (!r.ok) throw new Error()
                    await updateProfile({subscription_status:'active'})
                    setSubMsg('Subscription resumed.')
                  } catch { setSubMsg('Something went wrong.') }
                  finally { setSubLoading(false) }
                }} style={{fontSize:'12px', padding:'6px 14px', borderRadius:'6px', border:'1px solid var(--amber)', background:'rgba(245,166,35,0.1)', color:'var(--amber)', cursor:'pointer'}}>
                  {subLoading ? 'Resuming...' : 'Resume subscription'}
                </button>
              )}
            </div>
          </>
        )}

        {/* Preferences */}
        {isPro && (
          <>
            <div style={sectionTitleStyle}>Preferences</div>
            <div style={rowStyle}>
              <div>
                <div style={labelStyle}>Driving distance</div>
                <div style={subLabelStyle}>Show real driving distance for top 10 results</div>
              </div>
              <Toggle checked={user?.use_driving_distance || false} onChange={async e => {
                try { await updateProfile({ use_driving_distance: e.target.checked }) }
                catch { alert('Failed to save') }
              }} />
            </div>
            <div style={rowStyle}>
              <div>
                <div style={labelStyle}>Fuel economy units</div>
                <div style={subLabelStyle}>Only applies when you have an active vehicle</div>
              </div>
              <select value={user?.economy_units || 'mpg'} onChange={async e => {
                try { await updateProfile({ economy_units: e.target.value }) }
                catch { alert('Failed to save') }
              }} style={{background:'var(--surface2)', border:'1px solid var(--border2)', color:'var(--text)', padding:'6px 10px', borderRadius:'6px', fontSize:'13px'}}>
                <option value="mpg">MPG</option>
                <option value="l100km">L/100km</option>
              </select>
            </div>
          </>
        )}

        {/* Notifications */}
        <div style={sectionTitleStyle}>Notifications</div>
        <div style={{...rowStyle, borderBottom:'none'}}>
          <div>
            <div style={labelStyle}>Blog newsletter</div>
            <div style={subLabelStyle}>Email when new fuel price insights are published</div>
          </div>
          <Toggle checked={user?.blog_newsletter || false} onChange={async e => {
            try { await updateProfile({ blog_newsletter: e.target.checked }) }
            catch { alert('Failed to save') }
          }} />
        </div>
        <div style={{...rowStyle, borderBottom:'none', marginTop:'12px'}}>
          <div>
            <div style={labelStyle}>Monthly spending digest</div>
            <div style={subLabelStyle}>Requires fuel tracker usage — monthly summary per vehicle, sent on the 1st</div>
          </div>
          <Toggle checked={user?.spending_digest || false} onChange={async e => {
            try { await updateProfile({ spending_digest: e.target.checked }) }
            catch { alert('Failed to save') }
          }} />
        </div>
      </div>
    </ModalOverlay>
  )
}

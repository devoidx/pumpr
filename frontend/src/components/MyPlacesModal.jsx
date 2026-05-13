import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import Portal from './Portal'

const TYPE_ICON  = { home: '🏠', work: '🏢', custom: '📍' }
const TYPE_LABEL = { home: 'Home', work: 'Work', custom: 'Custom' }

function ModalOverlay({ children, onClose }) {
  return (
    <Portal>
      <div
        style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', zIndex:10000, display:'flex', alignItems:'center', justifyContent:'center', padding:'16px'}}
        onClick={e => e.target === e.currentTarget && onClose()}
      >
        <div style={{background:'var(--bg)', border:'1px solid var(--border)', borderRadius:'16px', width:'100%', maxWidth:'520px', maxHeight:'90vh', display:'flex', flexDirection:'column', overflow:'hidden'}}>
          {children}
        </div>
      </div>
    </Portal>
  )
}

function LocationForm({ existing, existingTypes, authFetch, onSave, onClose }) {
  const [label, setLabel] = useState(existing?.label || '')
  const [type, setType] = useState(existing?.type || 'custom')
  const [postcode, setPostcode] = useState(existing?.postcode || '')
  const [lat, setLat] = useState(existing?.lat || null)
  const [lng, setLng] = useState(existing?.lng || null)
  const [hasCharger, setHasCharger] = useState(existing?.has_home_charger || false)
  const [lookingUp, setLookingUp] = useState(false)
  const [postcodeErr, setPostcodeErr] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!existing && type !== 'custom') setLabel(type.charAt(0).toUpperCase() + type.slice(1))
  }, [type, existing])

  async function lookupPostcode() {
    const clean = postcode.trim().replace(/\s+/g, '').toUpperCase()
    if (!clean) return
    setLookingUp(true); setPostcodeErr('')
    try {
      const res = await fetch(`https://api.postcodes.io/postcodes/${clean}`)
      const data = await res.json()
      if (data.status === 200) {
        setLat(data.result.latitude); setLng(data.result.longitude)
        setPostcode(data.result.postcode); setPostcodeErr('')
      } else { setPostcodeErr('Postcode not found') }
    } catch { setPostcodeErr('Lookup failed') }
    finally { setLookingUp(false) }
  }

  async function handleSave(e) {
    e.preventDefault()
    if (!lat || !lng) { setError('Please look up a postcode first'); return }
    setSaving(true); setError('')
    try {
      const method = existing ? 'PATCH' : 'POST'
      const url = existing ? `/api/v1/locations/${existing.id}` : '/api/v1/locations'
      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label, type, lat, lng, postcode, has_home_charger: hasCharger }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Save failed')
      onSave(data)
    } catch(err) { setError(err.message) }
    finally { setSaving(false) }
  }

  const takenTypes = existingTypes.filter(t => t !== existing?.type)
  const inputStyle = {background:'var(--surface2)', border:'1px solid var(--border2)', color:'var(--text)', padding:'8px 10px', borderRadius:'8px', fontSize:'13px', width:'100%', boxSizing:'border-box'}

  return (
    <form onSubmit={handleSave} style={{display:'flex', flexDirection:'column', gap:'12px'}}>
      {error && <p style={{color:'#e74c3c', fontSize:'12px', margin:0}}>{error}</p>}
      <div>
        <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'6px'}}>Type</div>
        <div style={{display:'flex', gap:'8px'}}>
          {['home','work','custom'].map(t => (
            <button key={t} type="button"
              onClick={() => !takenTypes.includes(t) && setType(t)}
              disabled={takenTypes.includes(t) && t !== 'custom'}
              style={{flex:1, padding:'8px', borderRadius:'8px', border:'1px solid',
                borderColor: type === t ? 'var(--amber)' : 'var(--border2)',
                background: type === t ? 'rgba(245,166,35,0.15)' : 'var(--surface2)',
                color: type === t ? 'var(--amber)' : takenTypes.includes(t) ? 'var(--text3)' : 'var(--text2)',
                cursor: takenTypes.includes(t) && t !== 'custom' ? 'not-allowed' : 'pointer',
                fontSize:'13px', opacity: takenTypes.includes(t) && t !== 'custom' ? 0.4 : 1,
              }}>
              {TYPE_ICON[t]} {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>Label</div>
        <input type="text" value={label} onChange={e => setLabel(e.target.value)}
          placeholder={type === 'custom' ? "e.g. Mum's house" : type.charAt(0).toUpperCase() + type.slice(1)}
          maxLength={50} required style={inputStyle} />
      </div>
      <div>
        <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>Postcode</div>
        <div style={{display:'flex', gap:'8px'}}>
          <input type="text" value={postcode} onChange={e => { setPostcode(e.target.value); setLat(null); setLng(null) }}
            placeholder="e.g. PE27 5EU" maxLength={8} style={{...inputStyle, flex:1}} />
          <button type="button" onClick={lookupPostcode} disabled={lookingUp || !postcode.trim()}
            style={{padding:'8px 14px', borderRadius:'8px', border:'1px solid var(--border2)',
              background:'var(--surface2)', color:'var(--text2)', cursor:'pointer', fontSize:'13px', flexShrink:0}}>
            {lookingUp ? '…' : 'Look up'}
          </button>
        </div>
        {postcodeErr && <p style={{color:'#e74c3c', fontSize:'11px', margin:'4px 0 0'}}>{postcodeErr}</p>}
        {lat && lng && <p style={{color:'#2ecc71', fontSize:'11px', margin:'4px 0 0'}}>✓ Located</p>}
      </div>
      {type === 'home' && (
        <label style={{display:'flex', alignItems:'center', gap:'8px', fontSize:'13px', color:'var(--text2)', cursor:'pointer'}}>
          <input type="checkbox" checked={hasCharger} onChange={e => setHasCharger(e.target.checked)} />
          I have a home EV charger
        </label>
      )}
      <button type="submit" disabled={saving || !lat || !lng}
        style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px', borderRadius:'8px', border:'none', cursor:'pointer', fontSize:'14px', opacity: saving || !lat || !lng ? 0.6 : 1}}>
        {saving ? 'Saving…' : existing ? 'Save changes' : 'Add location'}
      </button>
    </form>
  )
}

export default function MyPlacesModal({ onClose, onSelectLocation }) {
  const { user, authFetch } = useAuth()
  const isPro = user?.role === 'pro' || user?.role === 'admin'
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const [editTarget, setEditTarget] = useState(null)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    if (!isPro) { setLoading(false); return }
    authFetch('/api/v1/locations')
      .then(r => r.json())
      .then(data => { setLocations(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [isPro])

  async function deleteLocation(id) {
    await authFetch(`/api/v1/locations/${id}`, { method: 'DELETE' })
    setLocations(l => l.filter(x => x.id !== id))
  }

  return (
    <ModalOverlay onClose={onClose}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border)', flexShrink:0}}>
        <h2 style={{color:'var(--text)', fontSize:'18px', margin:0}}>📍 My Places</h2>
        <button onClick={onClose} style={{background:'none', border:'none', color:'var(--text2)', fontSize:'20px', cursor:'pointer'}}>✕</button>
      </div>

      <div style={{flex:1, overflowY:'auto', padding:'20px'}}>
        {!isPro ? (
          <div style={{textAlign:'center', padding:'32px 0'}}>
            <p style={{color:'var(--text2)', marginBottom:'16px'}}>Saved locations are a Pro feature.</p>
            <a href="/pro" style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px 24px', borderRadius:'8px', textDecoration:'none'}}>Go Pro →</a>
          </div>
        ) : showForm ? (
          <div>
            <button onClick={() => { setShowForm(false); setEditTarget(null) }}
              style={{background:'none', border:'none', color:'var(--text3)', cursor:'pointer', fontSize:'13px', marginBottom:'16px', padding:0}}>
              ← Back
            </button>
            <h3 style={{color:'var(--text)', fontSize:'15px', marginBottom:'16px'}}>{editTarget ? 'Edit location' : 'Add location'}</h3>
            <LocationForm
              existing={editTarget}
              existingTypes={locations.map(l => l.type)}
              authFetch={authFetch}
              onSave={loc => {
                if (editTarget) setLocations(l => l.map(x => x.id === loc.id ? loc : x))
                else setLocations(l => [...l, loc])
                setShowForm(false); setEditTarget(null)
              }}
              onClose={() => { setShowForm(false); setEditTarget(null) }}
            />
          </div>
        ) : loading ? (
          <p style={{color:'var(--text3)'}}>Loading…</p>
        ) : (
          <div>
            {locations.length === 0 ? (
              <p style={{color:'var(--text3)', textAlign:'center', padding:'24px 0', fontSize:'14px'}}>
                No saved locations yet. Add your home or work to jump straight to local prices.
              </p>
            ) : (
              <div style={{display:'flex', flexDirection:'column', gap:'8px', marginBottom:'16px'}}>
                {locations.map(loc => (
                  <div key={loc.id} style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'12px 14px', display:'flex', alignItems:'center', gap:'12px'}}>
                    <span style={{fontSize:'20px', flexShrink:0}}>{TYPE_ICON[loc.type]}</span>
                    <div style={{flex:1, minWidth:0}}>
                      <div style={{fontWeight:600, color:'var(--text)', fontSize:'14px'}}>{loc.label}</div>
                      <div style={{fontSize:'12px', color:'var(--text3)'}}>
                        {TYPE_LABEL[loc.type]}{loc.postcode && ` · ${loc.postcode}`}
                        {loc.has_home_charger && ' · 🔌 Home charger'}
                      </div>
                    </div>
                    <div style={{display:'flex', gap:'6px', flexShrink:0}}>
                      {onSelectLocation && (
                        <button onClick={() => { onSelectLocation({lat: loc.lat, lng: loc.lng, postcode: loc.postcode}); onClose() }}
                          style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid var(--amber)', background:'rgba(245,166,35,0.1)', color:'var(--amber)', cursor:'pointer', fontWeight:700}}>
                          Go
                        </button>
                      )}
                      <button onClick={() => { setEditTarget(loc); setShowForm(true) }}
                        style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid var(--border2)', background:'var(--surface2)', color:'var(--text2)', cursor:'pointer'}}>Edit</button>
                      <button onClick={() => deleteLocation(loc.id)}
                        style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid #e74c3c', background:'transparent', color:'#e74c3c', cursor:'pointer'}}>Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {locations.length < 10 && (
              <button onClick={() => { setEditTarget(null); setShowForm(true) }}
                style={{width:'100%', padding:'10px', borderRadius:'8px', border:'1px dashed var(--border2)', background:'transparent', color:'var(--text3)', cursor:'pointer', fontSize:'13px'}}>
                + Add location
              </button>
            )}
          </div>
        )}
      </div>
    </ModalOverlay>
  )
}

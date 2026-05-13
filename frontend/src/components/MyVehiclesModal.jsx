import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import Portal from './Portal'

const FUEL_LABELS = {
  PETROL: 'Petrol', DIESEL: 'Diesel', ELECTRIC: 'Electric',
  'HYBRID ELECTRIC': 'Hybrid', 'PLUG-IN HYBRID ELECTRIC': 'Plug-in Hybrid',
}

const FUEL_DEFAULTS = {
  PETROL: { tank_litres: 50, mpg: 45 },
  DIESEL: { tank_litres: 60, mpg: 55 },
  ELECTRIC: { tank_litres: null, mpg: null, miles_per_kwh: 3.5 },
  'HYBRID ELECTRIC': { tank_litres: 45, mpg: 60 },
  'PLUG-IN HYBRID ELECTRIC': { tank_litres: 45, mpg: 50 },
}

function ModalOverlay({ children, onClose }) {
  return (
    <Portal>
      <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', zIndex:10000, display:'flex', alignItems:'center', justifyContent:'center', padding:'16px'}}
        onClick={e => e.target === e.currentTarget && onClose()}>
        <div style={{background:'var(--bg)', border:'1px solid var(--border)', borderRadius:'16px', width:'100%', maxWidth:'560px', maxHeight:'90vh', display:'flex', flexDirection:'column', overflow:'hidden'}}>
          {children}
        </div>
      </div>
    </Portal>
  )
}

function VehicleForm({ initial, onSave, onCancel, accessToken }) {
  const [reg, setReg] = useState(initial?.registration || '')
  const [form, setForm] = useState(initial || {})
  const [looking, setLooking] = useState(false)
  const [looked, setLooked] = useState(!!initial)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [lookupSource, setLookupSource] = useState(null)
  const isEV = form.fuel_type === 'ELECTRIC'

  async function lookup() {
    if (!reg.trim()) return
    setLooking(true); setError(null)
    try {
      const res = await fetch(`/api/v1/vehicles/lookup/${reg.trim().toUpperCase().replace(/\s/g, '')}`, {
        headers: { Authorization: 'Bearer ' + accessToken }
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Lookup failed')
      const defaults = FUEL_DEFAULTS[data.fuel_type?.toUpperCase()] || {}
      setForm(f => ({...f, registration: data.registration, make: data.make || '', model: data.model || '',
        year: data.year || '', colour: data.colour || '', fuel_type: data.fuel_type || 'PETROL',
        tank_litres: data.tank_litres ?? defaults.tank_litres ?? 50,
        mpg: data.mpg ?? defaults.mpg ?? 45,
        miles_per_kwh: data.miles_per_kwh ?? defaults.miles_per_kwh ?? null,
      }))
      setLookupSource(data.source || null); setLooked(true)
    } catch(e) { setError(e.message) }
    finally { setLooking(false) }
  }

  function set(field, val) {
    setForm(f => {
      const next = {...f, [field]: val}
      if (field === 'fuel_type') {
        const d = FUEL_DEFAULTS[val?.toUpperCase()] || {}
        next.tank_litres = d.tank_litres ?? f.tank_litres
        next.mpg = d.mpg ?? f.mpg
        next.miles_per_kwh = d.miles_per_kwh ?? f.miles_per_kwh
      }
      return next
    })
  }

  async function handleSave() {
    setSaving(true); setError(null)
    try {
      await onSave({
        registration: (form.registration || reg).toUpperCase().replace(/\s/g, ''),
        nickname: form.nickname || null, make: form.make || null, model: form.model || null,
        year: form.year ? parseInt(form.year) : null, colour: form.colour || null,
        fuel_type: form.fuel_type || 'PETROL',
        tank_litres: form.tank_litres ? parseFloat(form.tank_litres) : null,
        mpg: form.mpg ? parseFloat(form.mpg) : null,
        miles_per_kwh: form.miles_per_kwh ? parseFloat(form.miles_per_kwh) : null,
      })
    } catch(e) { setError(e.message); setSaving(false) }
  }

  const inputStyle = {background:'var(--surface2)', border:'1px solid var(--border2)', color:'var(--text)', padding:'8px 10px', borderRadius:'8px', fontSize:'13px', width:'100%', boxSizing:'border-box'}

  return (
    <div style={{display:'flex', flexDirection:'column', gap:'12px'}}>
      <div style={{display:'flex', alignItems:'center', gap:'8px', marginBottom:'4px'}}>
        <button onClick={onCancel} style={{background:'none', border:'none', color:'var(--text3)', cursor:'pointer', fontSize:'13px', padding:0}}>← Back</button>
        <span style={{color:'var(--text)', fontSize:'15px', fontWeight:700}}>{initial ? 'Edit Vehicle' : 'Add Vehicle'}</span>
      </div>
      {!initial && (
        <div style={{display:'flex', gap:'8px'}}>
          <input placeholder="Registration e.g. AB12 CDE" value={reg} onChange={e => setReg(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && lookup()} style={{...inputStyle, flex:1}} />
          <button onClick={lookup} disabled={looking}
            style={{padding:'8px 14px', borderRadius:'8px', border:'none', background:'var(--amber)', color:'#000', fontWeight:700, cursor:'pointer', flexShrink:0}}>
            {looking ? '...' : 'Look up'}
          </button>
        </div>
      )}
      {looked && (
        <>
          {lookupSource === 'dvla' && (
            <div style={{background:'var(--surface2)', border:'1px solid var(--border)', borderRadius:'8px', padding:'10px', fontSize:'11px', color:'var(--text3)'}}>
              Make, year, colour and fuel type from DVLA. Please enter model manually and update economy figures.
            </div>
          )}
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'10px'}}>
            {[
              {label:'Nickname', field:'nickname', placeholder:'"My Golf"'},
              {label:'Make', field:'make', placeholder:'e.g. Volkswagen'},
              {label:'Model', field:'model', placeholder:'e.g. Golf'},
              {label:'Year', field:'year', placeholder:'e.g. 2020', type:'number'},
              {label:'Colour', field:'colour', placeholder:'e.g. Blue'},
            ].map(f => (
              <div key={f.field}>
                <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>{f.label}</div>
                <input type={f.type || 'text'} placeholder={f.placeholder} value={form[f.field] || ''}
                  onChange={e => set(f.field, e.target.value)} style={inputStyle} />
              </div>
            ))}
            <div>
              <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>Fuel type</div>
              <select value={form.fuel_type || 'PETROL'} onChange={e => set('fuel_type', e.target.value)} style={inputStyle}>
                {Object.entries(FUEL_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          </div>
          {!isEV && (
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'10px'}}>
              <div>
                <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>Tank size (litres)</div>
                <input type="number" min="10" max="150" value={form.tank_litres || ''} onChange={e => set('tank_litres', e.target.value)} style={inputStyle} />
              </div>
              <div>
                <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>Fuel economy (MPG)</div>
                <input type="number" min="10" max="200" value={form.mpg || ''} onChange={e => set('mpg', e.target.value)} style={inputStyle} />
              </div>
            </div>
          )}
          {isEV && (
            <div>
              <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>Efficiency (miles/kWh)</div>
              <input type="number" min="1" max="10" step="0.1" value={form.miles_per_kwh || ''} onChange={e => set('miles_per_kwh', e.target.value)} style={inputStyle} />
            </div>
          )}
          {error && <p style={{color:'#e74c3c', fontSize:'12px', margin:0}}>{error}</p>}
          <button onClick={handleSave} disabled={saving}
            style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px', borderRadius:'8px', border:'none', cursor:'pointer', fontSize:'14px', opacity: saving ? 0.6 : 1}}>
            {saving ? 'Saving...' : 'Save vehicle'}
          </button>
        </>
      )}
      {!looked && error && <p style={{color:'#e74c3c', fontSize:'12px', margin:0}}>{error}</p>}
    </div>
  )
}

export default function MyVehiclesModal({ onClose }) {
  const { accessToken } = useAuth()
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(null)

  const headers = { Authorization: 'Bearer ' + accessToken }

  async function load() {
    fetch('/api/v1/vehicles', { headers })
      .then(r => r.ok ? r.json() : [])
      .then(data => { setVehicles(data); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleSave(body) {
    const url = editing ? `/api/v1/vehicles/${editing.id}` : '/api/v1/vehicles'
    const method = editing ? 'PUT' : 'POST'
    const res = await fetch(url, { method, headers: {...headers, 'Content-Type': 'application/json'}, body: JSON.stringify(body) })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Save failed')
    if (typeof umami !== 'undefined') umami.track(editing ? 'vehicle-updated' : 'vehicle-added')
    setAdding(false); setEditing(null); load()
  }

  async function handleActivate(id) {
    await fetch(`/api/v1/vehicles/${id}/activate`, { method: 'POST', headers })
    load()
  }

  async function handleDelete(id) {
    if (!window.confirm('Remove this vehicle?')) return
    await fetch(`/api/v1/vehicles/${id}`, { method: 'DELETE', headers })
    load()
  }

  return (
    <ModalOverlay onClose={onClose}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border)', flexShrink:0}}>
        <h2 style={{color:'var(--text)', fontSize:'18px', margin:0}}>My Vehicles</h2>
        <button onClick={onClose} style={{background:'none', border:'none', color:'var(--text2)', fontSize:'20px', cursor:'pointer'}}>X</button>
      </div>

      <div style={{flex:1, overflowY:'auto', padding:'20px'}}>
        {(adding || editing) ? (
          <VehicleForm
            initial={editing}
            accessToken={accessToken}
            onSave={handleSave}
            onCancel={() => { setAdding(false); setEditing(null) }}
          />
        ) : loading ? (
          <p style={{color:'var(--text3)'}}>Loading...</p>
        ) : vehicles.length === 0 ? (
          <div style={{textAlign:'center', padding:'32px 0'}}>
            <div style={{fontSize:'40px', marginBottom:'12px'}}>🚗</div>
            <p style={{color:'var(--text2)', marginBottom:'16px'}}>No vehicles yet. Add your first vehicle to get personalised fuel cost estimates.</p>
            <button onClick={() => setAdding(true)}
              style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px 24px', borderRadius:'8px', border:'none', cursor:'pointer'}}>
              Add my first vehicle
            </button>
          </div>
        ) : (
          <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
            {vehicles.map(v => (
              <div key={v.id} style={{background: v.is_active ? 'rgba(245,166,35,0.08)' : 'var(--surface)',
                border: '1px solid ' + (v.is_active ? 'var(--amber)' : 'var(--border)'),
                borderRadius:'10px', padding:'12px 14px'}}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'8px'}}>
                  <div style={{minWidth:0}}>
                    <div style={{display:'flex', gap:'8px', alignItems:'center', marginBottom:'4px', flexWrap:'wrap'}}>
                      <span style={{fontWeight:700, color:'var(--text)', fontFamily:'var(--font-mono)'}}>{v.registration}</span>
                      {v.nickname && <span style={{fontSize:'12px', color:'var(--text3)'}}>"{v.nickname}"</span>}
                      {v.is_active && <span style={{fontSize:'10px', padding:'2px 6px', borderRadius:'4px', background:'var(--amber)', color:'#000', fontWeight:700}}>Active</span>}
                    </div>
                    <div style={{fontSize:'13px', color:'var(--text2)'}}>
                      {[v.year, v.make, v.model].filter(Boolean).join(' ')}
                      {v.colour && ' · ' + v.colour}
                    </div>
                    <div style={{fontSize:'12px', color:'var(--text3)', marginTop:'2px', display:'flex', gap:'10px', flexWrap:'wrap'}}>
                      {v.fuel_type && <span>{FUEL_LABELS[v.fuel_type] || v.fuel_type}</span>}
                      {v.tank_litres && <span>{v.tank_litres}L</span>}
                      {v.mpg && <span>{v.mpg} MPG</span>}
                    </div>
                  </div>
                  <div style={{display:'flex', gap:'6px', flexShrink:0}}>
                    {!v.is_active && (
                      <button onClick={() => handleActivate(v.id)}
                        style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid var(--amber)', background:'rgba(245,166,35,0.1)', color:'var(--amber)', cursor:'pointer'}}>
                        Set active
                      </button>
                    )}
                    <button onClick={() => setEditing(v)}
                      style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid var(--border2)', background:'var(--surface2)', color:'var(--text2)', cursor:'pointer'}}>Edit</button>
                    <button onClick={() => handleDelete(v.id)}
                      style={{fontSize:'11px', padding:'4px 10px', borderRadius:'6px', border:'1px solid #e74c3c', background:'transparent', color:'#e74c3c', cursor:'pointer'}}>✕</button>
                  </div>
                </div>
              </div>
            ))}
            {vehicles.length < 10 && (
              <button onClick={() => setAdding(true)}
                style={{width:'100%', padding:'10px', borderRadius:'8px', border:'1px dashed var(--border2)', background:'transparent', color:'var(--text3)', cursor:'pointer', fontSize:'13px', marginTop:'4px'}}>
                + Add vehicle
              </button>
            )}
          </div>
        )}
      </div>
    </ModalOverlay>
  )
}

import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import Portal from './Portal'

const TABS = ['Log Fill-up', 'History', 'Stats']

function ModalOverlay({ children, onClose }) {
  return (
    <Portal>
      <div
        style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', zIndex:10000, display:'flex', alignItems:'center', justifyContent:'center', padding:'16px'}}
        onClick={e => e.target === e.currentTarget && onClose()}
      >
        <div style={{background:'var(--bg)', border:'1px solid var(--border)', borderRadius:'16px', width:'100%', maxWidth:'600px', maxHeight:'90vh', display:'flex', flexDirection:'column', overflow:'hidden'}}>
          {children}
        </div>
      </div>
    </Portal>
  )
}

function TabBar({ active, onChange }) {
  return (
    <div style={{display:'flex', borderBottom:'1px solid var(--border)', flexShrink:0}}>
      {TABS.map(t => (
        <button key={t} onClick={() => onChange(t)} style={{
          flex:1, padding:'12px', background:'none', border:'none',
          borderBottom: active === t ? '2px solid var(--amber)' : '2px solid transparent',
          color: active === t ? 'var(--amber)' : 'var(--text2)',
          fontWeight: active === t ? 700 : 400,
          cursor:'pointer', fontSize:'13px', marginBottom:'-1px',
        }}>{t}</button>
      ))}
    </div>
  )
}

export default function FuelTrackerModal({ onClose, prefillStation = null }) {
  const { user, accessToken } = useAuth()
  const [tab, setTab] = useState('Log Fill-up')
  const [vehicles, setVehicles] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)
  const [fillups, setFillups] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState(null)
  const [editingId, setEditingId] = useState(null)

  const [form, setForm] = useState({
    vehicle_id: '',
    filled_at: new Date().toISOString().split('T')[0],
    station_name: prefillStation?.name || '',
    station_id: prefillStation?.id || '',
    fuel_type: 'E10',
    litres: '',
    price_pence_per_litre: '',
    odometer_miles: '',
    notes: '',
  })

  const headers = { Authorization: 'Bearer ' + accessToken, 'Content-Type': 'application/json' }

  useEffect(() => {
    fetch('/api/v1/vehicles', { headers })
      .then(r => r.ok ? r.json() : [])
      .then(data => {
        setVehicles(data)
        const active = data.find(v => v.is_active) || data[0]
        if (active) {
          setSelectedVehicle(active)
          setForm(f => ({ ...f, vehicle_id: active.id, fuel_type: active.fuel_type || 'E10' }))
        }
      })
  }, [])

  useEffect(() => {
    if (tab === 'History' || tab === 'Stats') fetchData()
  }, [tab, selectedVehicle])

  async function fetchData() {
    setLoading(true)
    const vid = selectedVehicle?.id ? `?vehicle_id=${selectedVehicle.id}` : ''
    const [fillupRes, statsRes] = await Promise.all([
      fetch(`/api/v1/fillups/${vid}`, { headers }),
      fetch(`/api/v1/fillups/stats${vid}`, { headers }),
    ])
    if (fillupRes.ok) setFillups(await fillupRes.json())
    if (statsRes.ok) setStats(await statsRes.json())
    setLoading(false)
  }

  async function handleSubmit() {
    if (!form.vehicle_id || !form.litres || !form.price_pence_per_litre) {
      setMsg('Please fill in vehicle, litres and price.')
      return
    }
    setLoading(true); setMsg(null)
    try {
      const payload = {
        ...form,
        litres: parseFloat(form.litres),
        price_pence_per_litre: parseFloat(form.price_pence_per_litre),
        odometer_miles: form.odometer_miles ? parseFloat(form.odometer_miles) : null,
        station_id: form.station_id || null,
        station_name: form.station_name || null,
        notes: form.notes || null,
      }
      const url = editingId ? `/api/v1/fillups/${editingId}` : '/api/v1/fillups/'
      const method = editingId ? 'PATCH' : 'POST'
      const r = await fetch(url, { method, headers, body: JSON.stringify(payload) })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || 'Failed')
      setMsg(editingId ? 'Fill-up updated.' : 'Fill-up logged!')
      setEditingId(null)
      setForm(f => ({ ...f, litres: '', price_pence_per_litre: '', odometer_miles: '', notes: '', station_name: prefillStation?.name || '', station_id: prefillStation?.id || '' }))
    } catch(e) { setMsg('Error: ' + e.message) }
    finally { setLoading(false) }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this fill-up?')) return
    await fetch(`/api/v1/fillups/${id}`, { method: 'DELETE', headers })
    setFillups(prev => prev.filter(f => f.id !== id))
  }

  function handleEdit(fillup) {
    setEditingId(fillup.id)
    setForm({
      vehicle_id: fillup.vehicle_id,
      filled_at: fillup.filled_at,
      station_name: fillup.station_name || '',
      station_id: fillup.station_id || '',
      fuel_type: fillup.fuel_type,
      litres: String(fillup.litres),
      price_pence_per_litre: String(fillup.price_pence_per_litre),
      odometer_miles: fillup.odometer_miles ? String(fillup.odometer_miles) : '',
      notes: fillup.notes || '',
    })
    setTab('Log Fill-up')
  }

  const inputStyle = {
    background:'var(--surface2)', border:'1px solid var(--border2)', color:'var(--text)',
    padding:'8px 10px', borderRadius:'8px', fontSize:'13px', width:'100%', boxSizing:'border-box'
  }
  const labelStyle = { fontSize:'11px', color:'var(--text3)', marginBottom:'4px', display:'block' }

  return (
    <ModalOverlay onClose={onClose}>
      {/* Header */}
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border)', flexShrink:0}}>
        <div>
          <h2 style={{color:'var(--text)', fontSize:'18px', margin:0}}>⛽ Fuel Tracker</h2>
          <p style={{color:'var(--text3)', fontSize:'12px', margin:'2px 0 0', fontFamily:'var(--font-mono)'}}>Pro feature</p>
        </div>
        <button onClick={onClose} style={{background:'none', border:'none', color:'var(--text2)', fontSize:'20px', cursor:'pointer', padding:'4px'}}>✕</button>
      </div>

      {/* Vehicle selector */}
      <div style={{padding:'12px 20px', borderBottom:'1px solid var(--border)', flexShrink:0, display:'flex', gap:'8px', alignItems:'center', flexWrap:'wrap'}}>
        <span style={{fontSize:'12px', color:'var(--text3)'}}>Vehicle:</span>
        {vehicles.map(v => (
          <button key={v.id} onClick={() => { setSelectedVehicle(v); setForm(f => ({...f, vehicle_id: v.id, fuel_type: v.fuel_type || f.fuel_type})) }}
            style={{padding:'4px 12px', borderRadius:'20px', border:'1px solid', fontSize:'12px', cursor:'pointer',
              borderColor: selectedVehicle?.id === v.id ? 'var(--amber)' : 'var(--border2)',
              background: selectedVehicle?.id === v.id ? 'rgba(245,166,35,0.15)' : 'var(--surface2)',
              color: selectedVehicle?.id === v.id ? 'var(--amber)' : 'var(--text2)',
            }}>
            {v.nickname || `${v.make || ''} ${v.model || ''}`.trim() || v.registration}
            {v.is_active && ' ⚡'}
          </button>
        ))}
        {vehicles.length === 0 && <span style={{fontSize:'12px', color:'var(--text3)'}}>No vehicles. <a href="/my-vehicles" style={{color:'var(--amber)'}}>Add one →</a></span>}
      </div>

      <TabBar active={tab} onChange={setTab} />

      <div style={{flex:1, overflowY:'auto', padding:'20px'}}>

        {/* LOG FILL-UP TAB */}
        {tab === 'Log Fill-up' && (
          <div style={{display:'flex', flexDirection:'column', gap:'12px'}}>
            {editingId && <div style={{background:'rgba(245,166,35,0.1)', border:'1px solid var(--amber)', borderRadius:'8px', padding:'8px 12px', fontSize:'12px', color:'var(--amber)'}}>Editing fill-up — make changes and save</div>}
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px'}}>
              <div>
                <label style={labelStyle}>Date</label>
                <input type="date" style={inputStyle} value={form.filled_at} onChange={e => setForm(f => ({...f, filled_at: e.target.value}))} />
              </div>
              <div>
                <label style={labelStyle}>Fuel type</label>
                <select style={inputStyle} value={form.fuel_type} onChange={e => setForm(f => ({...f, fuel_type: e.target.value}))}>
                  {['E10','B7','E5','SDV','HVO','B10'].map(ft => <option key={ft} value={ft}>{ft}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>Litres filled</label>
                <input type="number" step="0.01" placeholder="e.g. 45.5" style={inputStyle} value={form.litres} onChange={e => setForm(f => ({...f, litres: e.target.value}))} />
              </div>
              <div>
                <label style={labelStyle}>Price (p/litre)</label>
                <input type="number" step="0.1" placeholder="e.g. 156.9" style={inputStyle} value={form.price_pence_per_litre} onChange={e => setForm(f => ({...f, price_pence_per_litre: e.target.value}))} />
              </div>
            </div>
            {form.litres && form.price_pence_per_litre && (
              <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'8px', padding:'10px 14px', fontSize:'13px', color:'var(--text2)'}}>
                Total cost: <strong style={{color:'var(--amber)'}}>£{(parseFloat(form.litres) * parseFloat(form.price_pence_per_litre) / 100).toFixed(2)}</strong>
              </div>
            )}
            <div>
              <label style={labelStyle}>Station (optional)</label>
              <input type="text" placeholder="Station name" style={inputStyle} value={form.station_name} onChange={e => setForm(f => ({...f, station_name: e.target.value, station_id: ''}))} />
            </div>
            <div>
              <label style={labelStyle}>Odometer reading — miles (optional, enables MPG tracking)</label>
              <input type="number" step="1" placeholder="e.g. 45231" style={inputStyle} value={form.odometer_miles} onChange={e => setForm(f => ({...f, odometer_miles: e.target.value}))} />
            </div>
            <div>
              <label style={labelStyle}>Notes (optional)</label>
              <input type="text" placeholder="e.g. Long motorway trip" style={inputStyle} value={form.notes} onChange={e => setForm(f => ({...f, notes: e.target.value}))} />
            </div>
            {msg && <p style={{fontSize:'12px', color: msg.startsWith('Error') ? '#e74c3c' : '#2ecc71', margin:0}}>{msg}</p>}
            <div style={{display:'flex', gap:'8px'}}>
              <button onClick={handleSubmit} disabled={loading}
                style={{flex:1, background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px', borderRadius:'8px', border:'none', cursor:'pointer', fontSize:'14px', opacity: loading ? 0.6 : 1}}>
                {loading ? 'Saving...' : editingId ? 'Save changes' : 'Log fill-up'}
              </button>
              {editingId && (
                <button onClick={() => { setEditingId(null); setForm(f => ({...f, litres:'', price_pence_per_litre:'', odometer_miles:'', notes:''})) }}
                  style={{padding:'10px 16px', borderRadius:'8px', border:'1px solid var(--border2)', background:'var(--surface2)', color:'var(--text2)', cursor:'pointer', fontSize:'13px'}}>
                  Cancel
                </button>
              )}
            </div>
          </div>
        )}

        {/* HISTORY TAB */}
        {tab === 'History' && (
          <div>
            {loading ? <p style={{color:'var(--text3)'}}>Loading...</p> :
            fillups.length === 0 ? <p style={{color:'var(--text3)', textAlign:'center', padding:'32px 0'}}>No fill-ups logged yet.</p> :
            <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
              {fillups.map(f => (
                <div key={f.id} style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'12px 14px'}}>
                  <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'8px'}}>
                    <div style={{minWidth:0}}>
                      <div style={{display:'flex', gap:'8px', alignItems:'center', marginBottom:'4px'}}>
                        <span style={{fontSize:'13px', fontWeight:700, color:'var(--text)'}}>{new Date(f.filled_at).toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric'})}</span>
                        <span style={{fontSize:'11px', padding:'1px 6px', borderRadius:'4px', background:'var(--surface2)', color:'var(--text3)'}}>{f.fuel_type}</span>
                        {f.vehicle_name && <span style={{fontSize:'11px', color:'var(--text3)'}}>{f.vehicle_name}</span>}
                      </div>
                      <div style={{fontSize:'13px', color:'var(--text2)'}}>
                        {f.litres.toFixed(2)}L @ {f.price_pence_per_litre.toFixed(1)}p = <strong style={{color:'var(--amber)'}}>£{(f.total_cost_pence/100).toFixed(2)}</strong>
                      </div>
                      {f.station_name && <div style={{fontSize:'12px', color:'var(--text3)', marginTop:'2px'}}>📍 {f.station_name}</div>}
                      {f.odometer_miles && <div style={{fontSize:'12px', color:'var(--text3)', marginTop:'2px'}}>🔢 {f.odometer_miles.toLocaleString()} mi</div>}
                      {f.notes && <div style={{fontSize:'12px', color:'var(--text3)', marginTop:'2px', fontStyle:'italic'}}>{f.notes}</div>}
                    </div>
                    <div style={{display:'flex', gap:'6px', flexShrink:0}}>
                      <button onClick={() => handleEdit(f)}
                        style={{fontSize:'11px', padding:'4px 8px', borderRadius:'6px', border:'1px solid var(--border2)', background:'var(--surface2)', color:'var(--text2)', cursor:'pointer'}}>Edit</button>
                      <button onClick={() => handleDelete(f.id)}
                        style={{fontSize:'11px', padding:'4px 8px', borderRadius:'6px', border:'1px solid #e74c3c', background:'transparent', color:'#e74c3c', cursor:'pointer'}}>Delete</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* STATS TAB */}
        {tab === 'Stats' && (
          <div>
            {loading ? <p style={{color:'var(--text3)'}}>Loading...</p> :
            !stats || stats.fillup_count === 0 ? <p style={{color:'var(--text3)', textAlign:'center', padding:'32px 0'}}>No data yet. Log some fill-ups first.</p> : (
              <div style={{display:'flex', flexDirection:'column', gap:'20px'}}>
                {/* Key stats */}
                <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:'10px'}}>
                  {[
                    {label:'Total spend', value:`£${stats.total_spend_gbp.toFixed(2)}`},
                    {label:'Total litres', value:`${stats.total_litres.toFixed(1)}L`},
                    {label:'Fill-ups logged', value:stats.fillup_count},
                    {label:'Avg price paid', value:`${stats.avg_ppl.toFixed(1)}p/L`},
                    {label:'Predicted monthly', value: stats.predicted_monthly_spend ? `£${stats.predicted_monthly_spend.toFixed(2)}` : '—'},
                    {label:'Predicted annual', value: stats.predicted_annual_spend ? `£${stats.predicted_annual_spend.toFixed(2)}` : '—'},
                  ].map(s => (
                    <div key={s.label} style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'8px', padding:'12px'}}>
                      <div style={{fontSize:'11px', color:'var(--text3)', marginBottom:'4px'}}>{s.label}</div>
                      <div style={{fontSize:'20px', fontWeight:700, color:'var(--amber)', fontFamily:'var(--font-mono)'}}>{s.value}</div>
                    </div>
                  ))}
                </div>

                {/* MPG comparison */}
                {(stats.avg_actual_mpg || stats.spec_mpg) && (
                  <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'14px'}}>
                    <div style={{fontSize:'13px', fontWeight:700, color:'var(--text)', marginBottom:'10px'}}>Fuel Economy</div>
                    <div style={{display:'flex', gap:'16px'}}>
                      {stats.avg_actual_mpg && (
                        <div>
                          <div style={{fontSize:'11px', color:'var(--text3)'}}>Actual MPG</div>
                          <div style={{fontSize:'22px', fontWeight:700, color:'#2ecc71', fontFamily:'var(--font-mono)'}}>{stats.avg_actual_mpg}</div>
                        </div>
                      )}
                      {stats.spec_mpg && (
                        <div>
                          <div style={{fontSize:'11px', color:'var(--text3)'}}>Spec MPG</div>
                          <div style={{fontSize:'22px', fontWeight:700, color:'var(--text2)', fontFamily:'var(--font-mono)'}}>{stats.spec_mpg}</div>
                        </div>
                      )}
                      {stats.avg_actual_mpg && stats.spec_mpg && (
                        <div>
                          <div style={{fontSize:'11px', color:'var(--text3)'}}>vs spec</div>
                          <div style={{fontSize:'22px', fontWeight:700, fontFamily:'var(--font-mono)',
                            color: stats.avg_actual_mpg >= stats.spec_mpg ? '#2ecc71' : '#e74c3c'}}>
                            {stats.avg_actual_mpg >= stats.spec_mpg ? '+' : ''}{(stats.avg_actual_mpg - stats.spec_mpg).toFixed(1)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Monthly spend chart */}
                {stats.monthly && stats.monthly.length > 1 && (
                  <div>
                    <div style={{fontSize:'13px', fontWeight:700, color:'var(--text)', marginBottom:'10px'}}>Monthly Spend</div>
                    <ResponsiveContainer width="100%" height={160}>
                      <BarChart data={stats.monthly}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                        <XAxis dataKey="month" tick={{fontSize:10, fill:'#666'}} />
                        <YAxis tick={{fontSize:10, fill:'#666'}} tickFormatter={v => `£${v}`} />
                        <Tooltip formatter={v => [`£${v}`, 'Spend']} contentStyle={{background:'#181818', border:'1px solid #333', fontSize:'12px'}} />
                        <Bar dataKey="spend_gbp" fill="#f5a623" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* MPG history chart */}
                {stats.mpg_history && stats.mpg_history.length > 1 && (
                  <div>
                    <div style={{fontSize:'13px', fontWeight:700, color:'var(--text)', marginBottom:'10px'}}>MPG History</div>
                    <ResponsiveContainer width="100%" height={160}>
                      <LineChart data={stats.mpg_history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                        <XAxis dataKey="date" tick={{fontSize:10, fill:'#666'}} />
                        <YAxis tick={{fontSize:10, fill:'#666'}} domain={['auto','auto']} />
                        <Tooltip formatter={v => [v + ' MPG', 'Actual MPG']} contentStyle={{background:'#181818', border:'1px solid #333', fontSize:'12px'}} />
                        {stats.spec_mpg && <Line type="monotone" dataKey={() => stats.spec_mpg} stroke="#666" strokeDasharray="4 4" dot={false} name="Spec MPG" />}
                        <Line type="monotone" dataKey="mpg" stroke="#2ecc71" strokeWidth={2} dot={{r:3}} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </ModalOverlay>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import { getPriceHistory, getStation, getPriceChanges } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import FuelTrackerModal from '../components/FuelTrackerModal'
import { useBrandLogos } from '../contexts/BrandsContext'
import { FUEL_COLORS, FUEL_LABELS } from '../constants/fuels'
import { getWeekHours, isOpenNow } from '../utils/openingHours'
import { timeAgo } from '../utils/timeAgo'
import './StationDetail.css'

const DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const TODAY_IDX = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1

const AMENITY_LABELS = {
  adblue_pumps:         { icon: '🔵', label: 'AdBlue Pumps' },
  adblue_packaged:      { icon: '🔵', label: 'AdBlue Packaged' },
  lpg_pumps:            { icon: '🟡', label: 'LPG' },
  car_wash:             { icon: '🚿', label: 'Car Wash' },
  air_pump_or_screenwash: { icon: '💨', label: 'Air / Screenwash' },
  water_filling:        { icon: '💧', label: 'Water' },
  twenty_four_hour_fuel:{ icon: '⏰', label: '24hr Fuel' },
  customer_toilets:     { icon: '🚻', label: 'Toilets' },
}

export default function StationDetail() {
  const { id } = useParams()
  const location = useLocation()
  const fuelParam = new URLSearchParams(location.search).get('fuel')
  const navigate = useNavigate()
  const [station, setStation] = useState(null)
  const [history, setHistory] = useState([])
  const [historyRange, setHistoryRange] = useState('all')
  const [selectedFuel, setSelectedFuel] = useState(fuelParam || 'E10')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [priceChanges, setPriceChanges] = useState({})
  const { user, accessToken } = useAuth()
  const brandLogos = useBrandLogos()
  const brandLogo = station?.brand ? brandLogos[station.brand.toUpperCase()] : null
  const isPro = user?.role === 'pro' || user?.role === 'admin'
  const [alerts, setAlerts] = useState([])
  const [alertForm, setAlertForm] = useState({ fuel_type: '', alert_type: 'below_pence', threshold: '' })
  const [alertMsg, setAlertMsg] = useState(null)
  const [alertLoading, setAlertLoading] = useState(false)

  useEffect(() => {
    Promise.all([getStation(id), getPriceChanges(id)])
      .then(([stationRes, changesRes]) => {
        setStation(stationRes.data)
        const fuels = stationRes.data.latest_prices.map(p => p.fuel_type)
        if (fuels.length > 0 && !fuelParam) setSelectedFuel(fuels[0])
        const map = {}
        changesRes.data.forEach(c => { map[c.fuel_type] = c })
        setPriceChanges(map)
      })
      .catch(() => setError('Unable to load station details.'))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!station) return
    setHistory([])
    const now = new Date()
    const rangeMap = { '7d': 7, '30d': 30, '90d': 90 }
    const days = rangeMap[historyRange]
    const params = days ? { from_dt: new Date(now - days * 86400000).toISOString().replace('Z', '').split('.')[0] } : {}
    getPriceHistory(id, selectedFuel, params).then(r => {
      setHistory(
        r.data.history.map(h => ({
          ts: new Date(h.recorded_at).getTime(),
          price: h.price_pence,
        }))
      )
    })
  }, [id, selectedFuel, station, historyRange])

  useEffect(() => {
    if (!isPro || !accessToken || !id) return
    fetch(`/api/v1/alerts/station/${id}`, {
      headers: { Authorization: 'Bearer ' + accessToken }
    }).then(r => r.ok ? r.json() : []).then(setAlerts).catch(() => {})
  }, [isPro, accessToken, id])

  if (loading) return <div className="detail-loading">Loading station…</div>
  if (!station) return <div className="detail-loading">Station not found</div>

  const availableFuels = station.latest_prices.map(p => p.fuel_type)
  const anyFlagged = station.latest_prices.some(p => p.price_flagged)
  const color = FUEL_COLORS[selectedFuel] || 'var(--amber)'
  const openStatus = isOpenNow(station.opening_times)
  const weekHours = getWeekHours(station.opening_times)

  return (
    <>
    <div className="detail-page">
      <div className="detail-inner">
        <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'0'}}>
          <button className="detail-back" onClick={() => navigate(-1)}>← Back</button>
          {isPro && (
            <button
              onClick={() => setShowTracker(true)}
              style={{padding:'6px 14px', borderRadius:'8px', border:'1px solid var(--amber)',
                background:'rgba(245,166,35,0.1)', color:'var(--amber)', fontSize:'13px',
                fontWeight:700, cursor:'pointer'}}
            >⛽ Log fill-up here</button>
          )}
        </div>

        {anyFlagged && (
          <div className="detail-flagged-banner">
            <span className="detail-flagged-icon">⚠️</span>
            <span>One or more prices at this station have been flagged as potentially unreliable. The price shown may be significantly below the local average, or hasn't been updated by the supplier in over 60 days. We recommend verifying at the pump.</span>
          </div>
        )}

        <div className="detail-header">
          <div>
            <h1 className="detail-name">{station.name}</h1>
            <p className="detail-address">{station.address} {station.postcode}</p>
            <div className="detail-tags">
              {station.brand && (
                <span className="detail-brand" style={{display:'flex', alignItems:'center', gap:'6px'}}>
                  {brandLogo && <img src={brandLogo} alt={station.brand} style={{width:'24px', height:'24px', objectFit:'contain', borderRadius:'4px', background:'#fff', padding:'2px'}} />}
                  {station.brand}
                </span>
              )}
              {station.is_motorway && <span className="detail-tag detail-tag-motorway">Motorway</span>}
              {station.is_supermarket && <span className="detail-tag detail-tag-supermarket">Supermarket</span>}
              {station.temporary_closure && <span className="detail-tag detail-tag-closed">Temporarily Closed</span>}
            </div>
          </div>
          {openStatus !== null && (
            <div className={`detail-open-badge ${openStatus ? 'open' : 'closed'}`}>
              <span className="detail-open-dot" />
              {openStatus ? 'Open Now' : 'Closed'}
            </div>
          )}
        </div>

        {/* Current prices */}
        <div className="detail-prices">
          {station.latest_prices.map(p => {
            const c = FUEL_COLORS[p.fuel_type] || 'var(--amber)'
            return (
              <div
                key={p.fuel_type}
                className={`detail-price-card ${selectedFuel === p.fuel_type ? 'active' : ''}`}
                style={selectedFuel === p.fuel_type ? { borderColor: c, background: c + '11' } : {}}
                onClick={() => setSelectedFuel(p.fuel_type)}
              >
                <div className="dpc-label">
                  {FUEL_LABELS[p.fuel_type] || p.fuel_type}
                  {p.price_flagged && <span className="dpc-flag" title="This price may be inaccurate — it appears significantly lower than average"> ⚠️</span>}
                  {p.is_county_cheapest && !p.price_flagged && <span className="dpc-flag" title={`Cheapest ${p.fuel_type} in ${station.county}`}> ⭐</span>}
                </div>
                <div className="dpc-updated" style={(() => {
                  if (!p.source_updated_at || p.price_flagged) return {}
                  const ageDays = (Date.now() - new Date(p.source_updated_at).getTime()) / 86400000
                  if (ageDays >= 7) return { color: '#f5a623' }
                  if (ageDays >= 1) return { color: 'var(--text3)' }
                  return {}
                })()}>
                  {p.source_updated_at ? ((() => {
                    const ageDays = (Date.now() - new Date(p.source_updated_at).getTime()) / 86400000
                    if (ageDays >= 7 && !p.price_flagged) return `⚠ Price may be outdated — ${timeAgo(p.source_updated_at)}`
                    return `Updated ${timeAgo(p.source_updated_at)}`
                  })()) : ""}
                </div>
                {priceChanges[p.fuel_type]?.change_pence !== undefined && priceChanges[p.fuel_type]?.change_pence !== 0 && (
                  <div className="dpc-change" style={{ color: priceChanges[p.fuel_type].change_pence < 0 ? '#2ecc71' : '#e74c3c' }}>
                    {priceChanges[p.fuel_type].change_pence > 0 ? '▲' : '▼'} {Math.abs(priceChanges[p.fuel_type].change_pence).toFixed(1)}p
                  </div>
                )}
                <div className="dpc-price" style={{ color: c }}>
                  {p.price_pence.toFixed(2)}<span className="dpc-unit">p</span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Price Alerts */}
        {isPro ? (
          <div className="detail-hours-card">
            <h2 className="detail-section-title">🔔 Price Alerts</h2>

            {alerts.length > 0 && (
              <div style={{marginBottom:'12px', display:'flex', flexDirection:'column', gap:'6px'}}>
                {alerts.map(a => (
                  <div key={a.id} style={{
                    display:'flex', alignItems:'center', justifyContent:'space-between',
                    padding:'8px 12px', background:'var(--surface2)', borderRadius:'8px',
                    border:'1px solid var(--border)', fontSize:'13px', opacity: a.is_active ? 1 : 0.5
                  }}>
                    <span>
                      <strong>{a.fuel_type}</strong> —{' '}
                      {a.alert_type === 'below_pence'
                        ? `below ${a.threshold.toFixed(1)}p`
                        : `change >${a.threshold.toFixed(1)}%`}
                      {a.triggered_count > 0 && <span style={{color:'var(--text3)', marginLeft:'6px'}}>· triggered {a.triggered_count}×</span>}
                    </span>
                    <div style={{display:'flex', gap:'6px'}}>
                      <button
                        onClick={async () => {
                          const r = await fetch('/api/v1/alerts/' + a.id + '/toggle', {
                            method:'PATCH', headers:{Authorization:'Bearer ' + accessToken}
                          })
                          if (r.ok) setAlerts(prev => prev.map(x => x.id === a.id ? {...x, is_active: !x.is_active} : x))
                        }}
                        style={{fontSize:'11px', padding:'3px 8px', borderRadius:'6px', border:'1px solid var(--border2)',
                          background:'var(--surface)', color:'var(--text2)', cursor:'pointer'}}
                      >{a.is_active ? 'Pause' : 'Resume'}</button>
                      <button
                        onClick={async () => {
                          if (!window.confirm('Delete this alert?')) return
                          const r = await fetch('/api/v1/alerts/' + a.id, {
                            method:'DELETE', headers:{Authorization:'Bearer ' + accessToken}
                          })
                          if (r.ok) setAlerts(prev => prev.filter(x => x.id !== a.id))
                        }}
                        style={{fontSize:'11px', padding:'3px 8px', borderRadius:'6px', border:'1px solid #e74c3c',
                          background:'transparent', color:'#e74c3c', cursor:'pointer'}}
                      >Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
              <div style={{display:'flex', gap:'8px', flexWrap:'wrap'}}>
                <select
                  value={alertForm.fuel_type}
                  onChange={e => setAlertForm(f => ({...f, fuel_type: e.target.value}))}
                  style={{flex:1, minWidth:'80px', background:'var(--surface2)', border:'1px solid var(--border2)',
                    color:'var(--text)', padding:'6px 8px', borderRadius:'6px', fontSize:'13px'}}
                >
                  <option value="">Fuel type</option>
                  {station.latest_prices.map(p => (
                    <option key={p.fuel_type} value={p.fuel_type}>{p.fuel_type}</option>
                  ))}
                </select>
                <select
                  value={alertForm.alert_type}
                  onChange={e => setAlertForm(f => ({...f, alert_type: e.target.value}))}
                  style={{flex:1, minWidth:'120px', background:'var(--surface2)', border:'1px solid var(--border2)',
                    color:'var(--text)', padding:'6px 8px', borderRadius:'6px', fontSize:'13px'}}
                >
                  <option value="below_pence">Below (pence)</option>
                  <option value="change_pct">Change (%)</option>
                </select>
                <input
                  type="number"
                  placeholder={alertForm.alert_type === 'below_pence' ? 'e.g. 135.0' : 'e.g. 2.5'}
                  value={alertForm.threshold}
                  onChange={e => setAlertForm(f => ({...f, threshold: e.target.value}))}
                  style={{flex:1, minWidth:'90px', background:'var(--surface2)', border:'1px solid var(--border2)',
                    color:'var(--text)', padding:'6px 8px', borderRadius:'6px', fontSize:'13px'}}
                />
                <button
                  disabled={alertLoading || !alertForm.fuel_type || !alertForm.threshold}
                  onClick={async () => {
                    setAlertLoading(true); setAlertMsg(null)
                    try {
                      const r = await fetch('/api/v1/alerts/', {
                        method:'POST',
                        headers:{'Content-Type':'application/json', Authorization:'Bearer ' + accessToken},
                        body: JSON.stringify({
                          station_id: id,
                          fuel_type: alertForm.fuel_type,
                          alert_type: alertForm.alert_type,
                          threshold: parseFloat(alertForm.threshold),
                        })
                      })
                      const data = await r.json()
                      if (!r.ok) throw new Error(data.detail || 'Failed')
                      setAlerts(prev => [data, ...prev])
                      setAlertForm(f => ({...f, threshold: ''}))
                      setAlertMsg('Alert created.')
                    } catch (e) { setAlertMsg('Error: ' + e.message) }
                    finally { setAlertLoading(false) }
                  }}
                  style={{padding:'6px 16px', borderRadius:'6px', border:'none', background:'var(--amber)',
                    color:'#000', fontWeight:700, fontSize:'13px', cursor:'pointer', opacity: alertLoading ? 0.6 : 1}}
                >{alertLoading ? 'Saving…' : '+ Add alert'}</button>
              </div>
              {alertMsg && <p style={{fontSize:'12px', color:'var(--text2)', margin:0}}>{alertMsg}</p>}
              <p style={{fontSize:'11px', color:'var(--text3)', margin:0}}>
                Alerts fire once per 24 hours. You'll get an email when the condition is met.
              </p>
            </div>
          </div>
        ) : (
          <div className="detail-hours-card" style={{display:'flex', alignItems:'center', justifyContent:'space-between', gap:'16px'}}>
            <div>
              <h2 className="detail-section-title" style={{marginBottom:'4px'}}>🔔 Price Alerts</h2>
              <p style={{fontSize:'13px', color:'var(--text3)', margin:0}}>Get notified by email when prices drop or change. A Pro feature.</p>
            </div>
            <a href="/pro" style={{flexShrink:0, padding:'8px 16px', borderRadius:'8px', background:'var(--amber)',
              color:'#000', fontWeight:700, fontSize:'13px', textDecoration:'none', whiteSpace:'nowrap'}}>
              Go Pro →
            </a>
          </div>
        )}

        {/* Price history */}
        <div className="detail-chart-card">
          <div className="detail-chart-header">
            <h2 className="detail-chart-title">Price History</h2>
            <div className="detail-fuel-tabs">
              {availableFuels.map(f => (
                <button
                  key={f}
                  className={`detail-fuel-tab ${selectedFuel === f ? 'active' : ''}`}
                  style={selectedFuel === f ? { color: FUEL_COLORS[f], borderColor: FUEL_COLORS[f] } : {}}
                  onClick={() => setSelectedFuel(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div style={{display:'flex', gap:'6px', marginBottom:'8px'}}>
            {['7d','30d','90d','all'].map(r => (
              <button key={r} onClick={() => setHistoryRange(r)} style={{
                padding:'3px 10px', borderRadius:'6px', border:'1px solid',
                fontSize:'12px', cursor:'pointer',
                borderColor: historyRange === r ? 'var(--amber)' : 'var(--border)',
                background: historyRange === r ? 'rgba(245,166,35,0.1)' : 'transparent',
                color: historyRange === r ? 'var(--amber)' : 'var(--text3)',
              }}>{r === 'all' ? 'All' : r.toUpperCase()}</button>
            ))}
          </div>
          {history.length < 2 ? (
            <div className="detail-no-history">
              No data for this period — prices may not have changed. Try All to see full history.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={history} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis
                  dataKey="ts"
                  type="number"
                  scale="time"
                  domain={['dataMin', 'dataMax']}
                  tick={{ fontSize: 11, fill: '#666' }}
                  axisLine={{ stroke: '#2a2a2a' }}
                  tickLine={false}
                  minTickGap={60}
                  tickFormatter={ts => {
                    const d = new Date(ts)
                    const day = d.getDate()
                    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                    const mon = months[d.getMonth()]
                    const hh = String(d.getHours()).padStart(2,'0')
                    const mm = String(d.getMinutes()).padStart(2,'0')
                    if (historyRange === '7d') return `${day} ${mon} ${hh}:${mm}`
                    return `${day} ${mon}`
                  }}
                />
                <YAxis domain={['auto', 'auto']} width={45} tick={{ fontSize: 11, fill: '#666' }} axisLine={false} tickLine={false} tickFormatter={v => typeof v === 'number' ? `${v.toFixed(1)}p` : v} />
                <Tooltip
                  contentStyle={{ background: '#181818', border: '1px solid #333', borderRadius: '8px', fontSize: '13px' }}
                  formatter={v => [`${v.toFixed(2)}p`, selectedFuel]}
                  labelStyle={{ color: '#888' }}
                  labelFormatter={ts => {
                    const d = new Date(ts)
                    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
                  }}
                />
                <Line type="monotone" dataKey="price" stroke={color} strokeWidth={2} dot={false} activeDot={{ r: 4, fill: color }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Opening hours */}
        {weekHours.length > 0 && (
          <div className="detail-hours-card">
            <h2 className="detail-section-title">Opening Hours</h2>
            <div className="detail-hours-grid">
              {weekHours.map((h, i) => (
                <div key={h.day} className={`detail-hours-row ${i === TODAY_IDX ? 'today' : ''}`}>
                  <span className="detail-hours-day">{h.day}</span>
                  <span className={`detail-hours-val ${h.is_24_hours ? 'allday' : ''}`}>
                    {h.hours}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Amenities */}
        {station.amenities && station.amenities.length > 0 && (
          <div className="detail-amenities-card">
            <h2 className="detail-section-title">Amenities</h2>
            <div className="detail-amenities">
              {station.amenities.map(a => {
                const info = AMENITY_LABELS[a]
                if (!info) return null
                return (
                  <div key={a} className="detail-amenity">
                    <span className="detail-amenity-icon">{info.icon}</span>
                    <span className="detail-amenity-label">{info.label}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {false && (
          <div className="detail-hours-card">
            <h2 className="detail-section-title">🔔 Price Alerts</h2>

            {alerts.length > 0 && (
              <div style={{marginBottom:'12px', display:'flex', flexDirection:'column', gap:'6px'}}>
                {alerts.map(a => (
                  <div key={a.id} style={{
                    display:'flex', alignItems:'center', justifyContent:'space-between',
                    padding:'8px 12px', background:'var(--surface2)', borderRadius:'8px',
                    border:'1px solid var(--border)', fontSize:'13px', opacity: a.is_active ? 1 : 0.5
                  }}>
                    <span>
                      <strong>{a.fuel_type}</strong> —{' '}
                      {a.alert_type === 'below_pence'
                        ? `below ${a.threshold.toFixed(1)}p`
                        : `change >${a.threshold.toFixed(1)}%`}
                      {a.triggered_count > 0 && <span style={{color:'var(--text3)', marginLeft:'6px'}}>· triggered {a.triggered_count}×</span>}
                    </span>
                    <div style={{display:'flex', gap:'6px'}}>
                      <button
                        onClick={async () => {
                          const r = await fetch('/api/v1/alerts/' + a.id + '/toggle', {
                            method:'PATCH', headers:{Authorization:'Bearer ' + accessToken}
                          })
                          if (r.ok) setAlerts(prev => prev.map(x => x.id === a.id ? {...x, is_active: !x.is_active} : x))
                        }}
                        style={{fontSize:'11px', padding:'3px 8px', borderRadius:'6px', border:'1px solid var(--border2)',
                          background:'var(--surface)', color:'var(--text2)', cursor:'pointer'}}
                      >{a.is_active ? 'Pause' : 'Resume'}</button>
                      <button
                        onClick={async () => {
                          if (!window.confirm('Delete this alert?')) return
                          const r = await fetch('/api/v1/alerts/' + a.id, {
                            method:'DELETE', headers:{Authorization:'Bearer ' + accessToken}
                          })
                          if (r.ok) setAlerts(prev => prev.filter(x => x.id !== a.id))
                        }}
                        style={{fontSize:'11px', padding:'3px 8px', borderRadius:'6px', border:'1px solid #e74c3c',
                          background:'transparent', color:'#e74c3c', cursor:'pointer'}}
                      >Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
              <div style={{display:'flex', gap:'8px', flexWrap:'wrap'}}>
                <select
                  value={alertForm.fuel_type}
                  onChange={e => setAlertForm(f => ({...f, fuel_type: e.target.value}))}
                  style={{flex:1, minWidth:'80px', background:'var(--surface2)', border:'1px solid var(--border2)',
                    color:'var(--text)', padding:'6px 8px', borderRadius:'6px', fontSize:'13px'}}
                >
                  <option value="">Fuel type</option>
                  {station.latest_prices.map(p => (
                    <option key={p.fuel_type} value={p.fuel_type}>{p.fuel_type}</option>
                  ))}
                </select>
                <select
                  value={alertForm.alert_type}
                  onChange={e => setAlertForm(f => ({...f, alert_type: e.target.value}))}
                  style={{flex:1, minWidth:'120px', background:'var(--surface2)', border:'1px solid var(--border2)',
                    color:'var(--text)', padding:'6px 8px', borderRadius:'6px', fontSize:'13px'}}
                >
                  <option value="below_pence">Below (pence)</option>
                  <option value="change_pct">Change (%)</option>
                </select>
                <input
                  type="number"
                  placeholder={alertForm.alert_type === 'below_pence' ? 'e.g. 135.0' : 'e.g. 2.5'}
                  value={alertForm.threshold}
                  onChange={e => setAlertForm(f => ({...f, threshold: e.target.value}))}
                  style={{flex:1, minWidth:'90px', background:'var(--surface2)', border:'1px solid var(--border2)',
                    color:'var(--text)', padding:'6px 8px', borderRadius:'6px', fontSize:'13px'}}
                />
                <button
                  disabled={alertLoading || !alertForm.fuel_type || !alertForm.threshold}
                  onClick={async () => {
                    setAlertLoading(true); setAlertMsg(null)
                    try {
                      const r = await fetch('/api/v1/alerts/', {
                        method:'POST',
                        headers:{'Content-Type':'application/json', Authorization:'Bearer ' + accessToken},
                        body: JSON.stringify({
                          station_id: id,
                          fuel_type: alertForm.fuel_type,
                          alert_type: alertForm.alert_type,
                          threshold: parseFloat(alertForm.threshold),
                        })
                      })
                      const data = await r.json()
                      if (!r.ok) throw new Error(data.detail || 'Failed')
                      setAlerts(prev => [data, ...prev])
                      setAlertForm(f => ({...f, threshold: ''}))
                      setAlertMsg('Alert created.')
                    } catch (e) { setAlertMsg('Error: ' + e.message) }
                    finally { setAlertLoading(false) }
                  }}
                  style={{padding:'6px 16px', borderRadius:'6px', border:'none', background:'var(--amber)',
                    color:'#000', fontWeight:700, fontSize:'13px', cursor:'pointer', opacity: alertLoading ? 0.6 : 1}}
                >{alertLoading ? 'Saving…' : '+ Add alert'}</button>
              </div>
              {alertMsg && <p style={{fontSize:'12px', color:'var(--text2)', margin:0}}>{alertMsg}</p>}
              <p style={{fontSize:'11px', color:'var(--text3)', margin:0}}>
                Alerts fire once per 24 hours. You'll get an email when the condition is met.
              </p>
            </div>
          </div>
        )}

        {/* Contact */}
        {station.phone && (
          <div className="detail-contact">
            <span className="detail-contact-label">📞</span>
            <a href={`tel:${station.phone}`} className="detail-contact-val">{station.phone}</a>
          </div>
        )}
      </div>
    </div>
    {showTracker && <FuelTrackerModal onClose={() => setShowTracker(false)} prefillStation={{'id': station?.id, 'name': station?.name}} />}
    </>
  )
}

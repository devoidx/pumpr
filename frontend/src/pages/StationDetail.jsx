import { useEffect, useState } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import { getPriceHistory, getStation, getPriceChanges } from '../api/client'
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
  const [selectedFuel, setSelectedFuel] = useState(fuelParam || 'E10')
  const [loading, setLoading] = useState(true)
  const [priceChanges, setPriceChanges] = useState({})

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
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!station) return
    getPriceHistory(id, selectedFuel).then(r => {
      setHistory(
        r.data.history.map(h => ({
          date: new Date(h.recorded_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
          time: new Date(h.recorded_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
          price: h.price_pence,
        }))
      )
    })
  }, [id, selectedFuel, station])

  if (loading) return <div className="detail-loading">Loading station…</div>
  if (!station) return <div className="detail-loading">Station not found</div>

  const availableFuels = station.latest_prices.map(p => p.fuel_type)
  const color = FUEL_COLORS[selectedFuel] || 'var(--amber)'
  const openStatus = isOpenNow(station.opening_times)
  const weekHours = getWeekHours(station.opening_times)

  return (
    <div className="detail-page">
      <div className="detail-inner">
        <button className="detail-back" onClick={() => navigate(-1)}>← Back</button>

        <div className="detail-header">
          <div>
            <h1 className="detail-name">{station.name}</h1>
            <p className="detail-address">{station.address} {station.postcode}</p>
            <div className="detail-tags">
              {station.brand && <span className="detail-brand">{station.brand}</span>}
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
                <div className="dpc-label">{FUEL_LABELS[p.fuel_type] || p.fuel_type}</div>
                <div className="dpc-updated">{p.source_updated_at ? `Updated ${timeAgo(p.source_updated_at)}` : ""}</div>
                {priceChanges[p.fuel_type]?.change_pence !== undefined && priceChanges[p.fuel_type]?.change_pence !== 0 && (
                  <div className="dpc-change" style={{ color: priceChanges[p.fuel_type].change_pence < 0 ? '#2ecc71' : '#e74c3c' }}>
                    {priceChanges[p.fuel_type].change_pence > 0 ? '▲' : '▼'} {Math.abs(priceChanges[p.fuel_type].change_pence).toFixed(1)}p
                  </div>
                )}
                <div className="dpc-price" style={{ color: c }}>
                  {p.price_pence.toFixed(1)}<span className="dpc-unit">p</span>
                </div>
              </div>
            )
          })}
        </div>

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
          {history.length < 2 ? (
            <div className="detail-no-history">
              Not enough history yet — check back after a few polling cycles.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={history} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#666' }} axisLine={{ stroke: '#2a2a2a' }} tickLine={false} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11, fill: '#666' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}p`} />
                <Tooltip
                  contentStyle={{ background: '#181818', border: '1px solid #333', borderRadius: '8px', fontSize: '13px' }}
                  formatter={v => [`${v.toFixed(1)}p`, selectedFuel]}
                  labelStyle={{ color: '#888' }}
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

        {/* Contact */}
        {station.phone && (
          <div className="detail-contact">
            <span className="detail-contact-label">📞</span>
            <a href={`tel:${station.phone}`} className="detail-contact-val">{station.phone}</a>
          </div>
        )}
      </div>
    </div>
  )
}

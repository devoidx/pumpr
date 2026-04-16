import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import { getPriceHistory, getStation } from '../api/client'
import { FUEL_COLORS, FUEL_LABELS, FUEL_TYPES } from '../constants/fuels'
import './StationDetail.css'

export default function StationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [station, setStation] = useState(null)
  const [history, setHistory] = useState([])
  const [selectedFuel, setSelectedFuel] = useState('E10')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getStation(id)
      .then(r => {
        setStation(r.data)
        const fuels = r.data.latest_prices.map(p => p.fuel_type)
        if (fuels.length > 0) setSelectedFuel(fuels[0])
      })
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!station) return
    getPriceHistory(id, selectedFuel).then(r => {
      setHistory(
        r.data.history.map(h => ({
          date: new Date(h.recorded_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
          price: h.price_pence,
        }))
      )
    })
  }, [id, selectedFuel, station])

  if (loading) return (
    <div className="detail-loading">Loading station…</div>
  )

  if (!station) return (
    <div className="detail-loading">Station not found</div>
  )

  const availableFuels = station.latest_prices.map(p => p.fuel_type)
  const color = FUEL_COLORS[selectedFuel] || 'var(--amber)'

  return (
    <div className="detail-page">
      <div className="detail-inner">
        <button className="detail-back" onClick={() => navigate(-1)}>
          ← Back
        </button>

        <div className="detail-header">
          <div>
            <h1 className="detail-name">{station.name}</h1>
            <p className="detail-address">{station.address} {station.postcode}</p>
            {station.brand && <p className="detail-brand">{station.brand}</p>}
          </div>
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
                <div className="dpc-price" style={{ color: c }}>
                  {p.price_pence.toFixed(1)}
                  <span className="dpc-unit">p</span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Price history chart */}
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
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#666' }}
                  axisLine={{ stroke: '#2a2a2a' }}
                  tickLine={false}
                />
                <YAxis
                  domain={['auto', 'auto']}
                  tick={{ fontSize: 11, fill: '#666' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={v => `${v}p`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#181818',
                    border: '1px solid #333',
                    borderRadius: '8px',
                    fontSize: '13px',
                  }}
                  formatter={v => [`${v.toFixed(1)}p`, selectedFuel]}
                  labelStyle={{ color: '#888' }}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: color }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

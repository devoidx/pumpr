import { useEffect, useState } from 'react'
import { getStats } from '../api/client'
import { FUEL_COLORS, FUEL_LABELS } from '../constants/fuels'
import './Stats.css'

export default function Stats() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getStats().then(r => setStats(r.data)).finally(() => setLoading(false))
  }, [])

  return (
    <div className="stats-page">
      <div className="stats-inner">
        <div className="stats-header">
          <h1 className="stats-title">UK Fuel Prices</h1>
          <p className="stats-sub">
            Live averages across {stats[0]?.station_count?.toLocaleString() || '—'} reporting stations
          </p>
        </div>

        {loading ? (
          <div className="stats-loading">Loading…</div>
        ) : (
          <div className="stats-grid">
            {stats.map(s => {
              const color = FUEL_COLORS[s.fuel_type] || 'var(--amber)'
              return (
                <div key={s.fuel_type} className="stat-card" style={{ '--fuel-color': color }}>
                  <div className="stat-fuel-label">{FUEL_LABELS[s.fuel_type]}</div>
                  <div className="stat-avg" style={{ color }}>
                    {s.avg_price_pence.toFixed(1)}
                    <span className="stat-unit">p/L</span>
                  </div>
                  <div className="stat-range">
                    <div className="stat-range-bar">
                      <div className="stat-range-fill" style={{ background: color }} />
                    </div>
                    <div className="stat-range-labels">
                      <span>{s.min_price_pence.toFixed(1)}p</span>
                      <span>min → max</span>
                      <span>{s.max_price_pence.toFixed(1)}p</span>
                    </div>
                  </div>
                  <div className="stat-stations">
                    {s.station_count.toLocaleString()} stations reporting
                  </div>
                </div>
              )
            })}
          </div>
        )}

        <div className="stats-note">
          Prices updated every 30 minutes from the GOV.UK Fuel Finder API.
          Data collected under the Motor Fuel Price (Open Data) Regulations 2025. LPG is not included in the scheme.
        </div>
      </div>
    </div>
  )
}

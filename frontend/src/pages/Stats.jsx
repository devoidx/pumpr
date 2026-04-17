import { useEffect, useState } from 'react'
import { getStats } from '../api/client'
import { FUEL_COLORS, FUEL_LABELS, FUEL_TYPES } from '../constants/fuels'
import './Stats.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8002'

const COUNTRIES = ['England', 'Scotland', 'Wales', 'Northern Ireland']

export default function Stats() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [fuel, setFuel] = useState('E10')
  const [countryStats, setCountryStats] = useState([])
  const [countyStats, setCountyStats] = useState([])
  const [selectedCountry, setSelectedCountry] = useState('England')
  const [regionalLoading, setRegionalLoading] = useState(false)

  useEffect(() => {
    getStats().then(r => setStats(r.data)).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    setRegionalLoading(true)
    Promise.all([
      fetch(`${API_BASE}/api/v1/stats/countries/cheapest?fuel=${fuel}`).then(r => r.json()),
      fetch(`${API_BASE}/api/v1/stats/counties/cheapest?fuel=${fuel}&country=${selectedCountry}`).then(r => r.json()),
    ])
      .then(([countries, counties]) => {
        setCountryStats(countries)
        setCountyStats(counties)
      })
      .finally(() => setRegionalLoading(false))
  }, [fuel, selectedCountry])

  return (
    <div className="stats-page">
      <div className="stats-inner">

        {/* UK Overview */}
        <div className="stats-header">
          <h1 className="stats-title">UK Fuel Prices</h1>
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
                    {s.avg_price_pence.toFixed(1)}<span className="stat-unit">p/L</span>
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
                  <div className="stat-stations">{s.station_count.toLocaleString()} stations reporting</div>
                </div>
              )
            })}
          </div>
        )}

        {/* Regional Section */}
        <div className="stats-regional">
          <div className="stats-regional-header">
            <h2 className="stats-section-title">Cheapest by Region</h2>
            <div className="stats-fuel-tabs">
              {FUEL_TYPES.map(f => (
                <button
                  key={f}
                  className={`stats-fuel-tab ${fuel === f ? 'active' : ''}`}
                  style={fuel === f ? { color: FUEL_COLORS[f], borderColor: FUEL_COLORS[f] } : {}}
                  onClick={() => setFuel(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Country cards */}
          <div className="stats-country-grid">
            {COUNTRIES.map(country => {
              const data = countryStats.find(c => c.region === country)
              return (
                <div key={country} className="stats-country-card">
                  <div className="stats-country-name">{country}</div>
                  {data ? (
                    <>
                      <div className="stats-country-price" style={{ color: FUEL_COLORS[fuel] }}>
                        {data.price_pence.toFixed(1)}<span className="stats-country-unit">p</span>
                      </div>
                      {data.station_name ? (
                        <div className="stats-country-station">
                          {data.station_name}
                          {data.postcode && <span className="stats-country-postcode"> · {data.postcode}</span>}
                        </div>
                      ) : (
                        <div className="stats-country-station">{data.tied_stations} stations at this price</div>
                      )}
                    </>
                  ) : (
                    <div className="stats-country-na">No data</div>
                  )}
                </div>
              )
            })}
          </div>

          {/* County breakdown */}
          <div className="stats-county-section">
            <div className="stats-county-header">
              <h3 className="stats-section-subtitle">Cheapest by County</h3>
              <div className="stats-country-tabs">
                {COUNTRIES.map(c => (
                  <button
                    key={c}
                    className={`stats-country-tab ${selectedCountry === c ? 'active' : ''}`}
                    onClick={() => setSelectedCountry(c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>

            {regionalLoading ? (
              <div className="stats-loading">Loading…</div>
            ) : (
              <div className="stats-county-grid">
                {countyStats.map(c => (
                  <div key={c.region} className="stats-county-row">
                    <div className="stats-county-name">{c.region}</div>
                    <div className="stats-county-right">
                      {c.station_name && (
                        <div className="stats-county-station">
                          {c.station_name}
                          {c.postcode && <span className="stats-county-postcode"> · {c.postcode}</span>}
                        </div>
                      )}
                      {!c.station_name && (
                        <div className="stats-county-station">{c.tied_stations} stations</div>
                      )}
                      <div className="stats-county-price" style={{ color: FUEL_COLORS[fuel] }}>
                        {c.price_pence.toFixed(1)}p
                      </div>
                    </div>
                  </div>
                ))}
                {countyStats.length === 0 && (
                  <div className="stats-loading">No county data available</div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="stats-note">
          Prices updated every 30 minutes from the GOV.UK Fuel Finder API.
          Data collected under the Motor Fuel Price (Open Data) Regulations 2025.
          LPG is not included in the scheme.
        </div>
      </div>
    </div>
  )
}

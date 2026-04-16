import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getCharger } from '../api/client'
import { CONNECTOR_COLORS, SPEED_COLOR, SPEED_LABEL } from '../constants/ev'
import './EvDetail.css'

export default function EvDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [charger, setCharger] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCharger(id).then(r => setCharger(r.data)).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="ev-loading">Loading charger…</div>
  if (!charger) return <div className="ev-loading">Charger not found</div>

  const speedColor = SPEED_COLOR(charger.max_power_kw)

  return (
    <div className="ev-detail-page">
      <div className="ev-detail-inner">
        <button className="ev-back" onClick={() => navigate(-1)}>← Back</button>

        <div className="ev-header">
          <div>
            <div className="ev-network">{charger.network}</div>
            <h1 className="ev-name">{charger.name}</h1>
            <p className="ev-address">{charger.address} {charger.postcode}</p>
          </div>
          <div className="ev-status-badge" style={{
            color: charger.is_operational ? '#2ecc71' : '#e74c3c',
            borderColor: charger.is_operational ? '#2ecc71' : '#e74c3c',
            background: charger.is_operational ? 'rgba(46,204,113,0.1)' : 'rgba(231,76,60,0.1)',
          }}>
            {charger.is_operational ? '● Operational' : '● Offline'}
          </div>
        </div>

        <div className="ev-stats">
          {charger.max_power_kw && (
            <div className="ev-stat-card">
              <div className="ev-stat-label">Max Power</div>
              <div className="ev-stat-value" style={{ color: speedColor }}>
                {charger.max_power_kw}<span className="ev-stat-unit">kW</span>
              </div>
              <div className="ev-stat-sub" style={{ color: speedColor }}>
                {SPEED_LABEL(charger.max_power_kw)}
              </div>
            </div>
          )}
          <div className="ev-stat-card">
            <div className="ev-stat-label">Charge Points</div>
            <div className="ev-stat-value">{charger.total_points}</div>
          </div>
          {charger.usage_cost && (
            <div className="ev-stat-card">
              <div className="ev-stat-label">Cost</div>
              <div className="ev-stat-value ev-stat-cost">{charger.usage_cost}</div>
            </div>
          )}
          {charger.is_membership_required && (
            <div className="ev-stat-card">
              <div className="ev-stat-label">Access</div>
              <div className="ev-stat-value ev-stat-small">Membership required</div>
            </div>
          )}
        </div>

        <div className="ev-connections-card">
          <h2 className="ev-section-title">Connections</h2>
          <div className="ev-connections">
            {charger.connections.map(c => {
              const color = CONNECTOR_COLORS[c.type] || '#888'
              return (
                <div key={c.id} className="ev-connection" style={{ borderLeft: `3px solid ${color}` }}>
                  <div className="ev-conn-header">
                    <span className="ev-conn-type" style={{ color }}>{c.type}</span>
                    <span className={`ev-conn-status ${c.is_operational ? 'ok' : 'down'}`}>
                      {c.is_operational ? 'Available' : 'Unavailable'}
                    </span>
                  </div>
                  <div className="ev-conn-meta">
                    {c.power_kw && <span>{c.power_kw}kW</span>}
                    {c.amps && <span>{c.amps}A</span>}
                    {c.voltage && <span>{c.voltage}V</span>}
                    {c.is_fast_charge && <span className="ev-fast">Fast charge</span>}
                  </div>
                  {c.level && <div className="ev-conn-level">{c.level}</div>}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

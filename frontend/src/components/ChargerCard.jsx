import { useEffect, useState } from 'react'
import { CONNECTOR_SHORT, SPEED_COLOR, SPEED_LABEL } from '../constants/ev'
import { useAuth } from '../hooks/useAuth'
import './ChargerCard.css'

export default function ChargerCard({ charger: c, isSelected, isHovered, onClick, onHover }) {
  const { user, authFetch } = useAuth()
  const isPro = user?.role === 'pro' || user?.role === 'admin'
  const [starred, setStarred] = useState(false)
  const [starLoading, setStarLoading] = useState(false)

  useEffect(() => {
    if (!isPro || !authFetch) return
    authFetch('/api/v1/locations/chargers/favourites')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) setStarred(data.some(f => f.charger_id === String(c.id)))
      })
      .catch(() => {})
  }, [c.id, isPro, authFetch])

  async function toggleStar(e) {
    e.stopPropagation()
    if (!isPro) return
    setStarLoading(true)
    try {
      if (starred) {
        await authFetch(`/api/v1/locations/chargers/favourites/${c.id}`, { method: 'DELETE' })
        setStarred(false)
      } else {
        await authFetch(`/api/v1/locations/chargers/favourites/${c.id}`, { method: 'POST' })
        setStarred(true)
      }
    } finally {
      setStarLoading(false)
    }
  }

  const maxKw = c.max_power_kw
  const speedColor = SPEED_COLOR(maxKw)

  return (
    <div
      id={`card-${c.id}`}
      className={`charger-card ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
      style={isSelected ? { borderColor: speedColor } : {}}
      onClick={onClick}
      onMouseEnter={() => onHover(c.id)}
      onMouseLeave={() => onHover(null)}
    >
      <button
        className={`cc-star ${starred ? 'cc-star-on' : ''} ${!isPro ? 'cc-star-locked' : ''}`}
        onClick={isPro ? toggleStar : undefined}
        disabled={starLoading}
        title={isPro ? (starred ? 'Remove from favourites' : 'Add to favourites') : 'Favourite chargers — Pro feature'}
      >
        {!isPro ? '🔒' : starred ? '★' : '☆'}
      </button>
      <div className="cc-left">
        <div className="cc-header">
          <span className="cc-name">{c.name}</span>
          {!c.is_operational && (
            <span className="cc-offline">Offline</span>
          )}
        </div>
        <div className="cc-meta">
          <span className="cc-network">{c.network}</span>
          {c.postcode && <><span className="cc-dot">·</span><span>{c.postcode}</span></>}
          {c.distance_km != null && <><span className="cc-dot">·</span><span>{c.distance_km}km</span></>}
        </div>
        <div className="cc-connectors">
          {c.connector_types.slice(0, 3).map(t => (
            <span key={t} className="cc-connector-tag">
              {CONNECTOR_SHORT[t] || t}
            </span>
          ))}
          {c.total_points > 1 && (
            <span className="cc-points">{c.total_points} points</span>
          )}
        </div>
      </div>
      <div className="cc-right">
        {maxKw && (
          <div className="cc-power" style={{ color: speedColor }}>
            {maxKw}<span className="cc-power-unit">kW</span>
          </div>
        )}
        <div className="cc-speed" style={{ color: speedColor }}>
          {SPEED_LABEL(maxKw)}
        </div>
      </div>
    </div>
  )
}

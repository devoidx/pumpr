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
  const lastVerified = c.date_last_verified ? new Date(c.date_last_verified) : null
  const monthsOld = lastVerified ? (Date.now() - lastVerified) / (1000 * 60 * 60 * 24 * 30) : null
  const isStale = monthsOld !== null && monthsOld > 12
  const isVeryStale = monthsOld !== null && monthsOld > 24
  const verifiedLabel = lastVerified ? lastVerified.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' }) : null

  return (
    <div
      id={`card-${c.id}`}
      className={`charger-card ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
      style={isSelected ? { borderColor: speedColor } : {}}
      onClick={onClick}
      onMouseEnter={() => onHover(c.id)}
      onMouseLeave={() => onHover(null)}
    >
      {isPro && (
        <button
          className={`cc-star ${starred ? 'cc-star-on' : ''}`}
          onClick={toggleStar}
          disabled={starLoading}
          title={starred ? 'Remove from favourites' : 'Add to favourites'}
        >
          {starred ? '★' : '☆'}
        </button>
      )}
      <div className="cc-left">
        <div className="cc-header">
          <span className="cc-name">{c.name}</span>
          {!c.is_operational && <span className="cc-offline">Offline</span>}
          {(c.usage_type_id === 2) && <span className="cc-tag cc-tag-private">Restricted</span>}
          {(c.usage_type_id === 6) && <span className="cc-tag cc-tag-private">Visitors only</span>}
          {(c.usage_type_id === 3) && <span className="cc-tag cc-tag-notice">Notice required</span>}
          {(c.usage_type_id === 7) && <span className="cc-tag cc-tag-notice">Notice required</span>}
          {(c.usage_type_id === 4) && <span className="cc-tag cc-tag-members">Membership</span>}
          {(c.usage_type_id === 1 && c.usage_cost === 'Free') && <span className="cc-tag cc-tag-free">Free</span>}
          {(c.usage_type_id === 0 || c.usage_type_id == null) && <span className="cc-tag cc-tag-notice">Access unknown</span>}
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
        <div className="cc-footer">
          {verifiedLabel && (
            <span className={`cc-verified ${isVeryStale ? 'cc-very-stale' : isStale ? 'cc-stale' : ''}`}
              title={`Last verified: ${lastVerified.toLocaleDateString('en-GB', {day: 'numeric', month: 'long', year: 'numeric'})}`}>
              {isVeryStale ? '⚠️' : isStale ? '⚠' : '✓'} Verified {verifiedLabel}
            </span>
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

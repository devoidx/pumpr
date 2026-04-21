import { FUEL_COLORS } from '../constants/fuels'
import { isOpenNow, getTodayHours } from '../utils/openingHours'
import { timeAgo } from '../utils/timeAgo'
import './StationCard.css'

const RANK_LABELS = ['Cheapest', '2nd', '3rd']

export default function StationCard({ station: s, rank, isSelected, isHovered, onClick, onHover, units = 'miles' }) {
  const color = FUEL_COLORS[s.fuel_type] || 'var(--amber)'
  const openStatus = isOpenNow(s.opening_times)
  const todayHours = getTodayHours(s.opening_times)
  const updatedAgo = timeAgo(s.source_updated_at)

  return (
    <div
      id={`card-${s.station_id}`}
      className={`station-card ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
      style={isSelected ? { borderColor: color } : {}}
      onClick={onClick}
      onMouseEnter={() => onHover(s.station_id)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="card-left">
        <div className="card-header">
          {s.is_county_cheapest && !s.price_flagged && <div className="card-tag card-tag-county" title={`Cheapest ${s.fuel_type} in ${s.county}`}>⭐</div>}
          {rank < 3 && (
            <div className="card-rank" style={{ color, borderColor: color + '44', background: color + '11' }}>
              {RANK_LABELS[rank]}
            </div>
          )}
          {s.temporary_closure && <div className="card-tag card-tag-closed">Temp closed</div>}
          {s.is_motorway && <div className="card-tag card-tag-motorway">Motorway</div>}
          {s.is_supermarket && <div className="card-tag card-tag-supermarket">Supermarket</div>}
        </div>
        <div className="card-name">{s.station_name}</div>
        <div className="card-meta">
          {s.brand && <span className="card-brand">{s.brand}</span>}
          {s.brand && s.postcode && <span className="card-dot">·</span>}
          {s.postcode && <span>{s.postcode}</span>}
          {s.distance_km != null && <><span className="card-dot">·</span><span>{units === 'miles' ? (s.distance_km * 0.621371).toFixed(1) + ' mi' : s.distance_km + ' km'}</span></>}
        </div>
        <div className="card-footer">
          {openStatus !== null && (
            <div className="card-open-status">
              <span className={`card-open-dot ${openStatus ? 'open' : 'closed'}`} />
              <span className={`card-open-label ${openStatus ? 'open' : 'closed'}`}>
                {openStatus ? 'Open' : 'Closed'}
              </span>
              {todayHours && <span className="card-open-hours">· {todayHours}</span>}
            </div>
          )}
          {updatedAgo && (
            <span className="card-updated">Updated {updatedAgo}</span>
          )}
        </div>
      </div>
      <div className="card-price-col">
        {s.price_flagged && (
          <span className="card-flag" title="This price may be inaccurate — it appears significantly lower than average">⚠️</span>
        )}
        <div className="card-price" style={{ color }}>
          {s.price_pence.toFixed(1)}
          <span className="card-price-unit">p</span>
        </div>
      </div>
    </div>
  )
}

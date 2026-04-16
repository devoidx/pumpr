import { FUEL_COLORS } from '../constants/fuels'
import './StationCard.css'

const RANK_LABELS = ['Cheapest', '2nd', '3rd']

export default function StationCard({ station: s, rank, isSelected, isHovered, onClick, onHover }) {
  const color = FUEL_COLORS[s.fuel_type] || 'var(--amber)'

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
        {rank < 3 && (
          <div className="card-rank" style={{ color, borderColor: color + '44', background: color + '11' }}>
            {RANK_LABELS[rank]}
          </div>
        )}
        <div className="card-name">{s.station_name}</div>
        <div className="card-meta">
          {s.brand && <span className="card-brand">{s.brand}</span>}
          {s.brand && s.postcode && <span className="card-dot">·</span>}
          {s.postcode && <span>{s.postcode}</span>}
          {s.distance_km != null && (
            <><span className="card-dot">·</span><span>{s.distance_km}km</span></>
          )}
        </div>
      </div>
      <div className="card-price" style={{ color }}>
        {s.price_pence.toFixed(1)}
        <span className="card-price-unit">p</span>
      </div>
    </div>
  )
}

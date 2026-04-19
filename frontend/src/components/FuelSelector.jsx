import { FUEL_COLORS, FUEL_SHORT, FUEL_SHORT2, FUEL_TYPES } from '../constants/fuels'
import './FuelSelector.css'

export default function FuelSelector({ value, onChange }) {
  return (
    <div className="fuel-selector">
      {FUEL_TYPES.map(f => (
        <button
          key={f}
          className={`fuel-btn ${value === f ? 'active' : ''}`}
          style={value === f ? {
            background: FUEL_COLORS[f] + '22',
            borderColor: FUEL_COLORS[f],
            color: FUEL_COLORS[f],
          } : {}}
          onClick={() => onChange(f)}
        >
          <span className="fuel-btn-main">{FUEL_SHORT[f]}</span>
          <span className="fuel-btn-sub">{FUEL_SHORT2[f]}</span>
        </button>
      ))}
    </div>
  )
}

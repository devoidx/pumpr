import './EvFilters.css'

const CONNECTOR_TYPES = [
  { label: 'All',      value: '' },
  { label: 'CCS',      value: 'CCS' },
  { label: 'CHAdeMO',  value: 'CHAdeMO' },
  { label: 'Type 2',   value: 'Type 2' },
  { label: 'Tesla',    value: 'Tesla' },
]

const SPEEDS = [
  { label: 'Any speed',    value: 0 },
  { label: '7kW+ Fast',    value: 7 },
  { label: '22kW+ Fast',   value: 22 },
  { label: '50kW+ Rapid',  value: 50 },
  { label: '100kW+ Ultra', value: 100 },
]

export default function EvFilters({ connector, onConnector, minPower, onMinPower, publicOnly, onPublicOnly, freeOnly, onFreeOnly, hideStale, onHideStale }) {
  return (
    <div className="ev-filters">
      <div className="ev-filter-group">
        {CONNECTOR_TYPES.map(t => (
          <button
            key={t.value}
            className={`ev-filter-btn ${connector === t.value ? 'active' : ''}`}
            onClick={() => onConnector(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="ev-filter-row2">
        <select
          className="ev-speed-select"
          value={minPower}
          onChange={e => onMinPower(Number(e.target.value))}
        >
          {SPEEDS.map(s => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
        <button
          className={`ev-filter-btn ${publicOnly ? 'active' : ''}`}
          onClick={() => onPublicOnly(!publicOnly)}
          title="Show only publicly accessible chargers"
        >
          Public
        </button>
        <button
          className={`ev-filter-btn ${freeOnly ? 'active' : ''}`}
          onClick={() => onFreeOnly(!freeOnly)}
          title="Show only free chargers"
        >
          Free
        </button>
        <button
          className={`ev-filter-btn ${hideStale ? 'active' : ''}`}
          onClick={() => onHideStale(!hideStale)}
          title="Hide chargers not verified in the last 2 years"
        >
          Verified
        </button>
      </div>
    </div>
  )
}

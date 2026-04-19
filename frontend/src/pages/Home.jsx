import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCheapest, getChargers } from '../api/client'
import Map from '../components/Map'
import StationCard from '../components/StationCard'
import ChargerCard from '../components/ChargerCard'
import FuelSelector from '../components/FuelSelector'
import ModeToggle from '../components/ModeToggle'
import EvFilters from '../components/EvFilters'
import LocationPrompt from '../components/LocationPrompt'
import PostcodeSearch from '../components/PostcodeSearch'
import './Home.css'

export default function Home() {
  const [location, setLocation] = useState(() => {
    const saved = localStorage.getItem('pumpr_location')
    return saved ? JSON.parse(saved) : null
  })
  const [mode, setMode] = useState(() => localStorage.getItem('pumpr_mode') || 'fuel')
  const [stations, setStations] = useState([])
  const [chargers, setChargers] = useState([])
  const [allChargers, setAllChargers] = useState([])
  const [fuel, setFuel] = useState(() => localStorage.getItem('pumpr_fuel') || 'E10')
  const [radius, setRadius] = useState(() => Number(localStorage.getItem('pumpr_radius')) || 8)
  const [units, setUnits] = useState(() => localStorage.getItem('pumpr_units') || 'miles')
  const [connector, setConnector] = useState('')
  const [minPower, setMinPower] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [hoveredId, setHoveredId] = useState(null)
  const navigate = useNavigate()

  const handleSetLocation = (loc) => {
    localStorage.setItem('pumpr_location', JSON.stringify(loc))
    setLocation(loc)
  }

  const handleClearLocation = () => {
    localStorage.removeItem('pumpr_location')
    setLocation(null)
  }

  const handleSetMode = (m) => {
    localStorage.setItem('pumpr_mode', m)
    setMode(m)
    if (m === 'ev') setStations([])
    if (m === 'fuel') setChargers([])
  }

  const handleSetFuel = (f) => {
    localStorage.setItem('pumpr_fuel', f)
    setFuel(f)
  }

  const toDisplay = (km) => units === 'miles' ? (km * 0.621371).toFixed(1) : km
  const unitLabel = units === 'miles' ? 'mi' : 'km'
  const radiusOptions = units === 'miles'
    ? [{ label: '2 mi', km: 3 }, { label: '5 mi', km: 8 }, { label: '10 mi', km: 16 }, { label: '15 mi', km: 24 }, { label: '25 mi', km: 40 }]
    : [{ label: '2 km', km: 2 }, { label: '5 km', km: 5 }, { label: '10 km', km: 10 }, { label: '15 km', km: 15 }, { label: '25 km', km: 25 }]

  const handleSetUnits = (u) => {
    localStorage.setItem('pumpr_units', u)
    setUnits(u)
    // Switch to nearest equivalent radius
    const milesOptions = [3, 8, 16, 24, 40]
    const kmOptions = [2, 5, 10, 15, 25]
    if (u === 'miles') {
      const nearest = milesOptions.reduce((a, b) => Math.abs(b - radius) < Math.abs(a - radius) ? b : a)
      setRadius(nearest)
      localStorage.setItem('pumpr_radius', nearest)
    } else {
      const nearest = kmOptions.reduce((a, b) => Math.abs(b - radius) < Math.abs(a - radius) ? b : a)
      setRadius(nearest)
      localStorage.setItem('pumpr_radius', nearest)
    }
  }

  const handleSetRadius = (r) => {
    localStorage.setItem('pumpr_radius', r)
    setRadius(r)
  }

  const fetchData = useCallback(() => {
    if (!location) return
    setLoading(true)
    setSelected(null)

    if (mode === 'fuel') {
      getCheapest(fuel, { lat: location.lat, lng: location.lng, radius_km: radius, limit: 50 })
        .then(r => setStations(r.data))
        .finally(() => setLoading(false))
    } else {
      getChargers({ lat: location.lat, lng: location.lng, radius_km: radius, limit: 100 })
        .then(r => {
          setAllChargers(r.data)
        })
        .finally(() => setLoading(false))
    }
  }, [location, mode, fuel, radius])

  // Apply EV filters client-side for instant response
  useEffect(() => {
    let filtered = allChargers
    if (connector) {
      filtered = filtered.filter(c =>
        c.connector_types.some(t => t.toLowerCase().includes(connector.toLowerCase()))
      )
    }
    if (minPower > 0) {
      filtered = filtered.filter(c => c.max_power_kw && c.max_power_kw >= minPower)
    }
    setChargers(filtered)
  }, [allChargers, connector, minPower])

  useEffect(() => { fetchData() }, [fetchData])

  const handleSelectItem = (item) => {
    setSelected(item)
    const id = mode === 'fuel' ? item.station_id : item.id
    const el = document.getElementById(`card-${id}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  if (!location) return <LocationPrompt onLocation={handleSetLocation} />

  const items = mode === 'fuel' ? stations : chargers
  const count = items.length

  return (
    <div className="home">
      <div className="panel">
        <div className="panel-header">
          <div className="panel-controls">
            <ModeToggle mode={mode} onChange={handleSetMode} />
            <select
              className="radius-select"
              value={radius}
              onChange={e => handleSetRadius(Number(e.target.value))}
            >
              {radiusOptions.map(r => (
                <option key={r.km} value={r.km}>{r.label}</option>
              ))}
            </select>
            <button
              className={`units-btn ${units === 'miles' ? 'active' : ''}`}
              onClick={() => handleSetUnits(units === 'miles' ? 'km' : 'miles')}
            >
              {units === 'miles' ? 'mi' : 'km'}
            </button>
          </div>
          <div className="panel-meta">
            {loading ? (
              <span className="loading-dot">Searching…</span>
            ) : (
              <span>
                {location.postcode ? `${location.postcode} · ` : ''}
                {count} {mode === 'fuel' ? 'stations' : 'chargers'} within {radiusOptions.find(r => r.km === radius)?.label || radius + unitLabel}
              </span>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <PostcodeSearch onLocation={handleSetLocation} />
              <button className="location-btn" onClick={handleClearLocation} title="Change location">📍</button>
            </div>
          </div>
        </div>

        {mode === 'fuel' && (
          <div className="fuel-filter-row">
            <FuelSelector value={fuel} onChange={handleSetFuel} />
          </div>
        )}
        {mode === 'ev' && (
          <EvFilters
            connector={connector}
            onConnector={setConnector}
            minPower={minPower}
            onMinPower={setMinPower}
          />
        )}

        <div className="station-list">
          {count === 0 && !loading && (
            <div className="empty-state">
              <p>No {mode === 'fuel' ? 'stations' : 'chargers'} found within {radiusOptions.find(r => r.km === radius)?.label || radius + unitLabel}</p>
              {mode === 'ev' && (connector || minPower > 0) && (
                <p style={{ marginTop: 8, fontSize: 12 }}>
                  Try clearing filters or increasing radius
                </p>
              )}
            </div>
          )}

          {mode === 'fuel' && stations.map((s, i) => (
            <StationCard units={units}
              key={s.station_id}
              station={s}
              rank={i}
              isSelected={selected?.station_id === s.station_id}
              isHovered={hoveredId === s.station_id}
              onClick={() => { setSelected(s); navigate(`/stations/${s.station_id}?fuel=${fuel}`) }}
              onHover={setHoveredId}
            />
          ))}

          {mode === 'ev' && chargers.map(c => (
            <ChargerCard
              key={c.id}
              charger={c}
              isSelected={selected?.id === c.id}
              isHovered={hoveredId === c.id}
              onClick={() => { setSelected(c); navigate(`/ev/${c.id}`) }}
              onHover={setHoveredId}
            />
          ))}
        </div>
      </div>

      <div className="map-container">
        <Map
          stations={stations}
          chargers={chargers}
          center={location}
          selectedId={mode === 'fuel' ? selected?.station_id : selected?.id}
          hoveredId={hoveredId}
          fuel={fuel}
          mode={mode}
          onSelect={handleSelectItem}
          onHover={setHoveredId}
        />
      </div>
    </div>
  )
}

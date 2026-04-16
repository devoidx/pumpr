import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCheapest } from '../api/client'
import Map from '../components/Map'
import StationCard from '../components/StationCard'
import FuelSelector from '../components/FuelSelector'
import LocationPrompt from '../components/LocationPrompt'
import './Home.css'

export default function Home() {
  const [location, setLocation] = useState(() => {
    const saved = localStorage.getItem('pumpr_location')
    return saved ? JSON.parse(saved) : null
  })
  const [stations, setStations] = useState([])
  const [fuel, setFuel] = useState('E10')
  const [radius, setRadius] = useState(5)
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

  const fetchStations = useCallback(() => {
    if (!location) return
    setLoading(true)
    getCheapest(fuel, {
      lat: location.lat,
      lng: location.lng,
      radius_km: radius,
      limit: 50,
    })
      .then(r => setStations(r.data))
      .finally(() => setLoading(false))
  }, [location, fuel, radius])

  useEffect(() => { fetchStations() }, [fetchStations])

  const handleSelectStation = (station) => {
    setSelected(station)
    const el = document.getElementById(`card-${station.station_id}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  if (!location) {
    return <LocationPrompt onLocation={handleSetLocation} />
  }

  return (
    <div className="home">
      <div className="panel">
        <div className="panel-header">
          <div className="panel-controls">
            <FuelSelector value={fuel} onChange={setFuel} />
            <select
              className="radius-select"
              value={radius}
              onChange={e => setRadius(Number(e.target.value))}
            >
              {[2, 5, 10, 15, 25].map(r => (
                <option key={r} value={r}>{r} km</option>
              ))}
            </select>
          </div>
          <div className="panel-meta">
            {loading ? (
              <span className="loading-dot">Searching…</span>
            ) : (
              <span>{stations.length} stations within {radius}km</span>
            )}
            <button className="location-btn" onClick={handleClearLocation}>
              📍 Change
            </button>
          </div>
        </div>

        <div className="station-list">
          {stations.length === 0 && !loading && (
            <div className="empty-state">
              <p>No stations found within {radius}km</p>
              <p>Try increasing the radius</p>
            </div>
          )}
          {stations.map((s, i) => (
            <StationCard
              key={s.station_id}
              station={s}
              rank={i}
              isSelected={selected?.station_id === s.station_id}
              isHovered={hoveredId === s.station_id}
              onClick={() => {
                setSelected(s)
                navigate(`/stations/${s.station_id}`)
              }}
              onHover={setHoveredId}
            />
          ))}
        </div>
      </div>

      <div className="map-container">
        <Map
          stations={stations}
          center={location}
          selectedId={selected?.station_id}
          hoveredId={hoveredId}
          fuel={fuel}
          onSelect={handleSelectStation}
          onHover={setHoveredId}
        />
      </div>
    </div>
  )
}

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSEO } from '../hooks/useSEO'
import { useAuth } from '../hooks/useAuth'
import { getEUNearby, getChargers } from '../api/client'
import EUMap from '../components/EUMap'

const COUNTRY_NAMES = { fr: 'France', de: 'Germany', es: 'Spain', it: 'Italy' }
const COUNTRY_CENTERS = {
  fr: { lat: 50.9513, lng: 1.8587, zoom: 9 },
  it: { lat: 45.4729, lng: 9.1754, zoom: 7 },
  es: { lat: 40.4146, lng: -3.6701, zoom: 6 },
  de: { lat: 51.1657, lng: 10.4515, zoom: 6 },
  es: { lat: 40.4637, lng: -3.7492, zoom: 6 },
  it: { lat: 41.8719, lng: 12.5674, zoom: 6 },
}
const FUEL_LABELS = { Diesel: 'Diesel', E5: 'Petrol (E5)', E10: 'Petrol (E10)' }
const FUEL_COLORS = { Diesel: '#3498db', E5: '#9b59b6', E10: '#2ecc71' }

export default function EuropeMapPage() {
  const { country = 'fr' } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isPro = user?.role === 'pro' || user?.role === 'admin'

  const countryName = COUNTRY_NAMES[country] || country.toUpperCase()
  const center = COUNTRY_CENTERS[country] || COUNTRY_CENTERS.fr

  useSEO({
    title: `${countryName} Fuel Map — Pumpr Pro`,
    description: `Interactive fuel price map for ${countryName}. Find the cheapest petrol and diesel near you.`,
    path: `/europe/map/${country}`,
    noindex: true, // map is a tool, not a content page — don't index
  })

  const [location, setLocation] = useState(center)
  const memoCenter = useMemo(() => location, [location.lat, location.lng, location.recenter])
  const [stations, setStations] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedFuel, setSelectedFuel] = useState('Diesel')
  const [radius, setRadius] = useState(25)
  const [selected, setSelected] = useState(null)
  const [hoveredId, setHoveredId] = useState(null)
  const [searchInput, setSearchInput] = useState('')
  const [locating, setLocating] = useState(false)

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      pos => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude, recenter: true })
        setLocating(false)
      },
      () => setLocating(false),
      { timeout: 10000 }
    )
  }
  const [searching, setSearching] = useState(false)
  const euMapRef = useRef(null)
  const [eurToGbp, setEurToGbp] = useState(null)
  const [chargers, setChargers] = useState([])
  const [showEV, setShowEV] = useState(false)

  // Redirect non-Pro users
  useEffect(() => {
    if (user !== undefined && !isPro) {
      navigate('/pro')
    }
  }, [user, isPro, navigate])

  const fetchChargers = useCallback(async () => {
    if (!location?.lat || !showEV) { setChargers([]); return }
    try {
      const resp = await getChargers({ lat: location.lat, lng: location.lng, radius_km: radius, limit: 100, country_code: country.toUpperCase() })
      setChargers(resp.data || [])
    } catch {
      setChargers([])
    }
  }, [location, radius, showEV])

  useEffect(() => { fetchChargers() }, [fetchChargers])

  const fetchStations = useCallback(async () => {
    if (!location?.lat) return
    setLoading(true)
    try {
      const resp = await getEUNearby({
        lat: location.lat,
        lng: location.lng,
        radius_km: radius,
        country: country.toUpperCase(),
        fuel_type: selectedFuel,
      })
      setStations(resp.data.stations || [])
      setEurToGbp(resp.data.eur_to_gbp)
    } catch {
      setStations([])
    } finally {
      setLoading(false)
    }
  }, [location, radius, country, selectedFuel])

  useEffect(() => { fetchStations() }, [fetchStations])

  const handleSearch = async () => {
    if (!searchInput.trim()) return
    setSearching(true)
    try {
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchInput + ', ' + countryName)}&format=json&limit=1`,
        { headers: { 'Accept-Language': 'en' } }
      )
      const results = await resp.json()
      if (results.length > 0) {
        const newLoc = { lat: parseFloat(results[0].lat), lng: parseFloat(results[0].lon), recenter: true }
    setLocation(newLoc)
      }
    } catch {
      // silently fail — user stays at current location
    } finally {
      setSearching(false)
    }
  }

  if (!isPro && user !== undefined) return null // redirecting

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Controls bar */}
      <div style={{
        padding: '10px 16px', background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap',
      }}>
        {/* Back */}
        <button
          onClick={() => navigate('/europe')}
          style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text2)', padding: '6px 12px', cursor: 'pointer', fontSize: '13px' }}
        >
          ← Europe
        </button>

        {/* Country flag */}
        <span style={{ fontSize: '18px' }}>
          {{ fr: '🇫🇷', de: '🇩🇪', es: '🇪🇸', it: '🇮🇹' }[country]}
        </span>

        {/* Location search */}
        <div style={{ display: 'flex', gap: '6px', flex: 1, minWidth: '180px' }}>
          <input
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder={`Search in ${countryName}…`}
            style={{
              flex: 1, padding: '6px 10px', borderRadius: '8px',
              border: '1px solid var(--border)', background: 'var(--bg)',
              color: 'var(--text)', fontSize: '13px',
            }}
          />
          <button
            onClick={handleSearch}
            disabled={searching}
            style={{ padding: '6px 12px', background: 'var(--amber)', color: '#000', fontWeight: 700, borderRadius: '8px', border: 'none', cursor: 'pointer', fontSize: '13px' }}
          >
            {searching ? '…' : 'Go'}
          </button>
        <button
          onClick={handleUseMyLocation}
          disabled={locating}
          title="Use my location"
          style={{ padding: '6px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text2)', cursor: 'pointer', fontSize: '13px', whiteSpace: 'nowrap' }}
        >
          {locating ? '…' : '📍 My location'}
        </button>
        </div>

        {/* Fuel selector */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {Object.keys(FUEL_LABELS).map(f => (
            <button
              key={f}
              onClick={() => setSelectedFuel(f)}
              style={{
                padding: '6px 12px', borderRadius: '8px', border: '1px solid',
                borderColor: selectedFuel === f ? FUEL_COLORS[f] : 'var(--border)',
                background: selectedFuel === f ? FUEL_COLORS[f] + '22' : 'var(--surface)',
                color: selectedFuel === f ? FUEL_COLORS[f] : 'var(--text2)',
                fontWeight: selectedFuel === f ? 700 : 400,
                cursor: 'pointer', fontSize: '12px',
              }}
            >
              {FUEL_LABELS[f]}
            </button>
          ))}
        </div>

        {/* Radius */}
        <select
          value={radius}
          onChange={e => setRadius(Number(e.target.value))}
          style={{ padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)', fontSize: '13px' }}
        >
          {[10, 25, 50, 100].map(r => (
            <option key={r} value={r}>{r} km</option>
          ))}
        </select>

        {/* EV toggle */}
        <button
          onClick={() => setShowEV(v => !v)}
          style={{
            padding: '6px 12px', borderRadius: '8px', border: '1px solid',
            borderColor: showEV ? '#2ecc71' : 'var(--border)',
            background: showEV ? 'rgba(46,204,113,0.15)' : 'var(--surface)',
            color: showEV ? '#2ecc71' : 'var(--text2)',
            cursor: 'pointer', fontSize: '12px', fontWeight: showEV ? 700 : 400,
          }}
        >
          ⚡ EV
        </button>

        {/* Station count */}
        <span style={{ color: 'var(--text3)', fontSize: '12px', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
          {loading ? 'Loading…' : `${stations.length} stations`}
        </span>

        {/* Rate */}
        {eurToGbp && (
          <span style={{ color: 'var(--text3)', fontSize: '12px', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
            £1 = €{(1 / eurToGbp).toFixed(4)}
          </span>
        )}
      </div>

      {/* Map */}
      <div style={{ flex: 1, position: 'relative' }}>
        <EUMap
          stations={stations}
          chargers={chargers}
          showChargers={showEV}
          center={memoCenter}
          selectedId={selected?.id}
          hoveredId={hoveredId}
          selectedFuel={selectedFuel}
          eurToGbp={eurToGbp}
          onSelect={setSelected}
          onHover={setHoveredId}
          onMapClick={setLocation}
        />
      </div>
    </div>
  )
}

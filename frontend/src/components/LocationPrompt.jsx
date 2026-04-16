import { useState } from 'react'
import './LocationPrompt.css'

export default function LocationPrompt({ onLocation }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleLocate = () => {
    setLoading(true)
    setError(null)
    navigator.geolocation.getCurrentPosition(
      pos => {
        onLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setLoading(false)
      },
      () => {
        setError('Location access denied. Please allow location in your browser.')
        setLoading(false)
      },
      { timeout: 10000 }
    )
  }

  return (
    <div className="location-prompt">
      <div className="lp-inner">
        <div className="lp-icon">⛽</div>
        <h1 className="lp-title">Pumpr</h1>
        <p className="lp-sub">Real-time UK fuel prices at 7,600+ stations</p>
        <div className="lp-divider" />
        <p className="lp-desc">
          Share your location to find the cheapest fuel near you,
          sorted by price and distance.
        </p>
        {error && <p className="lp-error">{error}</p>}
        <button
          className={`lp-btn ${loading ? 'loading' : ''}`}
          onClick={handleLocate}
          disabled={loading}
        >
          {loading ? <span className="lp-spinner" /> : '📍 Use my location'}
        </button>
        <p className="lp-privacy">Your location is never stored or shared</p>
      </div>
    </div>
  )
}

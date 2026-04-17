import { useState } from 'react'
import PumpIcon from './icons/PumpIcon'
import BoltIcon from './icons/BoltIcon'
import './LocationPrompt.css'

export default function LocationPrompt({ onLocation }) {
  const [loading, setLoading] = useState(false)
  const [postcode, setPostcode] = useState('')
  const [postcodeLoading, setPostcodeLoading] = useState(false)
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
        setError('Location access denied. Please allow location or enter a postcode.')
        setLoading(false)
      },
      { timeout: 10000 }
    )
  }

  const handlePostcode = async (e) => {
    e.preventDefault()
    const clean = postcode.trim().replace(/\s+/g, '').toUpperCase()
    if (!clean) return
    setPostcodeLoading(true)
    setError(null)
    try {
      const res = await fetch(`https://api.postcodes.io/postcodes/${clean}`)
      const data = await res.json()
      if (data.status === 200) {
        onLocation({ lat: data.result.latitude, lng: data.result.longitude, postcode: data.result.postcode })
      } else {
        setError('Postcode not found. Please check and try again.')
      }
    } catch {
      setError('Could not look up postcode. Please try again.')
    } finally {
      setPostcodeLoading(false)
    }
  }

  return (
    <div className="location-prompt">
      <div className="lp-inner">
        <div className="lp-icons">
          <PumpIcon size={40} color="#f5a623" />
          <BoltIcon size={32} color="#2ecc71" />
        </div>
        <h1 className="lp-title">Pumpr</h1>
        <p className="lp-sub">Real-time UK fuel prices at 7,600+ stations</p>
        <div className="lp-divider" />

        <button
          className={`lp-btn ${loading ? 'loading' : ''}`}
          onClick={handleLocate}
          disabled={loading || postcodeLoading}
        >
          {loading ? <span className="lp-spinner" /> : '📍 Use my location'}
        </button>

        <div className="lp-or"><span>or</span></div>

        <form className="lp-postcode-form" onSubmit={handlePostcode}>
          <input
            className="lp-postcode-input"
            type="text"
            placeholder="Enter postcode e.g. PE27 5EU"
            value={postcode}
            onChange={e => setPostcode(e.target.value)}
            disabled={loading || postcodeLoading}
            maxLength={8}
          />
          <button
            className="lp-postcode-btn"
            type="submit"
            disabled={loading || postcodeLoading || !postcode.trim()}
          >
            {postcodeLoading ? <span className="lp-spinner lp-spinner-dark" /> : '→'}
          </button>
        </form>

        {error && <p className="lp-error">{error}</p>}
        <p className="lp-privacy">Your location is never stored or shared</p>
      </div>
    </div>
  )
}

import { useState } from 'react'
import './PostcodeSearch.css'

export default function PostcodeSearch({ onLocation }) {
  const [postcode, setPostcode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const clean = postcode.trim().replace(/\s+/g, '').toUpperCase()
    if (!clean) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`https://api.postcodes.io/postcodes/${clean}`)
      const data = await res.json()
      if (data.status === 200) {
        onLocation({ lat: data.result.latitude, lng: data.result.longitude, postcode: data.result.postcode })
        setPostcode('')
      } else {
        setError('Not found')
      }
    } catch {
      setError('Error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="postcode-search" onSubmit={handleSubmit}>
      <input
        className={`ps-input ${error ? 'error' : ''}`}
        type="text"
        placeholder="Postcode…"
        value={postcode}
        onChange={e => { setPostcode(e.target.value); setError(null) }}
        maxLength={8}
        disabled={loading}
        title={error || ''}
      />
      <button className="ps-btn" type="submit" disabled={loading || !postcode.trim()}>
        {loading ? <span className="ps-spinner" /> : '🔍'}
      </button>
    </form>
  )
}

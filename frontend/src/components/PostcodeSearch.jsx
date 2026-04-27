import { useEffect, useRef, useState } from 'react'
import './PostcodeSearch.css'

function isPostcode(input) {
  return /^[A-Z]{1,2}[0-9][0-9A-Z]?(\s?[0-9][A-Z]{2})?$/i.test(input.trim())
}

export default function PostcodeSearch({ onLocation }) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const debounceRef = useRef(null)
  const wrapperRef = useRef(null)

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Debounced place lookup
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const q = query.trim()
    if (!q || isPostcode(q) || q.length < 2) {
      setSuggestions([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`https://api.postcodes.io/places?q=${encodeURIComponent(q)}&limit=8`)
        const data = await res.json()
        if (data.status === 200 && data.result?.length > 0) {
          setSuggestions(data.result)
          setShowSuggestions(true)
        } else {
          setSuggestions([])
        }
      } catch {
        setSuggestions([])
      }
    }, 300)
  }, [query])

  function selectSuggestion(place) {
    // Zoom level based on place type
    const zoomByType = {
      'Village': 14, 'Hamlet': 15, 'Small Town': 13,
      'Town': 13, 'Suburban Area': 13, 'Urban Area': 12,
      'City': 11, 'Capital City': 10,
    }
    const zoom = zoomByType[place.local_type] || 13
    onLocation({ lat: place.latitude, lng: place.longitude, postcode: place.name_1, zoom })
    setQuery('')
    setSuggestions([])
    setShowSuggestions(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const clean = query.trim()
    if (!clean) return

    // If suggestions showing, pick first one
    if (suggestions.length > 0 && !isPostcode(clean)) {
      selectSuggestion(suggestions[0])
      return
    }

    setLoading(true)
    setError(null)
    try {
      if (isPostcode(clean)) {
        const res = await fetch(`https://api.postcodes.io/postcodes/${clean.replace(/\s+/g, '').toUpperCase()}`)
        const data = await res.json()
        if (data.status === 200) {
          onLocation({ lat: data.result.latitude, lng: data.result.longitude, postcode: data.result.postcode })
          setQuery('')
        } else {
          setError('Not found')
        }
      } else {
        setError('Select a place from the list')
      }
    } catch {
      setError('Error')
    } finally {
      setLoading(false)
    }
  }

  function placeLabel(place) {
    const parts = [place.local_type]
    if (place.county_unitary) parts.push(place.county_unitary)
    else if (place.region) parts.push(place.region)
    return parts.join(', ')
  }

  return (
    <div className="postcode-search-wrap" ref={wrapperRef}>
      <form className="postcode-search" onSubmit={handleSubmit}>
        <input
          className={`ps-input ${error ? 'error' : ''}`}
          type="text"
          placeholder="Town or postcode"
          value={query}
          onChange={e => { setQuery(e.target.value); setError(null) }}
          maxLength={50}
          disabled={loading}
          title={error || ''}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          autoComplete="off"
        />
        <button className="ps-btn" type="submit" disabled={loading || !query.trim()}>
          {loading ? <span className="ps-spinner" /> : '🔍'}
        </button>
      </form>
      {showSuggestions && suggestions.length > 0 && (
        <div className="ps-suggestions">
          {suggestions.map((place, i) => (
            <button
              key={i}
              className="ps-suggestion-item"
              onMouseDown={() => selectSuggestion(place)}
            >
              <span className="ps-suggestion-name">{place.name_1}</span>
              <span className="ps-suggestion-meta">{placeLabel(place)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

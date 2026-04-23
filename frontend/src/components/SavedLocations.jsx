import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import './SavedLocations.css'

const TYPE_ICON = { home: '🏠', work: '🏢', custom: '📍' }

export default function SavedLocations({ onSelect }) {
  const { isAuthenticated, user, authFetch } = useAuth()
  const [open, setOpen]           = useState(false)
  const [locations, setLocations] = useState([])
  const [loading, setLoading]     = useState(false)
  const ref                       = useRef(null)

  const isPro = user?.role === 'pro' || user?.role === 'admin'

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    if (!open || !isPro) return
    setLoading(true)
    authFetch('/api/v1/locations')
      .then(r => r.json())
      .then(data => setLocations(Array.isArray(data) ? data : []))
      .catch(() => setLocations([]))
      .finally(() => setLoading(false))
  }, [open, isPro, authFetch])

  function handleSelect(loc) {
    onSelect({ lat: loc.lat, lng: loc.lng, postcode: loc.postcode, label: loc.label })
    setOpen(false)
  }

  // Not logged in — don't render
  if (!isAuthenticated) return null

  return (
    <div className="saved-locations" ref={ref}>
      <button
        className={`sl-trigger ${!isPro ? 'sl-locked' : ''}`}
        onClick={() => setOpen(o => !o)}
        title={isPro ? 'Saved locations' : 'Saved locations — Pro feature'}
      >
        {isPro ? '📍' : '🔒'} Locations
        {isPro && locations.length > 0 && (
          <span className="sl-count">{locations.length}</span>
        )}
      </button>

      {open && (
        <div className="sl-dropdown">
          {!isPro ? (
            <div className="sl-pro-prompt">
              <span className="sl-lock-icon">🔒</span>
              <p>Saved locations is a <strong>Pro</strong> feature.</p>
              <a href="/pro" className="sl-pro-link">Go Pro →</a>
            </div>
          ) : loading ? (
            <div className="sl-empty">Loading…</div>
          ) : locations.length === 0 ? (
            <div className="sl-empty">
              No saved locations yet.
              <a href="/my-places" className="sl-manage-link">Add one →</a>
            </div>
          ) : (
            <>
              {locations.map(loc => (
                <button key={loc.id} className="sl-item" onClick={() => handleSelect(loc)}>
                  <span className="sl-item-icon">{TYPE_ICON[loc.type] || '📍'}</span>
                  <span className="sl-item-label">{loc.label}</span>
                  {loc.postcode && <span className="sl-item-postcode">{loc.postcode}</span>}
                </button>
              ))}
              <a href="/my-places" className="sl-manage-link">Manage locations →</a>
            </>
          )}
        </div>
      )}
    </div>
  )
}

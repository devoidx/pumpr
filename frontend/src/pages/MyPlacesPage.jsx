import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './MyPlacesPage.css'

const TYPE_ICON  = { home: '🏠', work: '🏢', custom: '📍' }
const TYPE_LABEL = { home: 'Home',  work: 'Work',  custom: 'Custom' }

export default function MyPlacesPage() {
  const { user, isAuthenticated, loading: authLoading, authFetch } = useAuth()
  const navigate = useNavigate()
  const isPro = user?.role === 'pro' || user?.role === 'admin'

  const [locations, setLocations]   = useState([])
  const [loading, setLoading]       = useState(false)
  const [showModal, setShowModal]   = useState(false)
  const [editTarget, setEditTarget] = useState(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) { navigate('/'); return }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    if (!isPro) return
    fetchLocations()
  }, [isPro])

  async function fetchLocations() {
    setLoading(true)
    try {
      const r = await authFetch('/api/v1/locations')
      const data = await r.json()
      setLocations(Array.isArray(data) ? data : [])
    } finally {
      setLoading(false)
    }
  }

  async function deleteLocation(id) {
    await authFetch(`/api/v1/locations/${id}`, { method: 'DELETE' })
    setLocations(l => l.filter(x => x.id !== id))
  }

  function openAdd() { setEditTarget(null); setShowModal(true) }
  function openEdit(loc) { setEditTarget(loc); setShowModal(true) }

  return (
    <div className="profile-page">
      <div className="profile-inner">
        <h1 className="profile-title">My Places</h1>



        {/* Saved locations */}
        <div className="profile-section">
          <div className="profile-section-header">
            <h2>Saved Locations</h2>
            {isPro && locations.length < 10 && (
              <button className="profile-add-btn" onClick={openAdd}>+ Add</button>
            )}
          </div>

          {!isPro ? (
            <div className="profile-pro-gate">
              <span>🔒</span>
              <p>Saved locations are a <strong>Pro</strong> feature. <a href="/pro">Go Pro →</a></p>
            </div>
          ) : loading ? (
            <p className="profile-loading">Loading…</p>
          ) : locations.length === 0 ? (
            <p className="profile-empty">No saved locations yet. Add your home or work to jump straight to local prices.</p>
          ) : (
            <div className="profile-location-list">
              {locations.map(loc => (
                <div key={loc.id} className="profile-location-row">
                  <span className="pll-icon">{TYPE_ICON[loc.type]}</span>
                  <div className="pll-info">
                    <span className="pll-label">{loc.label}</span>
                    <span className="pll-meta">
                      {TYPE_LABEL[loc.type]}
                      {loc.postcode && ` · ${loc.postcode}`}
                      {loc.has_home_charger && ' · 🔌 Home charger'}
                    </span>
                  </div>
                  <div className="pll-actions">
                    <button className="pll-btn" onClick={() => openEdit(loc)}>Edit</button>
                    <button className="pll-btn danger" onClick={() => deleteLocation(loc.id)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <LocationModal
          existing={editTarget}
          existingTypes={locations.map(l => l.type)}
          authFetch={authFetch}
          onSave={(loc) => {
            if (editTarget) {
              setLocations(l => l.map(x => x.id === loc.id ? loc : x))
            } else {
              setLocations(l => [...l, loc])
            }
            setShowModal(false)
          }}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  )
}


function LocationModal({ existing, existingTypes, authFetch, onSave, onClose }) {
  const [label, setLabel]               = useState(existing?.label || '')
  const [type, setType]                 = useState(existing?.type || 'custom')
  const [postcode, setPostcode]         = useState(existing?.postcode || '')
  const [lat, setLat]                   = useState(existing?.lat || null)
  const [lng, setLng]                   = useState(existing?.lng || null)
  const [hasCharger, setHasCharger]     = useState(existing?.has_home_charger || false)
  const [lookingUp, setLookingUp]       = useState(false)
  const [postcodeErr, setPostcodeErr]   = useState('')
  const [saving, setSaving]             = useState(false)
  const [error, setError]               = useState('')

  // Auto-set label when type changes
  useEffect(() => {
    if (!existing && type !== 'custom') setLabel(type.charAt(0).toUpperCase() + type.slice(1))
  }, [type, existing])

  async function lookupPostcode() {
    const clean = postcode.trim().replace(/\s+/g, '').toUpperCase()
    if (!clean) return
    setLookingUp(true)
    setPostcodeErr('')
    try {
      const res = await fetch(`https://api.postcodes.io/postcodes/${clean}`)
      const data = await res.json()
      if (data.status === 200) {
        setLat(data.result.latitude)
        setLng(data.result.longitude)
        setPostcode(data.result.postcode)
        setPostcodeErr('')
      } else {
        setPostcodeErr('Postcode not found')
      }
    } catch {
      setPostcodeErr('Lookup failed')
    } finally {
      setLookingUp(false)
    }
  }

  async function handleSave(e) {
    e.preventDefault()
    if (!lat || !lng) { setError('Please look up a postcode first'); return }
    setSaving(true); setError('')
    try {
      const method = existing ? 'PATCH' : 'POST'
      const url    = existing ? `/api/v1/locations/${existing.id}` : '/api/v1/locations'
      const res    = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label, type, lat, lng, postcode, has_home_charger: hasCharger }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Save failed')
      onSave(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const takenTypes = existingTypes.filter(t => t !== existing?.type)

  return (
    <div className="lm-overlay" onClick={onClose}>
      <div className="lm-modal" onClick={e => e.stopPropagation()}>
        <button className="lm-close" onClick={onClose}>✕</button>
        <h2>{existing ? 'Edit location' : 'Add location'}</h2>

        <form onSubmit={handleSave} className="lm-form">
          {error && <p className="lm-error">{error}</p>}

          <label>Type</label>
          <div className="lm-type-row">
            {['home', 'work', 'custom'].map(t => (
              <button
                key={t}
                type="button"
                className={`lm-type-btn ${type === t ? 'active' : ''} ${takenTypes.includes(t) && t !== 'custom' ? 'taken' : ''}`}
                onClick={() => !takenTypes.includes(t) && setType(t)}
                disabled={takenTypes.includes(t) && t !== 'custom'}
                title={takenTypes.includes(t) ? `You already have a ${t} location` : ''}
              >
                {TYPE_ICON[t]} {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          <label>Label</label>
          <input
            type="text"
            value={label}
            onChange={e => setLabel(e.target.value)}
            placeholder={type === 'custom' ? "e.g. Mum's house" : type.charAt(0).toUpperCase() + type.slice(1)}
            maxLength={50}
            required
          />

          <label>Postcode</label>
          <div className="lm-postcode-row">
            <input
              type="text"
              value={postcode}
              onChange={e => { setPostcode(e.target.value); setLat(null); setLng(null) }}
              placeholder="e.g. PE27 5EU"
              maxLength={8}
            />
            <button type="button" className="lm-lookup-btn" onClick={lookupPostcode} disabled={lookingUp || !postcode.trim()}>
              {lookingUp ? '…' : 'Look up'}
            </button>
          </div>
          {postcodeErr && <p className="lm-field-err">{postcodeErr}</p>}
          {lat && lng && <p className="lm-coords">✓ {lat.toFixed(4)}, {lng.toFixed(4)}</p>}

          {type === 'home' && (
            <label className="lm-checkbox-row">
              <input type="checkbox" checked={hasCharger} onChange={e => setHasCharger(e.target.checked)} />
              I have a home EV charger
            </label>
          )}

          <button type="submit" className="lm-save-btn" disabled={saving || !lat || !lng}>
            {saving ? 'Saving…' : existing ? 'Save changes' : 'Add location'}
          </button>
        </form>
      </div>
    </div>
  )
}

const TYPE_ICON2 = { home: '🏠', work: '🏢', custom: '📍' }

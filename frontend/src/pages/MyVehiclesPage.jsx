import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import './MyVehiclesPage.css'

const FUEL_LABELS = {
  PETROL: '⛽ Petrol',
  DIESEL: '🚛 Diesel',
  ELECTRIC: '⚡ Electric',
  'HYBRID ELECTRIC': '🔋 Hybrid',
  'PLUG-IN HYBRID ELECTRIC': '🔋 Plug-in Hybrid',
}

const FUEL_DEFAULTS = {
  PETROL: { tank_litres: 50, mpg: 45 },
  DIESEL: { tank_litres: 60, mpg: 55 },
  ELECTRIC: { tank_litres: null, mpg: null, miles_per_kwh: 3.5 },
  'HYBRID ELECTRIC': { tank_litres: 45, mpg: 60 },
  'PLUG-IN HYBRID ELECTRIC': { tank_litres: 45, mpg: 50 },
}

function VehicleCard({ vehicle, onActivate, onEdit, onDelete }) {
  return (
    <div className={`mv-card ${vehicle.is_active ? 'mv-card-active' : ''}`}>
      <div className="mv-card-header">
        <div className="mv-card-title">
          <span className="mv-reg">{vehicle.registration}</span>
          {vehicle.nickname && <span className="mv-nickname">"{vehicle.nickname}"</span>}
          {vehicle.is_active && <span className="mv-active-badge">Active</span>}
        </div>
        <div className="mv-card-actions">
          {!vehicle.is_active && (
            <button className="mv-btn mv-btn-ghost" onClick={() => onActivate(vehicle.id)}>
              Set active
            </button>
          )}
          <button className="mv-btn mv-btn-ghost" onClick={() => onEdit(vehicle)}>Edit</button>
          <button className="mv-btn mv-btn-danger" onClick={() => onDelete(vehicle.id)}>✕</button>
        </div>
      </div>
      <div className="mv-card-body">
        {(vehicle.make || vehicle.model || vehicle.year) && (
          <div className="mv-detail">
            🚗 {[vehicle.year, vehicle.make, vehicle.model].filter(Boolean).join(' ')}
            {vehicle.colour && ` · ${vehicle.colour}`}
          </div>
        )}
        {vehicle.fuel_type && (
          <div className="mv-detail">{FUEL_LABELS[vehicle.fuel_type] || vehicle.fuel_type}</div>
        )}
        <div className="mv-stats">
          {vehicle.tank_litres && <span>🪣 {vehicle.tank_litres}L tank</span>}
          {vehicle.mpg && <span>⚡ {vehicle.mpg} MPG</span>}
          {vehicle.miles_per_kwh && <span>⚡ {vehicle.miles_per_kwh} mi/kWh</span>}
        </div>
      </div>
    </div>
  )
}

function VehicleForm({ initial, onSave, onCancel, accessToken }) {
  const [reg, setReg] = useState(initial?.registration || '')
  const [form, setForm] = useState(initial || {})
  const [looking, setLooking] = useState(false)
  const [looked, setLooked] = useState(!!initial)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [lookupSource, setLookupSource] = useState(null)

  const isEV = form.fuel_type === 'ELECTRIC'

  async function lookup() {
    if (!reg.trim()) return
    setLooking(true)
    setError(null)
    try {
      const res = await fetch(`/api/v1/vehicles/lookup/${reg.trim().toUpperCase().replace(/\s/g, '')}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Lookup failed')
      const defaults = FUEL_DEFAULTS[data.fuel_type?.toUpperCase()] || {}
      setForm(f => ({
        ...f,
        registration: data.registration,
        make: data.make || f.make || '',
        model: data.model || f.model || '',
        year: data.year || f.year || '',
        colour: data.colour || f.colour || '',
        fuel_type: data.fuel_type || f.fuel_type || 'PETROL',
        tank_litres: data.tank_litres ?? defaults.tank_litres ?? f.tank_litres ?? 50,
        mpg: data.mpg ?? defaults.mpg ?? f.mpg ?? 45,
        miles_per_kwh: data.miles_per_kwh ?? defaults.miles_per_kwh ?? f.miles_per_kwh ?? null,
      }))
      setLookupSource(data.source || null)
      setLooked(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLooking(false)
    }
  }

  function set(field, val) {
    setForm(f => {
      const next = { ...f, [field]: val }
      if (field === 'fuel_type') {
        const defaults = FUEL_DEFAULTS[val?.toUpperCase()] || {}
        next.tank_litres = defaults.tank_litres ?? f.tank_litres
        next.mpg = defaults.mpg ?? f.mpg
        next.miles_per_kwh = defaults.miles_per_kwh ?? f.miles_per_kwh
      }
      return next
    })
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      await onSave({
        registration: (form.registration || reg).toUpperCase().replace(/\s/g, ''),
        nickname: form.nickname || null,
        make: form.make || null,
        model: form.model || null,
        year: form.year ? parseInt(form.year) : null,
        colour: form.colour || null,
        fuel_type: form.fuel_type || 'PETROL',
        tank_litres: form.tank_litres ? parseFloat(form.tank_litres) : null,
        mpg: form.mpg ? parseFloat(form.mpg) : null,
        miles_per_kwh: form.miles_per_kwh ? parseFloat(form.miles_per_kwh) : null,
      })
    } catch (e) {
      setError(e.message)
      setSaving(false)
    }
  }

  return (
    <div className="mv-form">
      <h3 className="mv-form-title">{initial ? 'Edit Vehicle' : 'Add Vehicle'}</h3>

      {!initial && (
        <div className="mv-lookup-row">
          <input
            className="mv-input mv-reg-input"
            placeholder="Registration e.g. AB12 CDE"
            value={reg}
            onChange={e => setReg(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && lookup()}
          />
          <button className="mv-btn mv-btn-primary" onClick={lookup} disabled={looking}>
            {looking ? 'Looking up…' : 'Look up'}
          </button>
        </div>
      )}

      {looked && (
        <>
          {lookupSource === 'dvla' && (
            <div className="mv-hint mv-dvla-note">
              ℹ️ Make, year, colour and fuel type were pulled from DVLA. Model is not available from DVLA — please enter it manually. Economy figures are estimates based on fuel type — update them for accurate savings calculations.
            </div>
          )}
          <div className="mv-form-grid">
            <label>Nickname (optional)
              <input className="mv-input" placeholder='e.g. "My Golf"' value={form.nickname || ''} onChange={e => set('nickname', e.target.value)} />
            </label>
            <label>Make
              <input className="mv-input" placeholder="e.g. Volkswagen" value={form.make || ''} onChange={e => set('make', e.target.value)} />
            </label>
            <label>Model
              <input className="mv-input" placeholder="e.g. Golf" value={form.model || ''} onChange={e => set('model', e.target.value)} />
            </label>
            <label>Year
              <input className="mv-input" type="number" placeholder="e.g. 2020" value={form.year || ''} onChange={e => set('year', e.target.value)} />
            </label>
            <label>Colour
              <input className="mv-input" placeholder="e.g. Blue" value={form.colour || ''} onChange={e => set('colour', e.target.value)} />
            </label>
            <label>Fuel type
              <select className="mv-input" value={form.fuel_type || 'PETROL'} onChange={e => set('fuel_type', e.target.value)}>
                <option value="PETROL">Petrol</option>
                <option value="DIESEL">Diesel</option>
                <option value="ELECTRIC">Electric</option>
                <option value="HYBRID ELECTRIC">Hybrid</option>
                <option value="PLUG-IN HYBRID ELECTRIC">Plug-in Hybrid</option>
              </select>
            </label>
          </div>
          {!isEV && (
            <div className="mv-economy-row">
              <label>
                Tank size (litres)
                <span className="mv-hint">Typical: 40–70L. Check your manual if unsure. We assume you'll fill up with 5L remaining rather than running dry.</span>
                <input className="mv-input" type="number" min="10" max="150" value={form.tank_litres || ''} onChange={e => set('tank_litres', e.target.value)} />
              </label>
              <label>
                Fuel economy (MPG)
                <span className="mv-hint">Your real-world MPG. Typical: 35–60 for petrol, 45–70 for diesel.</span>
                <input className="mv-input" type="number" min="10" max="200" value={form.mpg || ''} onChange={e => set('mpg', e.target.value)} />
              </label>
            </div>
          )}
          {isEV && (
            <div className="mv-economy-row">
              <label>
                Efficiency (miles/kWh)
                <span className="mv-hint">Typical EV: 3–4 mi/kWh. Check your car's display or manual.</span>
                <input className="mv-input" type="number" min="1" max="10" step="0.1" value={form.miles_per_kwh || ''} onChange={e => set('miles_per_kwh', e.target.value)} />
              </label>
            </div>
          )}
          {error && <p className="mv-error">{error}</p>}
          <div className="mv-form-btns">
            <button className="mv-btn mv-btn-ghost" onClick={onCancel}>Cancel</button>
            <button className="mv-btn mv-btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save vehicle'}
            </button>
          </div>
        </>
      )}
      {!looked && error && <p className="mv-error">{error}</p>}
    </div>
  )
}

export default function MyVehiclesPage() {
  const { accessToken } = useAuth()
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState(null)

  async function load() {
    try {
      const res = await fetch('/api/v1/vehicles', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      setVehicles(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleSave(body) {
    const url = editing ? `/api/v1/vehicles/${editing.id}` : '/api/v1/vehicles'
    const method = editing ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Save failed')
    setAdding(false)
    setEditing(null)
    load()
  }

  async function handleActivate(id) {
    await fetch(`/api/v1/vehicles/${id}/activate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    load()
  }

  async function handleDelete(id) {
    if (!window.confirm('Remove this vehicle?')) return
    await fetch(`/api/v1/vehicles/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    load()
  }

  return (
    <div className="mv-page">
      <div className="mv-inner">
        <div className="mv-header">
          <div>
            <h1 className="mv-title">My Vehicles</h1>
            <p className="mv-sub">Your active vehicle is used to calculate fuel costs and savings.</p>
          </div>
          {!adding && !editing && vehicles.length < 10 && (
            <button className="mv-btn mv-btn-primary" onClick={() => setAdding(true)}>+ Add vehicle</button>
          )}
        </div>

        {error && <p className="mv-error">{error}</p>}

        {(adding || editing) && (
          <VehicleForm
            initial={editing}
            accessToken={accessToken}
            onSave={handleSave}
            onCancel={() => { setAdding(false); setEditing(null) }}
          />
        )}

        {loading ? (
          <p className="mv-loading">Loading vehicles…</p>
        ) : vehicles.length === 0 && !adding ? (
          <div className="mv-empty">
            <div className="mv-empty-icon">🚗</div>
            <p>No vehicles yet. Add your first vehicle to get personalised fuel cost estimates.</p>
            <button className="mv-btn mv-btn-primary" onClick={() => setAdding(true)}>Add my first vehicle</button>
          </div>
        ) : (
          <div className="mv-list">
            {vehicles.map(v => (
              <VehicleCard
                key={v.id}
                vehicle={v}
                onActivate={handleActivate}
                onEdit={setEditing}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {vehicles.length >= 10 && (
          <p className="mv-limit">Maximum 10 vehicles reached.</p>
        )}
      </div>
    </div>
  )
}

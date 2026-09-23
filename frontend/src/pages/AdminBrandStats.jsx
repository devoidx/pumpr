import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useSEO } from '../hooks/useSEO'

export default function AdminBrandStats() {
  useSEO({ noindex: true, path: '/admin/brand-stats' })
  const { user, accessToken } = useAuth()
  const [brands, setBrands] = useState([])
  const [contacts, setContacts] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [stations, setStations] = useState({})
  const [stationsLoading, setStationsLoading] = useState(null)
  const [editingEmail, setEditingEmail] = useState(null)
  const [emailDraft, setEmailDraft] = useState('')
  const [saving, setSaving] = useState(false)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [statsRes, contactsRes] = await Promise.all([
        fetch('/api/v1/admin/brand-stats', { headers: { Authorization: 'Bearer ' + accessToken } }),
        fetch('/api/v1/admin/brand-stats/contacts', { headers: { Authorization: 'Bearer ' + accessToken } }),
      ])
      if (!statsRes.ok || !contactsRes.ok) throw new Error('Failed to load')
      const statsData = await statsRes.json()
      const contactsData = await contactsRes.json()
      setBrands(statsData.brands)
      const byName = {}
      for (const c of contactsData.contacts) byName[c.brand_name] = c
      setContacts(byName)
    } catch {
      setError('Failed to load brand stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.role === 'admin') load()
  }, [user])

  async function toggleExpand(brandName) {
    if (expanded === brandName) {
      setExpanded(null)
      return
    }
    setExpanded(brandName)
    if (!stations[brandName]) {
      setStationsLoading(brandName)
      try {
        const res = await fetch(`/api/v1/admin/brand-stats/stations?brand=${encodeURIComponent(brandName)}&days=14`, {
          headers: { Authorization: 'Bearer ' + accessToken },
        })
        if (!res.ok) throw new Error('Failed')
        const data = await res.json()
        setStations(s => ({ ...s, [brandName]: data.stations }))
      } catch {
        setStations(s => ({ ...s, [brandName]: [] }))
      } finally {
        setStationsLoading(null)
      }
    }
  }

  function startEditEmail(brandName) {
    setEditingEmail(brandName)
    setEmailDraft(contacts[brandName]?.contact_email || '')
  }

  async function saveEmail(brandName) {
    setSaving(true)
    try {
      const res = await fetch('/api/v1/admin/brand-stats/contacts', {
        method: 'PUT',
        headers: { Authorization: 'Bearer ' + accessToken, 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_name: brandName, contact_email: emailDraft || null, notes: contacts[brandName]?.notes || null }),
      })
      if (!res.ok) throw new Error('Failed')
      const updated = await res.json()
      setContacts(c => ({ ...c, [brandName]: updated }))
      setEditingEmail(null)
    } catch {
      alert('Failed to save contact email')
    } finally {
      setSaving(false)
    }
  }

  if (!user) return <div style={{ padding: '32px', color: 'var(--text2)' }}>Loading…</div>
  if (user.role !== 'admin') return <div style={{ padding: '32px', color: 'var(--text2)' }}>Not authorized.</div>

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '32px 20px' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '26px', marginBottom: '20px' }}>
        Brand Staleness ({brands.length})
      </h1>

      {loading && <div style={{ color: 'var(--text2)' }}>Loading…</div>}
      {error && <div style={{ color: 'var(--red)' }}>{error}</div>}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {brands.map(b => (
          <div key={b.brand} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '14px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: '200px' }}>
                <button
                  onClick={() => toggleExpand(b.brand)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '13px', color: 'var(--text3)', padding: '2px' }}
                >
                  {expanded === b.brand ? '▼' : '▶'}
                </button>
                <span style={{ fontWeight: 600, fontSize: '15px' }}>{b.brand}</span>
                <span style={{ fontSize: '12px', color: 'var(--text3)' }}>
                  {b.E10_stations || b.B7_stations || 0} stations
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px' }}>
                <span style={{ color: b.stale_rate_21d > 5 ? '#e74c3c' : b.stale_rate_21d > 2 ? '#f5a623' : 'var(--text3)' }}>
                  {b.stale_rate_21d}% stale (21d+)
                </span>
                <span style={{ color: 'var(--text3)' }}>{b.update_rate_7d}% fresh (7d)</span>
              </div>
            </div>

            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
              <span style={{ color: 'var(--text3)' }}>Contact:</span>
              {editingEmail === b.brand ? (
                <>
                  <input
                    type="email"
                    value={emailDraft}
                    onChange={e => setEmailDraft(e.target.value)}
                    placeholder="contact@brand.com"
                    style={{ flex: 1, maxWidth: '280px', padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--border2)', background: 'var(--bg)', color: 'var(--text)', fontSize: '13px' }}
                  />
                  <button onClick={() => saveEmail(b.brand)} disabled={saving} style={{ background: 'var(--amber)', color: '#000', border: 'none', borderRadius: '4px', padding: '4px 10px', fontSize: '12px', cursor: 'pointer' }}>
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                  <button onClick={() => setEditingEmail(null)} style={{ background: 'none', border: '1px solid var(--border2)', borderRadius: '4px', padding: '4px 10px', fontSize: '12px', cursor: 'pointer', color: 'var(--text2)' }}>
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <span style={{ color: contacts[b.brand]?.contact_email ? 'var(--text)' : 'var(--text3)' }}>
                    {contacts[b.brand]?.contact_email || 'Not set'}
                  </span>
                  <button onClick={() => startEditEmail(b.brand)} style={{ background: 'none', border: 'none', color: 'var(--amber)', fontSize: '12px', cursor: 'pointer', padding: '2px 6px' }}>
                    Edit
                  </button>
                </>
              )}
            </div>

            {expanded === b.brand && (
              <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                {stationsLoading === b.brand && <div style={{ color: 'var(--text3)', fontSize: '13px' }}>Loading stations…</div>}
                {stations[b.brand]?.length === 0 && stationsLoading !== b.brand && (
                  <div style={{ color: 'var(--text3)', fontSize: '13px' }}>No stations stale past 14 days.</div>
                )}
                {stations[b.brand]?.map(s => (
                  <div key={s.station_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '13px', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <a href={`/stations/${s.station_id}`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text)', fontWeight: 500 }}>{s.name}</a>
                      <span style={{ color: 'var(--text3)' }}> · {s.postcode}</span>
                    </div>
                    <div style={{ color: '#e74c3c' }}>
                      {Math.max(...s.stale_fuels.map(f => f.days_stale))} days stale
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

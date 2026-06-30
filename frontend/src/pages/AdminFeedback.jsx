import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useSEO } from '../hooks/useSEO'

export default function AdminFeedback() {
  useSEO({ noindex: true, path: '/admin/feedback' })
  const { user, accessToken } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/feedback/admin/list', {
        headers: { Authorization: 'Bearer ' + accessToken },
      })
      if (!res.ok) throw new Error('Failed to load')
      const data = await res.json()
      setItems(data.items)
    } catch {
      setError('Failed to load feedback')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.role === 'admin') load()
  }, [user])

  async function handleDelete(id) {
    if (!confirm('Delete this feedback?')) return
    try {
      const res = await fetch(`/api/v1/feedback/admin/${id}`, {
        method: 'DELETE',
        headers: { Authorization: 'Bearer ' + accessToken },
      })
      if (!res.ok) throw new Error('Failed to delete')
      setItems(items => items.filter(i => i.id !== id))
    } catch {
      alert('Failed to delete')
    }
  }

  if (!user) return <div style={{ padding: '32px', color: 'var(--text2)' }}>Loading…</div>
  if (user.role !== 'admin') return <div style={{ padding: '32px', color: 'var(--text2)' }}>Not authorized.</div>

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '32px 20px' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '26px', marginBottom: '20px' }}>
        Feedback ({items.length})
      </h1>

      {loading && <div style={{ color: 'var(--text2)' }}>Loading…</div>}
      {error && <div style={{ color: 'var(--red)' }}>{error}</div>}

      {!loading && items.length === 0 && (
        <div style={{ color: 'var(--text3)' }}>No feedback yet.</div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {items.map(item => (
          <div
            key={item.id}
            style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', padding: '16px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '14px' }}>
                  {item.name || 'Anonymous'} <span style={{ color: 'var(--text3)', fontWeight: 400 }}>· {item.email}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>
                  {new Date(item.created_at).toLocaleString('en-GB')}
                  {item.page_url && <> · <a href={item.page_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text3)' }}>{item.page_url}</a></>}
                </div>
              </div>
              <button
                onClick={() => handleDelete(item.id)}
                style={{
                  background: 'none', border: '1px solid var(--border2)', color: 'var(--red)',
                  borderRadius: '6px', padding: '4px 10px', fontSize: '12px', cursor: 'pointer'
                }}
              >
                Delete
              </button>
            </div>
            <div style={{ fontSize: '14px', color: 'var(--text)', whiteSpace: 'pre-wrap' }}>
              {item.message}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

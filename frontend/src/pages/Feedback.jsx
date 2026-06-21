import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

export default function Feedback() {
  const location = useLocation()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState(null) // null | 'sending' | 'sent' | 'error'

  useEffect(() => {
    if (typeof umami !== 'undefined') umami.track('feedback-page-viewed')
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('sending')
    try {
      const res = await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name || null,
          email,
          message,
          page_url: window.location.origin + location.pathname,
        }),
      })
      if (!res.ok) throw new Error('Failed')
      setStatus('sent')
      setName('')
      setEmail('')
      setMessage('')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div style={{ maxWidth: '560px', margin: '0 auto', padding: '32px 20px' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '28px', marginBottom: '8px' }}>
        Send us feedback
      </h1>
      <p style={{ color: 'var(--text2)', fontSize: '14px', marginBottom: '28px' }}>
        Spotted a bug, got a feature idea, or just want to say hello? We read every message.
      </p>

      {status === 'sent' ? (
        <div style={{
          background: 'var(--surface)', border: '1px solid var(--green)', borderRadius: 'var(--radius)',
          padding: '20px', color: 'var(--text)', fontSize: '14px'
        }}>
          ✅ Thanks — your feedback has been sent. We appreciate it!
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', color: 'var(--text2)', marginBottom: '6px' }}>
              Name (optional)
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 'var(--radius)',
                border: '1px solid var(--border2)', background: 'var(--surface)', color: 'var(--text)',
                fontSize: '14px', boxSizing: 'border-box'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', color: 'var(--text2)', marginBottom: '6px' }}>
              Email <span style={{ color: 'var(--text3)' }}>(required so we can reply)</span>
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 'var(--radius)',
                border: '1px solid var(--border2)', background: 'var(--surface)', color: 'var(--text)',
                fontSize: '14px', boxSizing: 'border-box'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', color: 'var(--text2)', marginBottom: '6px' }}>
              Your feedback
            </label>
            <textarea
              required
              rows={6}
              value={message}
              onChange={e => setMessage(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 'var(--radius)',
                border: '1px solid var(--border2)', background: 'var(--surface)', color: 'var(--text)',
                fontSize: '14px', fontFamily: 'var(--font-body)', resize: 'vertical', boxSizing: 'border-box'
              }}
            />
          </div>
          {status === 'error' && (
            <div style={{ color: 'var(--red)', fontSize: '13px' }}>
              Something went wrong — please try again, or email us directly.
            </div>
          )}
          <button
            type="submit"
            disabled={status === 'sending'}
            style={{
              background: 'var(--amber)', color: '#000', border: 'none', borderRadius: 'var(--radius)',
              padding: '12px 20px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
              opacity: status === 'sending' ? 0.6 : 1
            }}
          >
            {status === 'sending' ? 'Sending…' : 'Send feedback'}
          </button>
        </form>
      )}
    </div>
  )
}

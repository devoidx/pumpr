import { useNavigate } from 'react-router-dom'

export default function ProSuccessPage() {
  const navigate = useNavigate()

  return (
    <div style={{ alignItems: 'center', background: 'var(--bg)', display: 'flex', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, maxWidth: 480, padding: '2.5rem 2rem', textAlign: 'center', width: '100%' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⛽✓</div>
        <h2 style={{ color: 'var(--amber)', fontSize: '1.6rem', fontWeight: 800, margin: '0 0 0.75rem' }}>Payment successful!</h2>

        <div style={{ background: 'rgba(245,166,35,0.1)', border: '1px solid rgba(245,166,35,0.3)', borderRadius: 8, padding: '1rem 1.25rem', marginBottom: '1.5rem', textAlign: 'left' }}>
          <p style={{ color: 'var(--amber)', fontWeight: 700, margin: '0 0 0.5rem', fontSize: '0.95rem' }}>📧 Check your email</p>
          <p style={{ color: '#a0a0a8', margin: 0, lineHeight: 1.6, fontSize: '0.9rem' }}>
            We've sent you a link to set your password and activate your Pumpr Pro account.
            <strong style={{ color: 'var(--text)' }}> Your Pro features won't be active until you complete this step.</strong>
          </p>
        </div>

        <p style={{ color: 'var(--text3)', fontSize: '0.85rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
          Can't find the email? Check your spam folder. The link expires in 24 hours.
          If you already have a Pumpr account, your subscription has been upgraded automatically — just sign in.
        </p>

        <button
          onClick={() => navigate('/')}
          style={{ background: 'var(--amber)', border: 'none', borderRadius: 8, color: '#000', cursor: 'pointer', fontWeight: 700, padding: '0.7rem 1.5rem' }}
        >
          Go to map
        </button>
      </div>
    </div>
  )
}

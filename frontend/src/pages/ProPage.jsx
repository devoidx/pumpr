import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './ProPage.css'

const MONTHLY_PRICE_ID = 'price_1TP0qNFSIwexZJECmABnb9ah'
const ANNUAL_PRICE_ID  = 'price_1TP0qiFSIwexZJECIzFODDj1'

const BENEFITS = [
  { icon: '★', title: 'Favourite stations',    description: 'Save your most-used stations for instant access.' },
  { icon: '🔔', title: 'Price alerts',          description: 'Get notified when fuel drops below a price you set.' },
  { icon: '📍', title: 'Home location',         description: 'Set a home postcode and always see the cheapest fuel near you first.' },
  { icon: '📊', title: 'Extended price history',description: 'Up to 12 months of price history per station.' },
  { icon: '🔑', title: 'API access',            description: 'Query Pumpr data with a personal API key.' },
  { icon: '⚡', title: 'Early access',          description: 'New features before anyone else.' },
]

export default function ProPage() {
  const navigate              = useNavigate()
  const { isAuthenticated, accessToken } = useAuth()
  const [billing, setBilling] = useState('annual')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  async function handleSubscribe() {
    if (!isAuthenticated) {
      // store intent and redirect — NavAuthSection will handle login
      sessionStorage.setItem('post_login_redirect', '/pro')
      navigate('/pro')
      // trigger login modal by dispatching a custom event
      window.dispatchEvent(new CustomEvent('pumpr:open-login'))
      return
    }

    setLoading(true)
    setError('')
    try {
      const price_id = billing === 'monthly' ? MONTHLY_PRICE_ID : ANNUAL_PRICE_ID
      const res = await fetch('/api/v1/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ price_id }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Could not start checkout')
      window.location.href = data.checkout_url
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const monthlyTotal = '£2.99'
  const annualTotal  = '£24.99'
  const annualMonthly = '£2.08'

  return (
    <div className="pro-page">
      <div className="pro-hero">
        <div className="pro-hero-badge">Available now</div>
        <h1>Pumpr <span className="pro-highlight">Pro</span></h1>
        <p className="pro-hero-sub">
          Everything you need to stop overpaying for fuel.
        </p>

        {/* Billing toggle */}
        <div className="pro-billing-toggle">
          <button
            className={`pro-toggle-btn ${billing === 'monthly' ? 'active' : ''}`}
            onClick={() => setBilling('monthly')}
          >
            Monthly
          </button>
          <button
            className={`pro-toggle-btn ${billing === 'annual' ? 'active' : ''}`}
            onClick={() => setBilling('annual')}
          >
            Annual <span className="pro-save-badge">Save 30%</span>
          </button>
        </div>

        {/* Price display */}
        <div className="pro-price-display">
          {billing === 'monthly' ? (
            <><span className="pro-price-amount">{monthlyTotal}</span><span className="pro-price-period">/month</span></>
          ) : (
            <>
              <span className="pro-price-amount">{annualMonthly}</span>
              <span className="pro-price-period">/month</span>
              <div className="pro-price-sub">billed annually at {annualTotal}</div>
            </>
          )}
        </div>

        {error && <p className="pro-error">{error}</p>}

        <button className="pro-subscribe-btn" onClick={handleSubscribe} disabled={loading}>
          {loading ? 'Redirecting…' : 'Get Pumpr Pro'}
        </button>

        <p className="pro-cancel-note">Cancel any time. No commitment.</p>
      </div>

      <div className="pro-benefits">
        {BENEFITS.map(b => (
          <div key={b.title} className="pro-benefit-card">
            <div className="pro-benefit-icon">{b.icon}</div>
            <div>
              <h3>{b.title}</h3>
              <p>{b.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="pro-footer-note">
        Payments handled securely by Stripe. Built and maintained by one person — thanks for your support ⛽
      </div>
    </div>
  )
}

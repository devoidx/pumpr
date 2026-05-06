import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './ProPage.css'

const MONTHLY_PRICE_ID = 'price_1TU6vtFThYVN7wEdDTNWtnKe'
const ANNUAL_PRICE_ID  = 'price_1TU6vpFThYVN7wEd4pJd4NNW'

const BENEFITS = [
  { icon: '📍', title: 'Saved locations',       description: 'Save your home, work, or anywhere else and instantly search fuel prices nearby.', live: true },
  { icon: '🚗', title: 'Vehicle profiles',      description: 'Add your vehicles and see personalised fill costs and real savings based on your tank size and fuel economy.', live: true },
  { icon: '🗺️', title: 'Driving distances',     description: 'See real driving distance and time to the top 10 nearest stations, not just straight-line.', live: true },
  { icon: '💰', title: 'Smart savings',         description: "Know exactly how much you'll save — or spend — driving to a cheaper station, including the fuel cost to get there.", live: true },
  { icon: '🔔', title: 'Price alerts',          description: 'Get notified by email when fuel at your local station drops below a price you set.', live: false },
  { icon: '⚡', title: 'Early access',          description: 'New features land for Pro users first.', live: true },
]

export default function ProPage() {
  const navigate              = useNavigate()
  const { isAuthenticated, accessToken } = useAuth()
  const [billing, setBilling] = useState('annual')

  useEffect(() => {
    if (typeof umami !== 'undefined') umami.track('pro-page-view')
  }, [])
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  async function handleSubscribe() {
    setLoading(true)
    setError('')
    try {
      const price_id = billing === 'monthly' ? MONTHLY_PRICE_ID : ANNUAL_PRICE_ID
      const endpoint = isAuthenticated
        ? '/api/v1/stripe/create-checkout-session'
        : '/api/v1/stripe/create-checkout-session-public'
      const headers = { 'Content-Type': 'application/json' }
      if (isAuthenticated && accessToken) headers['Authorization'] = `Bearer ${accessToken}`
      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({ price_id }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Could not start checkout')
      if (typeof umami !== 'undefined') umami.track('checkout-started', { billing })
      window.location.href = data.checkout_url
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const monthlyTotal = '£1.99'
  const annualTotal  = '£20.00'
  const annualMonthly = '£1.67'

  return (
    <div className="pro-page">
      <div className="pro-hero">
        <div className="pro-hero-badge">Now available</div>
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
            Annual <span className="pro-save-badge">Save 16%</span>
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
          {loading ? 'Redirecting…' : billing === 'monthly' ? 'Subscribe — £1.99/mo' : 'Subscribe — £20/yr'}
        </button>

        <p className="pro-cancel-note">Cancel anytime. Payments handled securely by Stripe.</p>
      </div>

      <div className="pro-benefits">
        {BENEFITS.map(b => (
          <div key={b.title} className="pro-benefit-card">
            <div className="pro-benefit-icon">{b.icon}</div>
            <div>
              <h3>{b.title} {b.live ? <span className="pro-live-badge">Live</span> : <span className="pro-soon-badge">Coming soon</span>}</h3>
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

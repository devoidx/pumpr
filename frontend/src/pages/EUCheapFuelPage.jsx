import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSEO } from '../hooks/useSEO'

const FUEL_LABELS = { Diesel: 'Diesel', E5: 'Petrol (E5)', E10: 'Petrol (E10)' }
const FUEL_COLORS = { Diesel: '#3498db', E5: '#9b59b6', E10: '#2ecc71' }

const COUNTRY_NAMES = { FR: 'France', DE: 'Germany', ES: 'Spain', IT: 'Italy' }

function toTitleCase(str) {
  return str.replace(/-/g, ' ').replace(/\w\S*/g, t => t.charAt(0).toUpperCase() + t.slice(1).toLowerCase())
}

function formatEur(price) {
  return `€${price.toFixed(3)}`
}

function formatGbp(price) {
  // Convert EUR/litre to pence/litre for UK travellers
  return `${(price * 100).toFixed(1)}p`
}

export default function EUCheapFuelPage() {
  const { country, city } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [selectedFuel, setSelectedFuel] = useState('Diesel')

  const cityName = toTitleCase(city)
  const countryName = COUNTRY_NAMES[country?.toUpperCase()] || country

  useSEO({
    title: `Cheap Fuel in ${cityName}, ${countryName} — Prices for UK Travellers`,
    description: `Compare petrol and diesel prices at stations near ${cityName}, ${countryName}. Prices shown in EUR and GBP for UK drivers.`,
    path: `/cheap-fuel/europe/${country}/${city}`,
  })

  useEffect(() => {
    setLoading(true)
    setNotFound(false)
    fetch(`/api/v1/eu/cheap-fuel/${country}/${city}`)
      .then(r => { if (!r.ok) throw new Error('not found'); return r.json() })
      .then(d => {
        setData(d)
        // Default to Diesel if available, else first fuel type returned
        const fuels = Object.keys(d.cheapest)
        if (fuels.includes('Diesel')) setSelectedFuel('Diesel')
        else if (fuels.length > 0) setSelectedFuel(fuels[0])
        setLoading(false)
      })
      .catch(() => { setNotFound(true); setLoading(false) })
  }, [country, city])

  if (loading) return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 16px', color: 'var(--text2)' }}>
      Loading fuel prices for {cityName}...
    </div>
  )

  if (notFound) return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 16px', textAlign: 'center' }}>
      <h1 style={{ color: 'var(--text)', marginBottom: '8px' }}>City not found</h1>
      <p style={{ color: 'var(--text2)', marginBottom: '24px' }}>
        We don't have fuel price data for "{cityName}" yet.
      </p>
      <button
        onClick={() => navigate('/')}
        style={{ background: 'var(--amber)', color: '#000', fontWeight: 700, padding: '10px 24px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}
      >
        Back to map
      </button>
    </div>
  )

  const { cheapest, stats, eur_to_gbp } = data
  const stations = cheapest[selectedFuel] || []
  const localStats = stats[selectedFuel]

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px 16px', overflowY: 'auto' }}>

      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ color: 'var(--text3)', fontSize: '12px', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
          ⛽ Pumpr · {countryName}
        </p>
        <h1 style={{ color: 'var(--text)', fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
          Cheap Fuel in {cityName}, {countryName}
        </h1>
        <p style={{ color: 'var(--text2)', fontSize: '14px', lineHeight: 1.7 }}>
          Petrol and diesel prices for UK travellers near {cityName}.
          {eur_to_gbp && (
            <> Prices shown in EUR and GBP at today's rate of <strong style={{ color: 'var(--amber)' }}>£1 = €{(1 / eur_to_gbp).toFixed(4)}</strong>.</>
          )}
        </p>
      </div>

      {/* Fuel selector */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {Object.keys(FUEL_LABELS).map(f => (
          stats[f] && (
            <button
              key={f}
              onClick={() => setSelectedFuel(f)}
              style={{
                padding: '8px 16px', borderRadius: '8px', border: '1px solid',
                borderColor: selectedFuel === f ? FUEL_COLORS[f] : 'var(--border2)',
                background: selectedFuel === f ? FUEL_COLORS[f] + '22' : 'var(--surface)',
                color: selectedFuel === f ? FUEL_COLORS[f] : 'var(--text2)',
                fontWeight: selectedFuel === f ? 700 : 400,
                cursor: 'pointer', fontSize: '13px',
              }}
            >
              {FUEL_LABELS[f]} · {formatEur(stats[f].avg)}
            </button>
          )
        ))}
      </div>

      {/* Stats bar */}
      {localStats && (
        <div style={{
          display: 'flex', gap: '16px', flexWrap: 'wrap', padding: '12px 16px',
          background: 'var(--surface)', borderRadius: '10px', border: '1px solid var(--border)',
          marginBottom: '20px', fontSize: '13px', fontFamily: 'var(--font-mono)'
        }}>
          <span style={{ color: 'var(--text2)' }}>Lowest: <strong style={{ color: '#2ecc71' }}>{formatEur(localStats.min)}</strong></span>
          <span style={{ color: 'var(--text2)' }}>Average: <strong style={{ color: 'var(--amber)' }}>{formatEur(localStats.avg)}</strong></span>
          <span style={{ color: 'var(--text2)' }}>Highest: <strong style={{ color: '#e74c3c' }}>{formatEur(localStats.max)}</strong></span>
          <span style={{ color: 'var(--text2)' }}>{localStats.count} stations</span>
          {eur_to_gbp && (
            <span style={{ color: 'var(--text3)' }}>
              ≈ {formatGbp(localStats.avg)} avg in GBP
            </span>
          )}
        </div>
      )}

      {/* Station list */}
      <h2 style={{ color: 'var(--text)', fontSize: '16px', marginBottom: '12px' }}>
        Cheapest {FUEL_LABELS[selectedFuel]} near {cityName}
      </h2>

      {stations.length === 0 ? (
        <p style={{ color: 'var(--text3)' }}>No stations found near {cityName}.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '32px' }}>
          {stations.map((s, i) => (
            <div
              key={s.external_id}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)',
                borderRadius: '10px', gap: '12px', transition: 'border-color 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--amber)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                <span style={{
                  fontSize: '11px', fontWeight: 700,
                  color: i === 0 ? '#2ecc71' : 'var(--text3)',
                  fontFamily: 'var(--font-mono)', flexShrink: 0, width: '20px'
                }}>#{i + 1}</span>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text)', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.name || s.address}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>
                    {s.city} {s.postcode} · {(s.distance_km * 0.621371).toFixed(1)} mi
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ color: FUEL_COLORS[selectedFuel], fontWeight: 700, fontSize: '20px', fontFamily: 'var(--font-mono)' }}>
                  {formatEur(s.price_eur)}
                </div>
                {s.price_gbp && (
                  <div style={{ color: 'var(--text3)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                    ≈ {formatGbp(s.price_gbp)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Data freshness note */}
      <p style={{ color: 'var(--text3)', fontSize: '11px', fontFamily: 'var(--font-mono)', marginBottom: '24px' }}>
        Prices updated daily from official government data. Last station update shown per station where available.
      </p>

      {/* CTA */}
      <div style={{
        padding: '24px', background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: '12px', textAlign: 'center'
      }}>
        <h3 style={{ color: 'var(--text)', marginBottom: '8px' }}>Find cheap fuel near you in the UK</h3>
        <p style={{ color: 'var(--text2)', fontSize: '13px', marginBottom: '16px' }}>
          Use the Pumpr map for live UK fuel prices updated every 30 minutes.
        </p>
        <button
          onClick={() => navigate('/')}
          style={{ background: 'var(--amber)', color: '#000', fontWeight: 700, padding: '10px 28px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontSize: '14px' }}
        >
          Open map →
        </button>
      </div>
    </div>
  )
}

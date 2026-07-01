import { useNavigate } from 'react-router-dom'
import { useSEO } from '../hooks/useSEO'
import { useAuth } from '../hooks/useAuth'

const FRANCE_CITIES = [
  { slug: 'calais',           name: 'Calais' },
  { slug: 'boulogne-sur-mer', name: 'Boulogne-sur-Mer' },
  { slug: 'dunkirk',          name: 'Dunkirk' },
  { slug: 'lille',            name: 'Lille' },
  { slug: 'rouen',            name: 'Rouen' },
  { slug: 'paris',            name: 'Paris' },
  { slug: 'reims',            name: 'Reims' },
  { slug: 'le-havre',         name: 'Le Havre' },
  { slug: 'caen',             name: 'Caen' },
  { slug: 'rennes',           name: 'Rennes' },
  { slug: 'saint-malo',       name: 'Saint-Malo' },
  { slug: 'bordeaux',         name: 'Bordeaux' },
  { slug: 'toulouse',         name: 'Toulouse' },
  { slug: 'lyon',             name: 'Lyon' },
  { slug: 'nice',             name: 'Nice' },
  { slug: 'marseille',        name: 'Marseille' },
]

const ITALY_CITIES = [
  { slug: 'rome',      name: 'Rome' },
  { slug: 'milan',     name: 'Milan' },
  { slug: 'turin',     name: 'Turin' },
  { slug: 'naples',    name: 'Naples' },
  { slug: 'palermo',   name: 'Palermo' },
  { slug: 'genoa',     name: 'Genoa' },
  { slug: 'florence',  name: 'Florence' },
  { slug: 'bologna',   name: 'Bologna' },
  { slug: 'catania',   name: 'Catania' },
  { slug: 'verona',    name: 'Verona' },
  { slug: 'venice',    name: 'Venice' },
  { slug: 'bari',      name: 'Bari' },
]

export default function EuropePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const isPro = user?.role === 'pro' || user?.role === 'admin'

  useSEO({
    title: 'European Fuel Prices for UK Travellers — Pumpr',
    description: 'Find cheap petrol and diesel prices in France for UK drivers. Compare station prices in EUR and GBP, updated daily from official government data.',
    path: '/europe',
  })

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', padding: '32px 16px' }}>

      {/* Header */}
      <p style={{ color: 'var(--text3)', fontSize: '12px', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
        ⛽ Pumpr · Europe
      </p>
      <h1 style={{ color: 'var(--text)', fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
        European Fuel Prices for UK Travellers
      </h1>
      <p style={{ color: 'var(--text2)', fontSize: '14px', lineHeight: 1.7, marginBottom: '32px' }}>
        Planning a driving holiday? Compare petrol and diesel prices at stations across France,
        shown in both EUR and GBP. Updated daily from official government data.
      </p>

      {/* France section */}
      <div style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <span style={{ fontSize: '22px' }}>🇫🇷</span>
          <h2 style={{ color: 'var(--text)', fontSize: '18px', fontWeight: 700, margin: 0 }}>France</h2>
        </div>

        {/* City grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
          gap: '8px',
          marginBottom: '24px',
        }}>
          {FRANCE_CITIES.map(city => (
            <button
              key={city.slug}
              onClick={() => navigate(`/cheap-fuel/europe/fr/${city.slug}`)}
              style={{
                padding: '12px 16px',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '10px',
                color: 'var(--text)',
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'border-color 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--amber)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              {city.name}
            </button>
          ))}
        </div>

        {/* Pro map teaser */}
        {isPro ? (
          <button
            onClick={() => navigate('/europe/map/fr')}
            style={{
              width: '100%', padding: '16px',
              background: 'rgba(245,166,35,0.1)',
              border: '1px solid var(--amber)',
              borderRadius: '12px', cursor: 'pointer',
              color: 'var(--amber)', fontWeight: 700, fontSize: '14px',
            }}
          >
            🗺 Open France fuel map →
          </button>
        ) : (
          <div style={{
            padding: '20px 24px',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: '16px', flexWrap: 'wrap',
          }}>
            <div>
              <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
                🗺 Interactive fuel map — Pumpr Pro
              </div>
              <div style={{ color: 'var(--text2)', fontSize: '13px' }}>
                See all French stations on a live map. Search anywhere in France, not just these cities.
              </div>
            </div>
            <button
              onClick={() => navigate('/pro')}
              style={{
                padding: '10px 20px', background: 'var(--amber)',
                color: '#000', fontWeight: 700, fontSize: '13px',
                borderRadius: '8px', border: 'none', cursor: 'pointer',
                whiteSpace: 'nowrap', flexShrink: 0,
              }}
            >
              Upgrade to Pro →
            </button>
          </div>
        )}
      </div>
      {/* Italy section */}
      <div style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <span style={{ fontSize: '22px' }}>🇮🇹</span>
          <h2 style={{ color: 'var(--text)', fontSize: '18px', fontWeight: 700, margin: 0 }}>Italy</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '8px', marginBottom: '24px' }}>
          {ITALY_CITIES.map(city => (
            <button
              key={city.slug}
              onClick={() => navigate(`/cheap-fuel/europe/it/${city.slug}`)}
              style={{ padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '10px', color: 'var(--text)', fontSize: '14px', fontWeight: 500, cursor: 'pointer', textAlign: 'left', transition: 'border-color 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--amber)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              {city.name}
            </button>
          ))}
        </div>
      </div>

      {/* Italy Pro map teaser */}
      <div style={{ marginBottom: '40px' }}>
        {isPro ? (
          <button
            onClick={() => navigate('/europe/map/it')}
            style={{
              width: '100%', padding: '16px',
              background: 'rgba(245,166,35,0.1)',
              border: '1px solid var(--amber)',
              borderRadius: '12px', cursor: 'pointer',
              color: 'var(--amber)', fontWeight: 700, fontSize: '14px',
            }}
          >
            🗺 Open Italy fuel map →
          </button>
        ) : (
          <div style={{
            padding: '20px 24px',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: '16px', flexWrap: 'wrap',
          }}>
            <div>
              <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
                🗺 Interactive fuel map — Pumpr Pro
              </div>
              <div style={{ color: 'var(--text2)', fontSize: '13px' }}>
                See all Italian stations on a live map. Search anywhere in Italy.
              </div>
            </div>
            <button
              onClick={() => navigate('/pro')}
              style={{
                padding: '10px 20px', background: 'var(--amber)',
                color: '#000', fontWeight: 700, fontSize: '13px',
                borderRadius: '8px', border: 'none', cursor: 'pointer',
                whiteSpace: 'nowrap', flexShrink: 0,
              }}
            >
              Upgrade to Pro →
            </button>
          </div>
        )}
      </div>

      {/* Coming soon */}
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ color: 'var(--text2)', fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
          Coming soon
        </h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {[
            { flag: '🇩🇪', name: 'Germany' },
            { flag: '🇪🇸', name: 'Spain' },
          ].map(c => (
            <div key={c.name} style={{
              padding: '10px 16px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '10px',
              color: 'var(--text3)',
              fontSize: '14px',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              <span>{c.flag}</span>
              <span>{c.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Data note */}
      <p style={{ color: 'var(--text3)', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
        Prices sourced from official government open data. Updated daily. GBP conversion uses ECB daily reference rate.
      </p>
    </div>
  )
}

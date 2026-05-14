import { useEffect, useState } from 'react'
import { useSEO } from '../hooks/useSEO'
import { useParams, useNavigate } from 'react-router-dom'
import { useBrandLogos } from '../contexts/BrandsContext'
import { timeAgo } from '../utils/timeAgo'

const FUEL_LABELS = { E10: 'Petrol (E10)', B7: 'Diesel (B7)', E5: 'Premium (E5)' }
const FUEL_COLORS = { E10: '#2ecc71', B7: '#3498db', E5: '#9b59b6' }

function toTitleCase(str) {
  return str.replace(/-/g, ' ').replace(/\w\S*/g, t => t.charAt(0).toUpperCase() + t.slice(1).toLowerCase())
}

export default function CheapFuelPage() {
  const { location } = useParams()
  const navigate = useNavigate()
  const brandLogos = useBrandLogos()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [selectedFuel, setSelectedFuel] = useState('E10')

  const locationName = toTitleCase(location)
  useSEO({ title: `Cheap Petrol & Diesel in ${locationName}`, description: `Compare live fuel prices at petrol stations near ${locationName}. Find the cheapest petrol and diesel updated every 30 minutes.`, path: `/cheap-fuel/${location}` })

  useEffect(() => {
    setLoading(true)
    setNotFound(false)
    fetch('/api/v1/locations/cheap-fuel/' + location)
      .then(r => { if (!r.ok) throw new Error('not found'); return r.json() })
      .then(d => { setData(d); setLoading(false) })
      .catch(() => { setNotFound(true); setLoading(false) })
  }, [location])

  if (loading) return (
    <div style={{maxWidth:'800px', margin:'0 auto', padding:'40px 16px', color:'var(--text2)'}}>
      Loading fuel prices for {locationName}...
    </div>
  )

  if (notFound) return (
    <div style={{maxWidth:'800px', margin:'0 auto', padding:'40px 16px', textAlign:'center'}}>
      <h1 style={{color:'var(--text)', marginBottom:'8px'}}>Location not found</h1>
      <p style={{color:'var(--text2)', marginBottom:'24px'}}>We couldn't find fuel price data for "{locationName}".</p>
      <button onClick={() => navigate('/')} style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px 24px', borderRadius:'8px', border:'none', cursor:'pointer'}}>Find fuel near me</button>
    </div>
  )

  const { location: place, cheapest, stats, national } = data
  const stations = cheapest[selectedFuel] || []
  const localStats = stats[selectedFuel]
  const natAvg = national[selectedFuel]

  return (
    <div style={{maxWidth:'800px', margin:'0 auto', padding:'24px 16px', overflowY:'auto'}}>
      {/* Header */}
      <div style={{marginBottom:'24px'}}>
        <p style={{color:'var(--text3)', fontSize:'12px', fontFamily:'var(--font-mono)', marginBottom:'4px'}}>
          ⛽ Pumpr · {place.region || place.country}
        </p>
        <h1 style={{color:'var(--text)', fontSize:'28px', fontWeight:700, marginBottom:'8px'}}>
          Cheap Petrol & Diesel in {place.name}
        </h1>
        <p style={{color:'var(--text2)', fontSize:'14px', lineHeight:1.7}}>
          Compare live fuel prices at petrol stations near {place.name}.
          {localStats && natAvg && (
            <> The average {FUEL_LABELS[selectedFuel]} price in {place.name} is <strong style={{color:'var(--amber)'}}>{localStats.avg}p/litre</strong>
            {localStats.avg < natAvg
              ? <> — <strong style={{color:'#2ecc71'}}>{(natAvg - localStats.avg).toFixed(1)}p cheaper</strong> than the UK average of {natAvg}p.</>
              : <> — <strong style={{color:'#e74c3c'}}>{(localStats.avg - natAvg).toFixed(1)}p more expensive</strong> than the UK average of {natAvg}p.</>
            }</>
          )}
        </p>
      </div>

      {/* Fuel selector */}
      <div style={{display:'flex', gap:'8px', marginBottom:'20px', flexWrap:'wrap'}}>
        {Object.keys(FUEL_LABELS).map(f => (
          stats[f] && (
            <button
              key={f}
              onClick={() => setSelectedFuel(f)}
              style={{
                padding:'8px 16px', borderRadius:'8px', border:'1px solid',
                borderColor: selectedFuel === f ? FUEL_COLORS[f] : 'var(--border2)',
                background: selectedFuel === f ? FUEL_COLORS[f] + '22' : 'var(--surface)',
                color: selectedFuel === f ? FUEL_COLORS[f] : 'var(--text2)',
                fontWeight: selectedFuel === f ? 700 : 400,
                cursor:'pointer', fontSize:'13px',
              }}
            >
              {FUEL_LABELS[f]} · {stats[f].avg}p avg
            </button>
          )
        ))}
      </div>

      {/* Stats bar */}
      {localStats && (
        <div style={{
          display:'flex', gap:'16px', flexWrap:'wrap', padding:'12px 16px',
          background:'var(--surface)', borderRadius:'10px', border:'1px solid var(--border)',
          marginBottom:'20px', fontSize:'13px', fontFamily:'var(--font-mono)'
        }}>
          <span style={{color:'var(--text2)'}}>Lowest: <strong style={{color:'#2ecc71'}}>{localStats.min}p</strong></span>
          <span style={{color:'var(--text2)'}}>Average: <strong style={{color:'var(--amber)'}}>{localStats.avg}p</strong></span>
          <span style={{color:'var(--text2)'}}>Highest: <strong style={{color:'#e74c3c'}}>{localStats.max}p</strong></span>
          <span style={{color:'var(--text2)'}}>{localStats.count} stations</span>
          {natAvg && <span style={{color:'var(--text3)'}}>UK avg: {natAvg}p</span>}
        </div>
      )}

      {/* Station list */}
      <h2 style={{color:'var(--text)', fontSize:'16px', marginBottom:'12px'}}>
        Cheapest {FUEL_LABELS[selectedFuel]} near {place.name}
      </h2>
      {stations.length === 0 ? (
        <p style={{color:'var(--text3)'}}>No stations found near {place.name}.</p>
      ) : (
        <div style={{display:'flex', flexDirection:'column', gap:'8px', marginBottom:'32px'}}>
          {stations.map((s, i) => {
            const logo = s.brand ? brandLogos[s.brand.toUpperCase()] : null
            return (
              <div
                key={s.station_id}
                onClick={() => navigate('/stations/' + s.station_id + '?fuel=' + selectedFuel)}
                style={{
                  display:'flex', alignItems:'center', justifyContent:'space-between',
                  padding:'12px 16px', background:'var(--surface)', border:'1px solid var(--border)',
                  borderRadius:'10px', cursor:'pointer', gap:'12px',
                  transition:'border-color 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--amber)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <div style={{display:'flex', alignItems:'center', gap:'10px', minWidth:0}}>
                  <span style={{
                    fontSize:'11px', fontWeight:700, color: i === 0 ? '#2ecc71' : 'var(--text3)',
                    fontFamily:'var(--font-mono)', flexShrink:0, width:'20px'
                  }}>#{i+1}</span>
                  {logo && <img src={logo} style={{width:'20px', height:'20px', objectFit:'contain', borderRadius:'3px', background:'#fff', padding:'1px', flexShrink:0}} />}
                  <div style={{minWidth:0}}>
                    <div style={{fontWeight:600, color:'var(--text)', fontSize:'14px', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>{s.name}</div>
                    <div style={{fontSize:'12px', color:'var(--text3)', fontFamily:'var(--font-mono)'}}>
                      {s.postcode} · {(s.distance_km * 0.621371).toFixed(1)} mi
                      {s.is_motorway && ' · Motorway'}
                      {s.is_supermarket && ' · Supermarket'}
                      {s.source_updated_at && <> · Updated {timeAgo(s.source_updated_at)}</>}
                    </div>
                  </div>
                </div>
                <div style={{color: FUEL_COLORS[selectedFuel], fontWeight:700, fontSize:'20px', fontFamily:'var(--font-mono)', flexShrink:0}}>
                  {s.price_pence.toFixed(1)}<span style={{fontSize:'12px'}}>p</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* CTA */}
      <div style={{
        padding:'24px', background:'var(--surface)', border:'1px solid var(--border)',
        borderRadius:'12px', textAlign:'center'
      }}>
        <h3 style={{color:'var(--text)', marginBottom:'8px'}}>Find fuel near your exact location</h3>
        <p style={{color:'var(--text2)', fontSize:'13px', marginBottom:'16px'}}>
          Use the Pumpr map to find the cheapest petrol and diesel within any radius.
        </p>
        <button
          onClick={() => navigate('/')}
          style={{background:'var(--amber)', color:'#000', fontWeight:700, padding:'10px 28px', borderRadius:'8px', border:'none', cursor:'pointer', fontSize:'14px'}}
        >Open map →</button>
      </div>
    </div>
  )
}

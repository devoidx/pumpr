import { useEffect, useState } from 'react'
import { useBrandLogos } from '../contexts/BrandsContext'

const FUEL_LABELS = { E10: 'Petrol (E10)', B7: 'Diesel (B7)', E5: 'Premium (E5)', SDV: 'Super Diesel' }
const FUEL_COLORS = { E10: '#2ecc71', B7: '#3498db', E5: '#9b59b6', SDV: '#e67e22' }

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'16px', flex:'1', minWidth:'140px'}}>
      <div style={{fontSize:'11px', color:'var(--text3)', fontFamily:'var(--font-mono)', marginBottom:'6px'}}>{label}</div>
      <div style={{fontSize:'24px', fontWeight:700, color: color || 'var(--amber)', fontFamily:'var(--font-mono)'}}>{value}</div>
      {sub && <div style={{fontSize:'11px', color:'var(--text3)', marginTop:'4px'}}>{sub}</div>}
    </div>
  )
}

function SectionTitle({ children }) {
  return <h2 style={{color:'var(--text)', fontSize:'16px', fontWeight:700, margin:'32px 0 12px', borderBottom:'1px solid var(--border)', paddingBottom:'8px'}}>{children}</h2>
}

export default function IntelligencePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedFuel, setSelectedFuel] = useState('E10')
  const [sectorSearch, setSectorSearch] = useState('')
  const [activeTab, setActiveTab] = useState('overview')
  const brandLogos = useBrandLogos()

  useEffect(() => {
    if (typeof umami !== 'undefined') umami.track('intelligence-viewed')
    fetch('/api/v1/intelligence/latest')
      .then(r => r.ok ? r.json() : null)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div style={{padding:'40px', color:'var(--text2)'}}>Loading market intelligence...</div>
  if (!data) return <div style={{padding:'40px', color:'var(--text2)'}}>No intelligence data available yet. Check back tomorrow.</div>

  const { national, regional, brands, postcode_sectors, narrative } = data
  const nat = national[selectedFuel] || {}
  const natE10 = national['E10'] || {}
  const natB7 = national['B7'] || {}

  const filteredSectors = postcode_sectors
    .filter(s => !sectorSearch || s.sector?.toLowerCase().includes(sectorSearch.toLowerCase()))
    .slice(0, 50)

  return (
    <div style={{maxWidth:'900px', margin:'0 auto', padding:'24px 16px'}}>
      <div style={{marginBottom:'24px'}}>
        <p style={{color:'var(--text3)', fontSize:'12px', fontFamily:'var(--font-mono)', marginBottom:'4px'}}>
          ⛽ Pumpr Intelligence · Updated daily · {new Date(data.date).toLocaleDateString('en-GB', {day:'numeric', month:'long', year:'numeric'})}
        </p>
        <h1 style={{color:'var(--text)', fontSize:'28px', fontWeight:700, marginBottom:'8px'}}>UK Fuel Market Intelligence</h1>
        <p style={{color:'var(--text2)', fontSize:'14px', lineHeight:1.7}}>
          Daily analysis of UK fuel prices across {natE10.stations?.toLocaleString()} stations.
        </p>
      </div>

      {/* Narrative */}
      {narrative && (
        <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'20px', marginBottom:'24px'}}>
          <div style={{fontSize:'11px', color:'var(--amber)', fontFamily:'var(--font-mono)', marginBottom:'12px', fontWeight:700}}>DAILY BRIEFING</div>
          {narrative.split('\n\n').filter(p => p.trim() && !p.startsWith('#')).map((para, i) => (
            <p key={i} style={{color:'var(--text2)', fontSize:'14px', lineHeight:1.8, marginBottom:'12px'}}>{para}</p>
          ))}
        </div>
      )}

      {/* Fuel selector */}
      <div style={{display:'flex', gap:'8px', marginBottom:'20px', flexWrap:'wrap'}}>
        {Object.keys(FUEL_LABELS).filter(f => national[f]).map(f => (
          <button key={f} onClick={() => setSelectedFuel(f)} style={{
            padding:'6px 14px', borderRadius:'8px', border:'1px solid',
            borderColor: selectedFuel === f ? FUEL_COLORS[f] : 'var(--border2)',
            background: selectedFuel === f ? FUEL_COLORS[f] + '22' : 'var(--surface)',
            color: selectedFuel === f ? FUEL_COLORS[f] : 'var(--text2)',
            fontWeight: selectedFuel === f ? 700 : 400,
            cursor:'pointer', fontSize:'13px',
          }}>{FUEL_LABELS[f]}</button>
        ))}
      </div>

      {/* Tab nav */}
      <div style={{display:'flex', gap:'4px', marginBottom:'24px', borderBottom:'1px solid var(--border)', flexWrap:'wrap'}}>
        {[
          {id:'overview', label:'Overview'},
          {id:'regions', label:'Regions'},
          {id:'brands', label:'Brands'},
          {id:'postcodes', label:'Postcodes'},
          {id:'supermarkets', label:'Supermarkets'},
          {id:'trends', label:'Trends', disabled:true},
          {id:'motorway', label:'Motorway', disabled:true},
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && setActiveTab(tab.id)}
            style={{
              padding:'8px 16px', background:'none', border:'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--amber)' : '2px solid transparent',
              color: tab.disabled ? 'var(--text3)' : activeTab === tab.id ? 'var(--amber)' : 'var(--text2)',
              fontWeight: activeTab === tab.id ? 700 : 400,
              cursor: tab.disabled ? 'not-allowed' : 'pointer',
              fontSize:'14px', marginBottom:'-1px',
              opacity: tab.disabled ? 0.4 : 1,
            }}
            title={tab.disabled ? 'Coming soon' : ''}
          >{tab.label}</button>
        ))}
      </div>

      {/* Overview tab */}
      {activeTab === 'overview' && <>
      <SectionTitle>National Overview — {FUEL_LABELS[selectedFuel]}</SectionTitle>
      <div style={{display:'flex', gap:'12px', flexWrap:'wrap', marginBottom:'16px'}}>
        <StatCard label="Average price" value={`${nat.avg?.toFixed(2)}p`} sub={`${nat.stations?.toLocaleString()} stations`} />
        <StatCard label="Median price" value={`${nat.median?.toFixed(2)}p`} />
        <StatCard label="Lowest price" value={`${nat.min?.toFixed(2)}p`} color="#2ecc71" />
        <StatCard label="Highest price" value={`${nat.max?.toFixed(2)}p`} color="#e74c3c" />
      </div>
      {nat.supermarket_avg > 0 && (
        <div style={{display:'flex', gap:'12px', flexWrap:'wrap', marginBottom:'8px'}}>
          <StatCard label="Supermarket avg" value={`${nat.supermarket_avg?.toFixed(2)}p`} sub={`${nat.supermarket_discount?.toFixed(2)}p cheaper than branded`} color="#2ecc71" />
          <StatCard label="Branded avg" value={`${nat.branded_avg?.toFixed(2)}p`} />
          <StatCard label="Motorway avg" value={`${nat.motorway_avg?.toFixed(2)}p`} sub={`+${nat.motorway_premium?.toFixed(2)}p vs national`} color="#e74c3c" />
          {selectedFuel === 'E10' && <StatCard label="Diesel premium" value={`+${(natB7.avg - natE10.avg).toFixed(1)}p`} sub="B7 vs E10 national avg" color="#3498db" />}
        </div>
      )}

      </>
      }

      {/* Regions tab */}
      {activeTab === 'regions' && <>
      <SectionTitle>Regional Breakdown — E10 (Petrol)</SectionTitle>
      <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', overflow:'hidden'}}>
        <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
          <thead>
            <tr style={{background:'var(--surface2)', borderBottom:'1px solid var(--border)'}}>
              <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Region</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>E10 avg</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>B7 avg</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>Stations</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>vs UK avg</th>
            </tr>
          </thead>
          <tbody>
            {regional.map((r, i) => {
              const vsNat = r.E10 ? (r.E10 - natE10.avg).toFixed(1) : null
              return (
                <tr key={r.region} style={{borderBottom:'1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--surface2)'}}>
                  <td style={{padding:'10px 16px', color:'var(--text)', fontWeight: i === 0 ? 700 : 400}}>
                    {i === 0 ? '🏆 ' : ''}{r.region}
                  </td>
                  <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color: i === 0 ? '#2ecc71' : i === regional.length-1 ? '#e74c3c' : 'var(--text)'}}>{r.E10 ? `${r.E10.toFixed(2)}p` : '—'}</td>
                  <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--text2)'}}>{r.B7 ? `${r.B7.toFixed(2)}p` : '—'}</td>
                  <td style={{padding:'10px 16px', textAlign:'right', color:'var(--text3)', fontFamily:'var(--font-mono)'}}>{r.E10_stations?.toLocaleString() || '—'}</td>
                  <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color: vsNat < 0 ? '#2ecc71' : vsNat > 0 ? '#e74c3c' : 'var(--text3)'}}>
                    {vsNat ? (vsNat > 0 ? '+' : '') + vsNat + 'p' : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      </>
      }

      {/* Brands tab */}
      {activeTab === 'brands' && <>
      <SectionTitle>Brand League Table</SectionTitle>
      <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', overflow:'hidden'}}>
        <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
          <thead>
            <tr style={{background:'var(--surface2)', borderBottom:'1px solid var(--border)'}}>
              <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>#</th>
              <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Brand</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>E10 avg</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>B7 avg</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>Stations</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>vs UK avg</th>
            </tr>
          </thead>
          <tbody>
            {brands.filter(b => b.E10).map((b, i) => {
              const logo = brandLogos[b.brand?.toUpperCase()]
              const vsNat = b.E10_vs_national
              return (
                <tr key={b.brand} style={{borderBottom:'1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--surface2)'}}>
                  <td style={{padding:'10px 16px', color:'var(--text3)', fontFamily:'var(--font-mono)', fontSize:'11px'}}>{i+1}</td>
                  <td style={{padding:'10px 16px'}}>
                    <div style={{display:'flex', alignItems:'center', gap:'8px'}}>
                      {logo && <img src={logo} style={{width:'16px', height:'16px', objectFit:'contain', borderRadius:'2px', background:'#fff', padding:'1px'}} />}
                      <span style={{color:'var(--text)', fontWeight: i < 3 ? 700 : 400}}>{b.brand}</span>
                    </div>
                  </td>
                  <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color: i === 0 ? '#2ecc71' : 'var(--text)'}}>{b.E10?.toFixed(2)}p</td>
                  <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--text2)'}}>{b.B7 ? `${b.B7.toFixed(2)}p` : '—'}</td>
                  <td style={{padding:'10px 16px', textAlign:'right', color:'var(--text3)', fontFamily:'var(--font-mono)'}}>{b.E10_stations}</td>
                  <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color: vsNat < 0 ? '#2ecc71' : vsNat > 0 ? '#e74c3c' : 'var(--text3)'}}>
                    {vsNat ? (vsNat > 0 ? '+' : '') + vsNat + 'p' : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      </>
      }

      {/* Postcodes tab */}
      {activeTab === 'postcodes' && <>
      <SectionTitle>Postcode Sector Analysis</SectionTitle>
      <div style={{marginBottom:'12px'}}>
        <input
          type="text"
          placeholder="Search postcode (e.g. SW1, M1, LS1)..."
          value={sectorSearch}
          onChange={e => setSectorSearch(e.target.value)}
          style={{width:'100%', maxWidth:'300px', background:'var(--surface2)', border:'1px solid var(--border2)',
            color:'var(--text)', padding:'8px 12px', borderRadius:'8px', fontSize:'13px', boxSizing:'border-box'}}
        />
      </div>
      <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', overflow:'hidden'}}>
        <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
          <thead>
            <tr style={{background:'var(--surface2)', borderBottom:'1px solid var(--border)'}}>
              <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Sector</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>E10 avg</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>Range</th>
              <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>Stations</th>
              <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Market</th>
              <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Price leader</th>
            </tr>
          </thead>
          <tbody>
            {filteredSectors.map((s, i) => (
              <tr key={s.sector} style={{borderBottom:'1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--surface2)'}}>
                <td style={{padding:'10px 16px', color:'var(--text)', fontWeight:700, fontFamily:'var(--font-mono)'}}>{s.sector}</td>
                <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--amber)'}}>{s.avg_e10?.toFixed(2)}p</td>
                <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--text3)'}}>{s.price_range}p</td>
                <td style={{padding:'10px 16px', textAlign:'right', color:'var(--text3)', fontFamily:'var(--font-mono)'}}>{s.stations}</td>
                <td style={{padding:'10px 16px'}}>
                  <span
                    title={s.market_type === 'Competitive' ? 'Large price spread (≥10p) — stations are competing on price' : 'Small price spread (<10p) — limited price competition in this area'}
                    style={{fontSize:'11px', padding:'2px 8px', borderRadius:'4px', cursor:'help',
                    background: s.market_type === 'Competitive' ? '#2ecc7122' : '#e74c3c22',
                    color: s.market_type === 'Competitive' ? '#2ecc71' : '#e74c3c'}}>
                    {s.market_type}
                  </span>
                </td>
                <td style={{padding:'10px 16px', color:'var(--text2)', fontSize:'12px'}}>{s.price_leader || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!sectorSearch && postcode_sectors.length > 50 && (
          <div style={{padding:'12px 16px', color:'var(--text3)', fontSize:'12px', fontFamily:'var(--font-mono)', borderTop:'1px solid var(--border)'}}>
            Showing 50 of {postcode_sectors.length} sectors. Use search to filter.
          </div>
        )}
      </div>

      </>
      }

      {/* Supermarkets tab */}
      {activeTab === 'supermarkets' && <>
        <SectionTitle>Supermarket vs Branded Pricing</SectionTitle>
        <div style={{display:'flex', gap:'12px', flexWrap:'wrap', marginBottom:'24px'}}>
          <StatCard label="Supermarket E10 avg" value={`${natE10.supermarket_avg?.toFixed(2)}p`} sub={`${natE10.supermarket_discount?.toFixed(2)}p cheaper than branded`} color="#2ecc71" />
          <StatCard label="Branded E10 avg" value={`${natE10.branded_avg?.toFixed(2)}p`} />
          <StatCard label="Supermarket B7 avg" value={`${natB7.supermarket_avg?.toFixed(2)}p`} sub={`${natB7.supermarket_discount?.toFixed(2)}p cheaper than branded`} color="#2ecc71" />
          <StatCard label="Branded B7 avg" value={`${natB7.branded_avg?.toFixed(2)}p`} />
        </div>

        <SectionTitle>Supermarket Brand Comparison</SectionTitle>
        <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', overflow:'hidden', marginBottom:'24px'}}>
          <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
            <thead>
              <tr style={{background:'var(--surface2)', borderBottom:'1px solid var(--border)'}}>
                <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Supermarket</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>E10 avg</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>B7 avg</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>Stations</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>vs UK avg</th>
              </tr>
            </thead>
            <tbody>
              {brands.filter(b => ['TESCO','ASDA','MORRISONS',"SAINSBURY'S",'COSTCO WHOLESALE'].includes(b.brand)).sort((a,b) => (a.E10||999)-(b.E10||999)).map((b, i) => {
                const logo = brandLogos[b.brand?.toUpperCase()]
                return (
                  <tr key={b.brand} style={{borderBottom:'1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--surface2)'}}>
                    <td style={{padding:'10px 16px'}}>
                      <div style={{display:'flex', alignItems:'center', gap:'8px'}}>
                        {logo && <img src={logo} style={{width:'16px', height:'16px', objectFit:'contain', borderRadius:'2px', background:'#fff', padding:'1px'}} />}
                        <span style={{color:'var(--text)', fontWeight:600}}>{b.brand}</span>
                      </div>
                    </td>
                    <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'#2ecc71'}}>{b.E10?.toFixed(2)}p</td>
                    <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--text2)'}}>{b.B7 ? `${b.B7.toFixed(2)}p` : '—'}</td>
                    <td style={{padding:'10px 16px', textAlign:'right', color:'var(--text3)', fontFamily:'var(--font-mono)'}}>{b.E10_stations}</td>
                    <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color: b.E10_vs_national < 0 ? '#2ecc71' : '#e74c3c'}}>
                      {b.E10_vs_national ? (b.E10_vs_national > 0 ? '+' : '') + b.E10_vs_national.toFixed(2) + 'p' : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <SectionTitle>Non-Supermarket Brand Comparison</SectionTitle>
        <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', overflow:'hidden'}}>
          <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
            <thead>
              <tr style={{background:'var(--surface2)', borderBottom:'1px solid var(--border)'}}>
                <th style={{padding:'10px 16px', textAlign:'left', color:'var(--text2)', fontWeight:600}}>Brand</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>E10 avg</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>B7 avg</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>Stations</th>
                <th style={{padding:'10px 16px', textAlign:'right', color:'var(--text2)', fontWeight:600}}>vs UK avg</th>
              </tr>
            </thead>
            <tbody>
              {brands.filter(b => !['TESCO','ASDA','MORRISONS',"SAINSBURY'S",'COSTCO WHOLESALE'].includes(b.brand) && b.E10).sort((a,b) => (a.E10||999)-(b.E10||999)).map((b, i) => {
                const logo = brandLogos[b.brand?.toUpperCase()]
                return (
                  <tr key={b.brand} style={{borderBottom:'1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--surface2)'}}>
                    <td style={{padding:'10px 16px'}}>
                      <div style={{display:'flex', alignItems:'center', gap:'8px'}}>
                        {logo && <img src={logo} style={{width:'16px', height:'16px', objectFit:'contain', borderRadius:'2px', background:'#fff', padding:'1px'}} />}
                        <span style={{color:'var(--text)'}}>{b.brand}</span>
                      </div>
                    </td>
                    <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--text)'}}>{b.E10?.toFixed(2)}p</td>
                    <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color:'var(--text2)'}}>{b.B7 ? `${b.B7.toFixed(2)}p` : '—'}</td>
                    <td style={{padding:'10px 16px', textAlign:'right', color:'var(--text3)', fontFamily:'var(--font-mono)'}}>{b.E10_stations}</td>
                    <td style={{padding:'10px 16px', textAlign:'right', fontFamily:'var(--font-mono)', color: b.E10_vs_national < 0 ? '#2ecc71' : '#e74c3c'}}>
                      {b.E10_vs_national ? (b.E10_vs_national > 0 ? '+' : '') + b.E10_vs_national.toFixed(2) + 'p' : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </>}

      <div style={{marginTop:'32px', padding:'16px', background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', fontSize:'12px', color:'var(--text3)', lineHeight:1.7}}>
        <strong style={{color:'var(--text2)'}}>Methodology:</strong> Data sourced from the UK Government Fuel Finder scheme, updated every 30 minutes from {natE10.stations?.toLocaleString()} UK forecourts. 
        Prices outside 50–350p/litre are excluded as outliers. Regional averages are weighted by station count. 
        Market intelligence is recomputed daily at 4:30am GMT. Last updated: {new Date(data.computed_at).toLocaleString('en-GB')}.
      </div>
    </div>
  )
}

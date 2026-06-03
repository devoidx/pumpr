import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function TrendsCharts({ trendsData }) {
  return <>
    <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'20px', marginBottom:'24px'}}>
      <div style={{fontSize:'13px', color:'var(--text2)', marginBottom:'16px', fontWeight:600}}>Petrol (E10) — pence per litre</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={trendsData} margin={{top:4, right:16, left:0, bottom:4}}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="date" tick={{fontSize:11, fill:'var(--text3)'}} tickFormatter={d => d.slice(5)} />
          <YAxis tick={{fontSize:11, fill:'var(--text3)'}} domain={['auto','auto']} tickFormatter={v => `${v}p`} width={44} />
          <Tooltip formatter={(v, n) => [`${v.toFixed(1)}p`, n]} labelFormatter={l => `Date: ${l}`} contentStyle={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'8px', fontSize:'12px'}} />
          <Legend wrapperStyle={{fontSize:'12px', color:'var(--text2)'}} />
          <Line type="monotone" dataKey="e10_avg" name="National avg" stroke="#2ecc71" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="e10_supermarket_avg" name="Supermarket avg" stroke="#f5a623" strokeWidth={2} dot={false} strokeDasharray="4 2" />
          <Line type="monotone" dataKey="e10_motorway_avg" name="Motorway avg" stroke="#e74c3c" strokeWidth={2} dot={false} strokeDasharray="4 2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
    <div style={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'10px', padding:'20px', marginBottom:'24px'}}>
      <div style={{fontSize:'13px', color:'var(--text2)', marginBottom:'16px', fontWeight:600}}>Diesel (B7) — pence per litre</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={trendsData} margin={{top:4, right:16, left:0, bottom:4}}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="date" tick={{fontSize:11, fill:'var(--text3)'}} tickFormatter={d => d.slice(5)} />
          <YAxis tick={{fontSize:11, fill:'var(--text3)'}} domain={['auto','auto']} tickFormatter={v => `${v}p`} width={44} />
          <Tooltip formatter={(v, n) => [`${v.toFixed(1)}p`, n]} labelFormatter={l => `Date: ${l}`} contentStyle={{background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'8px', fontSize:'12px'}} />
          <Legend wrapperStyle={{fontSize:'12px', color:'var(--text2)'}} />
          <Line type="monotone" dataKey="b7_avg" name="National avg" stroke="#3498db" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="b7_supermarket_avg" name="Supermarket avg" stroke="#f5a623" strokeWidth={2} dot={false} strokeDasharray="4 2" />
          <Line type="monotone" dataKey="b7_motorway_avg" name="Motorway avg" stroke="#e74c3c" strokeWidth={2} dot={false} strokeDasharray="4 2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </>
}

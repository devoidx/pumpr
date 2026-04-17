export default function PumpIcon({ size = 24, color = '#f5a623' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'block', flexShrink: 0, marginTop: '1px' }}>
      <rect x="3" y="4" width="10" height="14" rx="1.5" stroke={color} strokeWidth="1.5"/>
      <rect x="5" y="6" width="6" height="4" rx="1" fill={color} opacity="0.8"/>
      <line x1="13" y1="6" x2="17" y2="6" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="17" y1="6" x2="17" y2="10" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <rect x="15.5" y="10" width="3" height="4" rx="1" fill={color}/>
      <rect x="2" y="17" width="12" height="1.5" rx="0.75" fill={color} opacity="0.6"/>
    </svg>
  )
}

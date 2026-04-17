export default function PumpIcon({ size = 24, color = '#f5a623' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'block', flexShrink: 0 }}>
      <rect x="3" y="9" width="10" height="13" rx="1.5" stroke={color} strokeWidth="1.5"/>
      <rect x="5" y="11" width="6" height="4" rx="1" fill={color} opacity="0.8"/>
      <line x1="13" y1="11" x2="17" y2="11" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="17" y1="11" x2="17" y2="14" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <rect x="15.5" y="14" width="3" height="4" rx="1" fill={color}/>
      <rect x="2" y="20.5" width="12" height="1.5" rx="0.75" fill={color} opacity="0.6"/>
    </svg>
  )
}

import { useEffect, useState } from 'react'

export default function FeedHealthIndicator() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    function fetch_health() {
      fetch('/api/v1/prices/feed-health')
        .then(r => r.json())
        .then(setHealth)
        .catch(() => setHealth({ status: 'red', message: 'Could not reach server' }))
    }
    fetch_health()
    const interval = setInterval(fetch_health, 5 * 60 * 1000) // refresh every 5 mins
    return () => clearInterval(interval)
  }, [])

  if (!health) return null

  const color = health.status === 'green' ? '#2ecc71' : health.status === 'amber' ? '#f5a623' : '#e74c3c'

  return (
    <div
      title={health.message}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 24,
        height: 24,
        flexShrink: 0,
        cursor: 'default',
      }}
    >
      <div style={{
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 6px ${color}`,
      }} />
    </div>
  )
}

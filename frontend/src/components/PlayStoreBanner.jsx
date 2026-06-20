import { useState } from 'react'
import { Capacitor } from '@capacitor/core'

export default function PlayStoreBanner() {
  const [dismissed, setDismissed] = useState(() => localStorage.getItem('pumpr_playstore_banner_dismissed') === '1')

  if (Capacitor.isNativePlatform()) return null
  if (dismissed) return null

  function handleDismiss() {
    localStorage.setItem('pumpr_playstore_banner_dismissed', '1')
    setDismissed(true)
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      background: 'var(--amber)',
      color: '#000',
      padding: '8px 16px',
      fontSize: '13px',
      flexWrap: 'wrap',
      textAlign: 'center'
    }}>
      <span>📲 Pumpr is now on Google Play!</span>
      <a
      
        href="https://play.google.com/store/apps/details?id=co.uk.pumpr"
        target="_blank"
        rel="noopener noreferrer"
        style={{ display: 'flex', alignItems: 'center' }}
      >
        <img
          src="https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png"
          alt="Get it on Google Play"
          style={{ height: '32px' }}
        />
      </a>
      <button
        onClick={handleDismiss}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: '#000',
          fontSize: '16px',
          lineHeight: 1,
          padding: '0 4px'
        }}
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}

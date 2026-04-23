import { useState } from 'react'
import './ShareButton.css'

function ShareIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
      <polyline points="16 6 12 2 8 6"/>
      <line x1="12" y1="2" x2="12" y2="15"/>
    </svg>
  )
}

export default function ShareButton({ location, fuel, radius }) {
  const [copied, setCopied] = useState(false)

  function handleShare() {
    const url = `${window.location.origin}/?lat=${location.lat}&lng=${location.lng}&fuel=${fuel}&radius=${radius}`
    navigator.clipboard?.writeText(url)
      .then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000) })
      .catch(() => prompt('Copy this link:', url))
  }

  return (
    <div className="share-btn-wrap">
      <button
        className={`location-btn share-btn ${copied ? 'share-btn-done' : ''}`}
        onClick={handleShare}
        title="Share this view"
      >
        {copied ? '✓' : <ShareIcon />}
      </button>
      {copied && <span className="share-tooltip">Link copied!</span>}
    </div>
  )
}

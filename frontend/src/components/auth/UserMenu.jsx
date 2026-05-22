import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import FuelTrackerModal from '../FuelTrackerModal'
import MyPlacesModal from '../MyPlacesModal'
import MyAlertsModal from '../MyAlertsModal'
import MyVehiclesModal from '../MyVehiclesModal'
import ProfileModal from '../ProfileModal'
import LoginModal from './LoginModal'
import RegisterModal from './RegisterModal'
import Portal from '../Portal'
import OnboardingModal from '../OnboardingModal'
import './AuthModal.css'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [showTracker, setShowTracker] = useState(false)
  const [showPlaces, setShowPlaces] = useState(false)
  const [showAlerts, setShowAlerts] = useState(false)
  const [showVehicles, setShowVehicles] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const triggerRef         = useRef(null)
  const dropdownRef        = useRef(null)

  useEffect(() => {
    function handler(e) {
      const inTrigger  = triggerRef.current?.contains(e.target)
      const inDropdown = dropdownRef.current?.contains(e.target)
      if (!inTrigger && !inDropdown) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    if (user && (user.role === 'pro' || user.role === 'admin')) {
      const key = 'pumpr_onboarded_' + user.email
      if (!localStorage.getItem(key)) {
        localStorage.setItem(key, '1')
        setShowOnboarding(true)
      }
    }
  }, [user])

  if (!user) return null
  const initial = (user.username?.[0] ?? user.email[0]).toUpperCase()
  const isPro = user.role === 'pro' || user.role === 'admin' 

  function go(path) {
    setOpen(false)
    // Dispatch navigation event — picked up by App.jsx
    window.dispatchEvent(new CustomEvent('pumpr:navigate', { detail: { path } }))
  }

  return (
    <div className="user-menu" ref={triggerRef}>
      <button className="user-menu-trigger" onClick={() => setOpen(o => !o)}>
        <span className="avatar">{initial}</span>{user.username}
        {isPro && <span style={{fontSize:"9px",fontWeight:700,letterSpacing:"0.06em",background:"var(--amber)",color:"#000",borderRadius:"3px",padding:"1px 4px",marginLeft:"2px"}}>PRO</span>}
      </button>
      {open && (
        <Portal>
          <div
            ref={dropdownRef}
            style={{position:'fixed',top:'52px',right:'8px',zIndex:9999,background:'var(--surface,#1a1a1a)',border:'1px solid var(--border,#2d2d2d)',borderRadius:'8px',boxShadow:'0 8px 32px rgba(0,0,0,0.5)',minWidth:'200px',padding:'0.4rem 0'}}
          >
            <div className="user-menu-info">
              <div className="um-username">{user.username}</div>
              <div className="um-email">{user.email}</div>
              <span className="um-badge">{user.role}</span>
            </div>
            {isPro && <button className="user-menu-item" style={{color:"var(--amber)",borderBottom:"1px solid var(--border)",marginBottom:"4px",paddingBottom:"8px"}} onClick={() => { setOpen(false); setShowOnboarding(true) }}>⚡ Pro features</button>}
            <button className="user-menu-item" onClick={() => { setOpen(false); setShowPlaces(true) }}>📍 My Places</button>
            <button className="user-menu-item" onClick={() => { setOpen(false); setShowVehicles(true) }}>🚗 My Vehicles</button>
            <button className="user-menu-item" onClick={() => { setOpen(false); setShowProfile(true) }}>👤 My Profile</button>
            <button className="user-menu-item" onClick={() => { setOpen(false); setShowAlerts(true) }}>🔔 Price alerts</button>
            <button className="user-menu-item" onClick={() => { setOpen(false); setShowTracker(true) }}>⛽ Fuel tracker</button>
            <button className="user-menu-item danger" onClick={() => { setOpen(false); logout() }}>Sign out</button>
          </div>
        </Portal>
      )}
    {showTracker && <FuelTrackerModal onClose={() => setShowTracker(false)} />}
    {showPlaces && <MyPlacesModal onClose={() => setShowPlaces(false)} onSelectLocation={loc => { setShowPlaces(false); window.dispatchEvent(new CustomEvent('pumpr:go-to-location', {detail: loc})) }} />}
    {showAlerts && <MyAlertsModal onClose={() => setShowAlerts(false)} />}
    {showVehicles && <MyVehiclesModal onClose={() => setShowVehicles(false)} />}
    {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    {showOnboarding && <OnboardingModal onClose={() => setShowOnboarding(false)} openTracker={() => { setShowOnboarding(false); setShowTracker(true) }} openPlaces={() => { setShowOnboarding(false); setShowPlaces(true) }} openAlerts={() => { setShowOnboarding(false); setShowAlerts(true) }} openVehicles={() => { setShowOnboarding(false); setShowVehicles(true) }} />}
    </div>
  )
}

export default function NavAuthSection() {
  const { isAuthenticated, loading } = useAuth()
  const [modal, setModal] = useState(null)

  // Listen for Pro page open event
  useEffect(() => {
    function handler() { setModal('login') }
    window.addEventListener('pumpr:open-login', handler)
    return () => window.removeEventListener('pumpr:open-login', handler)
  }, [])

  if (loading) return null
  if (isAuthenticated) return <UserMenu />

  return (
    <>
      <button className="nav-btn-ghost" onClick={() => setModal('login')}>Sign in</button>
      <button className="nav-btn-filled" onClick={() => { if (typeof umami !== 'undefined') umami.track('go-pro-clicked'); window.dispatchEvent(new CustomEvent('pumpr:navigate', { detail: { path: '/pro' } })) }}>Go Pro</button>
      {modal === 'login'    && <Portal><LoginModal    onClose={() => setModal(null)} onSwitchToRegister={() => setModal('register')} /></Portal>}
    </>
  )
}

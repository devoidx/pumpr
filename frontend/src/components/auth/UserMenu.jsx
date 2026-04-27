import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import LoginModal from './LoginModal'
import RegisterModal from './RegisterModal'
import Portal from '../Portal'
import './AuthModal.css'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen]    = useState(false)
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

  if (!user) return null
  const initial = (user.username?.[0] ?? user.email[0]).toUpperCase()

  function go(path) {
    setOpen(false)
    // Dispatch navigation event — picked up by App.jsx
    window.dispatchEvent(new CustomEvent('pumpr:navigate', { detail: { path } }))
  }

  return (
    <div className="user-menu" ref={triggerRef}>
      <button className="user-menu-trigger" onClick={() => setOpen(o => !o)}>
        <span className="avatar">{initial}</span>{user.username}
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
            <button className="user-menu-item" onClick={() => go('/my-places')}>📍 My Places</button>
            <button className="user-menu-item" onClick={() => go('/profile')}>👤 My Profile</button>
            <button className="user-menu-item" onClick={() => setOpen(false)} style={{opacity:0.5,cursor:'default'}} title='Coming soon'>🔔 Price alerts</button>
            <button className="user-menu-item danger" onClick={() => { setOpen(false); logout() }}>Sign out</button>
          </div>
        </Portal>
      )}
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
      <button className="nav-btn-filled" onClick={() => window.dispatchEvent(new CustomEvent('pumpr:navigate', { detail: { path: '/pro' } }))}>Go Pro</button>
      {modal === 'login'    && <Portal><LoginModal    onClose={() => setModal(null)} onSwitchToRegister={() => setModal('register')} /></Portal>}
      {modal === 'register' && <Portal><RegisterModal onClose={() => setModal(null)} onSwitchToLogin={() => setModal('login')} /></Portal>}
    </>
  )
}

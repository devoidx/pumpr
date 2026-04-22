import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import LoginModal from './LoginModal'
import RegisterModal from './RegisterModal'
import './AuthModal.css'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen]  = useState(false)
  const ref              = useRef(null)

  useEffect(() => {
    function handler(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (!user) return null
  const initial = (user.username?.[0] ?? user.email[0]).toUpperCase()

  return (
    <div className="user-menu" ref={ref}>
      <button className="user-menu-trigger" onClick={() => setOpen(o => !o)}>
        <span className="avatar">{initial}</span>{user.username}
      </button>
      {open && (
        <div className="user-menu-dropdown">
          <div className="user-menu-info">
            <div className="um-username">{user.username}</div>
            <div className="um-email">{user.email}</div>
            <span className="um-badge">{user.role}</span>
          </div>
          <button className="user-menu-item" onClick={() => setOpen(false)}>★ Favourite stations</button>
          <button className="user-menu-item" onClick={() => setOpen(false)}>🔔 Price alerts</button>
          <button className="user-menu-item danger" onClick={() => { setOpen(false); logout() }}>Sign out</button>
        </div>
      )}
    </div>
  )
}

export default function NavAuthSection() {
  const { isAuthenticated, loading } = useAuth()
  const [modal, setModal] = useState(null)
  const navigate = useNavigate()

  if (loading) return <div style={{ width: 120 }} />
  if (isAuthenticated) return <UserMenu />

  return (
    <>
      <div className="nav-auth-buttons">
        <button className="nav-btn-ghost"  onClick={() => setModal('login')}>Sign in</button>
        <button className="nav-btn-filled" onClick={() => navigate('/pro')}>Go Pro</button>
      </div>
      {modal === 'login'    && <LoginModal    onClose={() => setModal(null)} onSwitchToRegister={() => setModal('register')} />}
      {modal === 'register' && <RegisterModal onClose={() => setModal(null)} onSwitchToLogin={() => setModal('login')} />}
    </>
  )
}

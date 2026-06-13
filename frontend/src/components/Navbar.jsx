import { useState } from 'react'
import { useTheme } from '../hooks/useTheme'
import { Link, useLocation } from 'react-router-dom'
import PumpIcon from './icons/PumpIcon'
import NavAuthSection from './auth/UserMenu'
import FeedHealthIndicator from './FeedHealthIndicator'
import './Navbar.css'

export default function Navbar() {
  const loc = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const { theme, toggleTheme } = useTheme()

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand" onClick={() => setMenuOpen(false)}>
        <PumpIcon size={26} />
        <span className="navbar-name">Pumpr</span><FeedHealthIndicator />
      </Link>

      {/* Desktop links */}
      <div className="navbar-links">
        <Link to="/"      className={`navbar-link ${loc.pathname === '/'      ? 'active' : ''}`}>Map</Link>
        <Link to="/stats" className={`navbar-link ${loc.pathname === '/stats' ? 'active' : ''}`}>Stats</Link>
        <Link to="/intelligence" className={`navbar-link ${loc.pathname === '/intelligence' ? 'active' : ''}`}>Intelligence</Link>
        <Link to="/blog" className={`navbar-link ${loc.pathname.startsWith('/blog') ? 'active' : ''}`}>Insights</Link>
        <Link to="/about" className={`navbar-link ${loc.pathname === '/about' ? 'active' : ''}`}>About</Link>
      </div>

      <button
        onClick={toggleTheme}
        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        style={{background:'none',border:'none',cursor:'pointer',color:'var(--text2)',padding:'6px',display:'flex',alignItems:'center',justifyContent:'center',borderRadius:'6px',transition:'var(--transition)'}}
        onMouseEnter={e => e.currentTarget.style.color='var(--text)'}
        onMouseLeave={e => e.currentTarget.style.color='var(--text2)'}
      >
        {theme === 'dark'
          ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        }
      </button>
      {/* Desktop auth — hidden on mobile */}
      <div className="navbar-auth-desktop">
        <NavAuthSection />
      </div>

      {/* Mobile hamburger */}
      <button
        className={`navbar-burger ${menuOpen ? 'open' : ''}`}
        onClick={() => setMenuOpen(o => !o)}
        aria-label="Menu"
      >
        <span /><span /><span />
      </button>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="navbar-mobile-menu" onClick={() => setMenuOpen(false)}>
          <Link to="/"      className={`navbar-mobile-link ${loc.pathname === '/'      ? 'active' : ''}`}>Map</Link>
          <Link to="/stats" className={`navbar-mobile-link ${loc.pathname === '/stats' ? 'active' : ''}`}>Stats</Link>
          <Link to="/intelligence" className={`navbar-mobile-link ${loc.pathname === '/intelligence' ? 'active' : ''}`}>Intelligence</Link>
          <Link to="/blog" className={`navbar-mobile-link ${loc.pathname.startsWith('/blog') ? 'active' : ''}`}>Insights</Link>
          <Link to="/about" className={`navbar-mobile-link ${loc.pathname === '/about' ? 'active' : ''}`}>About</Link>
          <button
            onClick={toggleTheme}
            style={{background:'none',border:'none',cursor:'pointer',color:'var(--text2)',padding:'12px 16px',display:'flex',alignItems:'center',gap:'10px',fontSize:'15px',width:'100%'}}
          >
            {theme === 'dark'
              ? <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>Light mode</>
              : <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>Dark mode</>
            }
          </button>
          <div className="navbar-mobile-auth" onClick={e => e.stopPropagation()}>
            <NavAuthSection />
          </div>
        </div>
      )}
    </nav>
  )
}

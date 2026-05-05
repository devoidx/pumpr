import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import PumpIcon from './icons/PumpIcon'
import NavAuthSection from './auth/UserMenu'
import FeedHealthIndicator from './FeedHealthIndicator'
import './Navbar.css'

export default function Navbar() {
  const loc = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

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
        <Link to="/blog" className={`navbar-link ${loc.pathname.startsWith('/blog') ? 'active' : ''}`}>Insights</Link>
        <Link to="/about" className={`navbar-link ${loc.pathname === '/about' ? 'active' : ''}`}>About</Link>
      </div>

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
          <Link to="/blog" className={`navbar-mobile-link ${loc.pathname.startsWith('/blog') ? 'active' : ''}`}>Insights</Link>
          <Link to="/about" className={`navbar-mobile-link ${loc.pathname === '/about' ? 'active' : ''}`}>About</Link>
          <div className="navbar-mobile-auth" onClick={e => e.stopPropagation()}>
            <NavAuthSection />
          </div>
        </div>
      )}
    </nav>
  )
}

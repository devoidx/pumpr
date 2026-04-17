import { Link, useLocation } from 'react-router-dom'
import PumpIcon from './icons/PumpIcon'
import './Navbar.css'

export default function Navbar() {
  const loc = useLocation()

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <PumpIcon size={20} />
        <span className="navbar-name">Pumpr</span>
      </Link>
      <div className="navbar-links">
        <Link to="/" className={`navbar-link ${loc.pathname === '/' ? 'active' : ''}`}>Map</Link>
        <Link to="/stats" className={`navbar-link ${loc.pathname === '/stats' ? 'active' : ''}`}>UK Stats</Link>
        <Link to="/about" className={`navbar-link ${loc.pathname === '/about' ? 'active' : ''}`}>About</Link>
      </div>
      <div className="navbar-tag">Live UK fuel prices</div>
    </nav>
  )
}

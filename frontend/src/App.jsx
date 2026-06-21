import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Route, Routes, useNavigate } from 'react-router-dom'
import BlogPage from './pages/BlogPage'
import BlogPostPage from './pages/BlogPostPage'
import Navbar from './components/Navbar'
import Feedback from './pages/Feedback'
import PlayStoreBanner from './components/PlayStoreBanner'
import StationDetail from './pages/StationDetail'
import EvDetail from './pages/EvDetail'
import Home from './pages/Home'
import Stats from './pages/Stats'
import About from './pages/About'
import Privacy from './pages/Privacy'
import VerifyEmailPage from './components/auth/VerifyEmailPage'
import ResetPasswordPage from './components/auth/ResetPasswordPage'
import ProPage from './pages/ProPage'
import SetupPasswordPage from './pages/SetupPasswordPage'
import MyVehiclesPage from './pages/MyVehiclesPage'
import UnverifiedBanner from './components/auth/UnverifiedBanner'
import ProfilePage from './pages/ProfilePage'
import MyPlacesPage from './pages/MyPlacesPage'
import MyAlertsPage from './pages/MyAlertsPage'
import DisableAlertPage from './pages/DisableAlertPage'
import CheapFuelPage from './pages/CheapFuelPage'
import IntelligencePage from './pages/IntelligencePage'
import ProSuccessPage from './pages/ProSuccessPage'

export default function App() {
  const navigate = useNavigate()
  const currentPath = useLocation().pathname

  useEffect(() => {
    function handler(e) { navigate(e.detail.path) }
    window.addEventListener('pumpr:navigate', handler)
    return () => window.removeEventListener('pumpr:navigate', handler)
  }, [navigate])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <PlayStoreBanner />
      <UnverifiedBanner />
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/stations/:id" element={<StationDetail />} />
          <Route path="/ev/:id" element={<EvDetail />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/about" element={<About />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/pro" element={<ProPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/my-places" element={<MyPlacesPage />} />
          <Route path="/pro/success" element={<ProSuccessPage />} />
          <Route path="/setup-password" element={<SetupPasswordPage />} />
          <Route path="/my-vehicles" element={<MyVehiclesPage />} />
          <Route path="/my-alerts" element={<MyAlertsPage />} />
          <Route path="/alerts/disable" element={<DisableAlertPage />} />
          <Route path="/cheap-fuel/:location" element={<CheapFuelPage />} />
          <Route path="/intelligence" element={<IntelligencePage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/blog/:slug" element={<BlogPostPage />} />
        </Routes>
      </div>
      {currentPath !== '/' && <footer style={{
          borderTop:'1px solid var(--border)', padding:'16px 24px',
          background:'var(--surface)', fontSize:'11px', color:'var(--text3)',
          fontFamily:'var(--font-mono)', flexShrink:0
        }}>
          <div style={{maxWidth:'900px', margin:'0 auto'}}>
            <div style={{display:'flex', alignItems:'center', gap:'8px', marginBottom:'6px', cursor:'pointer'}} onClick={() => {const el = document.getElementById('footer-cities'); el.style.display = el.style.display === 'none' ? 'flex' : 'none'}}>
              <span style={{fontWeight:600, color:'var(--text2)', fontSize:'11px'}}>Cheap fuel by city</span>
              <span style={{color:'var(--text3)', fontSize:'10px'}}>▾</span>
            </div>
            <div id="footer-cities" style={{display:'none', flexWrap:'wrap', gap:'8px', marginBottom:'8px'}}>
              {['london','manchester','birmingham','leeds','glasgow','liverpool','edinburgh','bristol','sheffield','newcastle','nottingham','cardiff','leicester','coventry','plymouth','exeter','cambridge','oxford'].map(city => (
                <a key={city} href={'/cheap-fuel/' + city}
                  style={{color:'var(--text3)', textDecoration:'none', padding:'2px 6px',
                    border:'1px solid var(--border)', borderRadius:'4px'}}
                  onMouseEnter={e => e.currentTarget.style.color='var(--amber)'}
                  onMouseLeave={e => e.currentTarget.style.color='var(--text3)'}
                >
                  {city.charAt(0).toUpperCase() + city.slice(1)}
                </a>
              ))}
            </div>
            <div style={{color:'var(--text3)'}}>
              © {new Date().getFullYear()} Pumpr · <a href="/about" style={{color:'var(--text3)'}}>About</a> · <a href="/privacy" style={{color:'var(--text3)'}}>Privacy</a> · <a href="/blog" style={{color:'var(--text3)'}}>Insights</a> · <a href="/feedback" style={{color:'var(--text3)'}}>Feedback</a>
            </div>
          </div>
        </footer>}
    </div>
  )
}

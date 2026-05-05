import { useEffect } from 'react'
import { Route, Routes, useNavigate } from 'react-router-dom'
import BlogPage from './pages/BlogPage'
import BlogPostPage from './pages/BlogPostPage'
import Navbar from './components/Navbar'
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
import ProSuccessPage from './pages/ProSuccessPage'

export default function App() {
  const navigate = useNavigate()

  useEffect(() => {
    function handler(e) { navigate(e.detail.path) }
    window.addEventListener('pumpr:navigate', handler)
    return () => window.removeEventListener('pumpr:navigate', handler)
  }, [navigate])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <UnverifiedBanner />
      <div style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/stations/:id" element={<StationDetail />} />
          <Route path="/ev/:id" element={<EvDetail />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/about" element={<About />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/pro" element={<ProPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/my-places" element={<MyPlacesPage />} />
          <Route path="/pro/success" element={<ProSuccessPage />} />
          <Route path="/setup-password" element={<SetupPasswordPage />} />
          <Route path="/my-vehicles" element={<MyVehiclesPage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/blog/:slug" element={<BlogPostPage />} />
        </Routes>
      </div>
    </div>
  )
}

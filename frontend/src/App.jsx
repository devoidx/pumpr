import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import StationDetail from './pages/StationDetail'
import EvDetail from './pages/EvDetail'
import Home from './pages/Home'
import Stats from './pages/Stats'
import About from './pages/About'
import Privacy from './pages/Privacy'

export default function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/stations/:id" element={<StationDetail />} />
          <Route path="/ev/:id" element={<EvDetail />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/about" element={<About />} />
          <Route path="/privacy" element={<Privacy />} />
        </Routes>
      </div>
    </div>
  )
}

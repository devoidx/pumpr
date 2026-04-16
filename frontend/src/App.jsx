import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import StationDetail from './pages/StationDetail'
import Home from './pages/Home'
import Stats from './pages/Stats'

export default function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/stations/:id" element={<StationDetail />} />
          <Route path="/stats" element={<Stats />} />
        </Routes>
      </div>
    </div>
  )
}

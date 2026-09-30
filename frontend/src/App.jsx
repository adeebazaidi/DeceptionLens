import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import ImageAnalysis from './pages/ImageAnalysis.jsx'
import FingerprintComparison from './pages/FingerprintComparison.jsx'

export default function App() {
  return (
    <div className="app-root">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<ImageAnalysis />} />
        <Route path="/fingerprint" element={<FingerprintComparison />} />
      </Routes>
    </div>
  )
}

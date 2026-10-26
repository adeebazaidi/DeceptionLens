import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import Footer from './components/Footer.jsx'
import ImageAnalysis from './pages/ImageAnalysis.jsx'
import FingerprintComparison from './pages/FingerprintComparison.jsx'
import SignatureAnalysis from './pages/SignatureAnalysis.jsx'

import DocumentAnalysis from './pages/DocumentAnalysis.jsx'
import Cases from './pages/Cases.jsx'

export default function App() {
  return (
    <div className="app-root">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/cases" element={<Cases />} />
        <Route path="/analyze" element={<ImageAnalysis />} />
        <Route path="/fingerprint" element={<FingerprintComparison />} />
        <Route path="/signature" element={<SignatureAnalysis />} />
        <Route path="/document" element={<DocumentAnalysis />} />
      </Routes>
      <Footer />
    </div>
  )
}

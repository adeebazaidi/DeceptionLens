import { Link, useLocation } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <Link to="/" className="navbar-brand" aria-label="DeceptionLens home">
        <div className="navbar-logo-icon" aria-hidden="true"><img src="/logo.png" alt="Logo" style={{ width: '28px', height: '28px', borderRadius: '6px' }} /></div>
        <div>
          <div className="navbar-title">DeceptionLens</div>
          <div className="navbar-subtitle">Forensic Analysis</div>
        </div>
      </Link>

      <div className="navbar-right">
        <div className="navbar-disclaimer" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={16} /> Research &amp; educational use only
        </div>
        <Link
          to="/"
          className={`nav-link${location.pathname === '/' ? ' active' : ''}`}
        >
          Home
        </Link>
        <Link
          to="/analyze"
          className={`nav-link${location.pathname === '/analyze' ? ' active' : ''}`}
        >
          Image Analysis
        </Link>
        <Link
          to="/fingerprint"
          className={`nav-link${location.pathname === '/fingerprint' ? ' active' : ''}`}
        >
          Fingerprint
        </Link>
        <Link
          to="/signature"
          className={`nav-link${location.pathname === '/signature' ? ' active' : ''}`}
        >
          Signature
        </Link>
      </div>
    </nav>
  )
}

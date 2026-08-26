import { Link, useLocation } from 'react-router-dom'
import { Search, AlertTriangle } from 'lucide-react'

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <Link to="/" className="navbar-brand" aria-label="DeceptionLens home">
        <div className="navbar-logo-icon" aria-hidden="true"><Search size={24} /></div>
        <div>
          <div className="navbar-title">DeceptionLens</div>
          <div className="navbar-subtitle">Forensic Image Analysis</div>
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
          Analyze
        </Link>
      </div>
    </nav>
  )
}

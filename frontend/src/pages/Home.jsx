import { Link } from 'react-router-dom'
import { Microscope, Fingerprint, PenTool, Search, ShieldAlert, Lock, FileBadge, Crosshair, Activity } from 'lucide-react'

export default function Home() {
  return (
    <main className="home-page" id="home-page" style={{ position: 'relative', overflow: 'hidden', minHeight: 'calc(100vh - 70px)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '2rem' }}>
      {/* Decorative Background Shapes */}
      {/* Dot Grid Pattern */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundImage: 'radial-gradient(rgba(128,128,128,0.15) 1px, transparent 1px)',
        backgroundSize: '30px 30px',
        zIndex: -2,
        pointerEvents: 'none'
      }} />

      {/* Small Floating Icons */}
      <div style={{ position: 'absolute', top: '15%', right: '15%', opacity: 0.05, transform: 'rotate(15deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <Search size={50} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', top: '10%', left: '20%', opacity: 0.05, transform: 'rotate(-10deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <Fingerprint size={65} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', top: '40%', right: '25%', opacity: 0.04, transform: 'rotate(5deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <ShieldAlert size={60} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', bottom: '20%', left: '15%', opacity: 0.05, transform: 'rotate(25deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <Lock size={45} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', bottom: '15%', right: '15%', opacity: 0.05, transform: 'rotate(-15deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <FileBadge size={55} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', top: '50%', left: '8%', opacity: 0.04, transform: 'rotate(-5deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <Crosshair size={70} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', top: '60%', right: '8%', opacity: 0.04, transform: 'rotate(10deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <Activity size={60} strokeWidth={1.5} />
      </div>
      <div style={{ position: 'absolute', bottom: '35%', left: '25%', opacity: 0.05, transform: 'rotate(30deg)', zIndex: -1, pointerEvents: 'none', color: 'currentColor' }}>
        <PenTool size={50} strokeWidth={1.5} />
      </div>
      <div className="hero-badge">
        <span className="hero-badge-dot" aria-hidden="true" />
        Easy Digital Forensics Suite
      </div>

      <h1 className="hero-title">DeceptionLens</h1>

      <p className="hero-tagline">
        A simple and easy-to-use tool to analyze images, verify fingerprints, and detect signature forgeries.
      </p>

      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', justifyContent: 'center', marginTop: '3rem' }}>
        <Link to="/analyze" id="start-analysis-button" className="hero-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <Microscope size={20} /> Image Analysis
          <span aria-hidden="true">→</span>
        </Link>
        <Link to="/fingerprint" id="start-fingerprint-button" className="hero-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'var(--accent-teal)' }}>
          <Fingerprint size={20} /> Fingerprint
          <span aria-hidden="true">→</span>
        </Link>
        <Link to="/signature" id="start-signature-button" className="hero-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <PenTool size={20} /> Signature Forgery
          <span aria-hidden="true">→</span>
        </Link>
      </div>


    </main>
  )
}

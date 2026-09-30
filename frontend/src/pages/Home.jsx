import { Link } from 'react-router-dom'
import { Activity, Search, Waves, Square, FileCode2, BrainCircuit, Microscope, Fingerprint } from 'lucide-react'

const FEATURES = [
  { icon: <Activity size={18} />, label: 'Entropy Analysis' },
  { icon: <Search size={18} />, label: 'Error Level Analysis' },
  { icon: <Waves size={18} />, label: 'Noise Estimation' },
  { icon: <Fingerprint size={18} />, label: 'Fingerprint Minutiae Matching' },
  { icon: <Square size={18} />, label: 'Texture (GLCM)' },
  { icon: <FileCode2 size={18} />, label: 'Metadata Extraction' },
  { icon: <BrainCircuit size={18} />, label: 'ML Classification (optional)' },
]

export default function Home() {
  return (
    <main className="home-page" id="home-page">
      <div className="hero-badge">
        <span className="hero-badge-dot" aria-hidden="true" />
        Forensic Biometric &amp; Image Screening Suite
      </div>

      <h1 className="hero-title">DeceptionLens</h1>

      <p className="hero-tagline">
        Multi-modal forensic analysis suite: Entropy-driven image forgery detection,
        minutiae-based fingerprint verification, noise estimation, and GLCM texture features.
      </p>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link to="/analyze" id="start-analysis-button" className="hero-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <Microscope size={20} /> Start Image Analysis
          <span aria-hidden="true">→</span>
        </Link>
        <Link to="/fingerprint" id="start-fingerprint-button" className="hero-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'var(--accent-teal)' }}>
          <Fingerprint size={20} /> Fingerprint Comparison
          <span aria-hidden="true">→</span>
        </Link>
      </div>

      <div className="hero-features" role="list" aria-label="Analysis features">
        {FEATURES.map(({ icon, label }) => (
          <div key={label} className="hero-feature-chip" role="listitem">
            <span aria-hidden="true">{icon}</span>
            {label}
          </div>
        ))}
      </div>

      <div className="hero-disclaimer" role="note">
        <strong>Scientific Disclaimer</strong><br />
        DeceptionLens provides preliminary image-forensic analysis for research and educational
        purposes. Entropy variation, ELA, noise, texture, and ML outputs are analytical indicators
        and should not be interpreted as definitive proof that an image has been manipulated.
      </div>
    </main>
  )
}

import { useState } from 'react'

function Lightbox({ src, onClose }) {
  return (
    <div className="lightbox-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <button className="lightbox-close" onClick={onClose} aria-label="Close">✕</button>
      <img src={src} alt="Full-size noise map" className="lightbox-img" onClick={(e) => e.stopPropagation()} />
    </div>
  )
}

export default function NoisePanel({ noise }) {
  const [lightbox, setLightbox] = useState(false)

  if (!noise) return null

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon card-icon-violet" aria-hidden="true">〰️</div>
        <div>
          <div className="card-title">Noise Analysis</div>
          <div className="card-subtitle">Gaussian blur subtraction residuals</div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">Mean Noise</div>
          <div className="stat-value">{noise.mean?.toFixed(3)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Std Dev</div>
          <div className="stat-value teal">{noise.std?.toFixed(3)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Maximum</div>
          <div className="stat-value">{noise.max?.toFixed(1)}</div>
        </div>
      </div>

      {noise.image_url && (
        <div className="img-viewer" style={{ marginTop: '0.75rem' }}>
          <span className="img-viewer-label">Noise Map</span>
          <img
            src={noise.image_url}
            alt="Noise visualization map"
            title="Click to enlarge"
            onClick={() => setLightbox(true)}
          />
        </div>
      )}

      {lightbox && <Lightbox src={noise.image_url} onClose={() => setLightbox(false)} />}
    </div>
  )
}

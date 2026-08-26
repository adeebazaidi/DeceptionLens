import { useState } from 'react'

function Lightbox({ src, onClose }) {
  return (
    <div
      className="lightbox-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image viewer"
    >
      <button className="lightbox-close" onClick={onClose} aria-label="Close image viewer">✕</button>
      <img
        src={src}
        alt="Full-size view"
        className="lightbox-img"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  )
}

export default function ElaPanel({ ela, originalFile }) {
  const [lightbox, setLightbox] = useState(null)

  if (!ela) return null

  const originalUrl = originalFile ? URL.createObjectURL(originalFile) : null

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon card-icon-teal" aria-hidden="true">🔎</div>
        <div>
          <div className="card-title">Error Level Analysis</div>
          <div className="card-subtitle">ELA Anomaly Indicator</div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">ELA Mean</div>
          <div className="stat-value teal">{ela.mean?.toFixed(2)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Std Dev</div>
          <div className="stat-value">{ela.std?.toFixed(2)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Maximum</div>
          <div className="stat-value">{ela.max?.toFixed(1)}</div>
        </div>
      </div>

      <div className="img-comparison">
        {originalUrl && (
          <div className="img-viewer">
            <span className="img-viewer-label">Original</span>
            <img
              src={originalUrl}
              alt="Original uploaded image"
              title="Click to enlarge"
              onClick={() => setLightbox(originalUrl)}
            />
          </div>
        )}
        {ela.image_url && (
          <div className="img-viewer">
            <span className="img-viewer-label">ELA Map</span>
            <img
              src={ela.image_url}
              alt="ELA difference map"
              title="Click to enlarge"
              onClick={() => setLightbox(ela.image_url)}
            />
          </div>
        )}
      </div>

      <div className="disclaimer-note">
        ℹ️ ELA is an analytical indicator and should not be interpreted as definitive proof of
        manipulation. Many factors — including original image quality, content complexity,
        and prior compression — affect ELA output.
      </div>

      {lightbox && <Lightbox src={lightbox} onClose={() => setLightbox(null)} />}
    </div>
  )
}

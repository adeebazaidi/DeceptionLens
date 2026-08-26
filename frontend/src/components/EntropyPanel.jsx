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

export default function EntropyPanel({ entropy, originalFile }) {
  const [lightbox, setLightbox] = useState(null)

  if (!entropy) return null

  const originalUrl = originalFile ? URL.createObjectURL(originalFile) : null

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon card-icon-cyan" aria-hidden="true">📊</div>
        <div>
          <div className="card-title">Entropy Analysis</div>
          <div className="card-subtitle">Shannon information entropy</div>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">Global Entropy</div>
          <div className="stat-value">{entropy.global?.toFixed(3)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Mean Local</div>
          <div className="stat-value">{entropy.mean_local?.toFixed(3)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Std Dev</div>
          <div className="stat-value teal">{entropy.std_local?.toFixed(3)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Anomaly Score</div>
          <div className={`stat-value${entropy.anomaly_score > 0.2 ? ' amber' : ''}`}>
            {entropy.anomaly_score?.toFixed(4)}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
        <span className="stat-item" style={{ flex: 1, minWidth: 100 }}>
          <div className="stat-label">Min Local</div>
          <div className="stat-value" style={{ fontSize: '1rem' }}>{entropy.min_local?.toFixed(3)}</div>
        </span>
        <span className="stat-item" style={{ flex: 1, minWidth: 100 }}>
          <div className="stat-label">Max Local</div>
          <div className="stat-value" style={{ fontSize: '1rem' }}>{entropy.max_local?.toFixed(3)}</div>
        </span>
      </div>

      {/* Image viewers */}
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
        {entropy.heatmap_url && (
          <div className="img-viewer">
            <span className="img-viewer-label">Entropy Heatmap</span>
            <img
              src={entropy.heatmap_url}
              alt="Entropy heatmap overlay"
              title="Click to enlarge"
              onClick={() => setLightbox(entropy.heatmap_url)}
            />
          </div>
        )}
      </div>

      <div className="disclaimer-note">
        ℹ️ The anomaly score is a heuristic indicator (coefficient of variation of local entropy blocks).
        A higher value suggests greater local complexity variation — this does <em>not</em> constitute
        proof of manipulation.
      </div>

      {lightbox && <Lightbox src={lightbox} onClose={() => setLightbox(null)} />}
    </div>
  )
}

import { AlertTriangle, X } from 'lucide-react'

export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null
  return (
    <div className="error-box" role="alert" aria-live="assertive">
      <span className="error-icon" aria-hidden="true" style={{ display: 'flex' }}><AlertTriangle size={24} /></span>
      <div style={{ flex: 1 }}>
        <div className="error-title">Analysis Failed</div>
        <div className="error-message">{message}</div>
      </div>
      {onDismiss && (
        <button
          id="dismiss-error-button"
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '1.1rem',
            padding: '0.25rem',
            flexShrink: 0,
          }}
          aria-label="Dismiss error"
        >
          <X size={20} />
        </button>
      )}
    </div>
  )
}

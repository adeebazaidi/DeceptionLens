import { useRef, useState, useEffect } from 'react'
import { Fingerprint, FolderSearch, X, AlertCircle } from 'lucide-react'

const ALLOWED_EXTS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff']
const MAX_SIZE_MB = 10

function formatBytes(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export default function FingerprintUploader({
  title,
  subtitle,
  file,
  onFileSelect,
  disabled = false,
  badgeColor = 'cyan',
}) {
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')
  const [previewUrl, setPreviewUrl] = useState(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  function validateFile(f) {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTS.includes(ext)) {
      return `Unsupported format "${ext}". Supported: JPG, PNG, WEBP, BMP, TIF.`
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File exceeds ${MAX_SIZE_MB} MB limit.`
    }
    return null
  }

  function handleFile(f) {
    if (!f) return
    const err = validateFile(f)
    if (err) {
      setError(err)
      return
    }
    setError('')
    onFileSelect(f)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    const f = e.dataTransfer.files?.[0]
    if (f) handleFile(f)
  }

  function handleInputChange(e) {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
    e.target.value = ''
  }

  function handleRemove(e) {
    e.stopPropagation()
    setError('')
    onFileSelect(null)
  }

  return (
    <div className="fingerprint-uploader-card">
      <div className="card-header" style={{ marginBottom: '0.85rem' }}>
        <div className={`card-icon card-icon-${badgeColor}`} aria-hidden="true">
          <Fingerprint size={22} />
        </div>
        <div>
          <div className="card-title" style={{ fontSize: '1.05rem' }}>{title}</div>
          <div className="card-subtitle">{subtitle}</div>
        </div>
      </div>

      {!file ? (
        <div
          className={`uploader-zone fingerprint-drop-zone${dragOver ? ' drag-over' : ''}${disabled ? ' disabled' : ''}`}
          onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label={`Upload ${title}`}
          onKeyDown={(e) => e.key === 'Enter' && !disabled && inputRef.current?.click()}
        >
          <div className="uploader-icon" style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.75rem', color: `var(--accent-${badgeColor})` }}>
            <Fingerprint size={42} />
          </div>
          <div className="uploader-title" style={{ fontSize: '0.95rem' }}>Drag &amp; Drop Fingerprint</div>
          <div className="uploader-or" style={{ margin: '0.35rem 0' }}>— or —</div>
          <button
            className="btn-browse"
            type="button"
            disabled={disabled}
            onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', padding: '0.4rem 0.9rem' }}
          >
            <FolderSearch size={16} /> Choose File
          </button>
          <div className="uploader-formats" style={{ marginTop: '0.75rem', fontSize: '0.75rem' }}>
            <span>TIF · PNG · JPG · BMP</span>
            <span style={{ color: 'var(--text-muted)', marginLeft: '0.35rem' }}>· max {MAX_SIZE_MB}MB</span>
          </div>

          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTS.join(',')}
            style={{ display: 'none' }}
            onChange={handleInputChange}
          />
        </div>
      ) : (
        <div className="fingerprint-preview-container">
          <div className="preview-image-wrapper">
            {previewUrl && (
              <img
                src={previewUrl}
                alt={`${title} preview`}
                className="fingerprint-preview-img"
              />
            )}
            <button
              type="button"
              className="btn-remove-preview"
              onClick={handleRemove}
              title="Remove fingerprint"
              aria-label="Remove image"
            >
              <X size={16} />
            </button>
          </div>
          <div className="preview-meta-row">
            <span className="file-name" title={file.name}>{file.name}</span>
            <span className="file-size">{formatBytes(file.size)}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="upload-error-inline" role="alert" style={{ marginTop: '0.75rem', color: 'var(--risk-high)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}

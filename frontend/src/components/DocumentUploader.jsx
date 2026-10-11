import { useRef, useState } from 'react'
import { FileText, FolderSearch, Loader, Microscope, AlertTriangle, X } from 'lucide-react'

const ALLOWED_EXTS = ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff']
const MAX_SIZE_MB = 20

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DocumentUploader({ onFileSelect, onAnalyze, file, isAnalyzing }) {
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  function validateFile(f) {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTS.includes(ext)) {
      return `Unsupported format "${ext}". Please use PDF, JPG, PNG, or TIFF.`
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large (${formatBytes(f.size)}). Maximum allowed: ${MAX_SIZE_MB} MB.`
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
    if (onFileSelect) onFileSelect(f)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) handleFile(f)
  }

  function handleInputChange(e) {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
    e.target.value = ''
  }

  function handleRemove() {
    setError('')
    if (onFileSelect) onFileSelect(null)
  }

  return (
    <div>
      {!file ? (
        <div
          id="upload-drop-zone"
          className={`uploader-zone${dragOver ? ' drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Upload document for analysis"
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <span className="uploader-icon" aria-hidden="true" style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem', color: 'var(--accent-cyan)' }}><FileText size={48} /></span>
          <div className="uploader-title">Drag &amp; Drop Document Here</div>
          <div className="uploader-or">— or —</div>
          <button
            id="browse-button"
            className="btn-browse"
            type="button"
            onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <FolderSearch size={18} /> Browse Files
          </button>
          <div className="uploader-formats">
            {['PDF', 'JPG', 'PNG', 'TIFF'].map((f) => (
              <span key={f} className="format-tag">{f}</span>
            ))}
            <span style={{ color: 'var(--text-muted)', marginLeft: '0.25rem' }}>
              · max {MAX_SIZE_MB} MB
            </span>
          </div>

          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTS.join(',')}
            style={{ display: 'none' }}
            onChange={handleInputChange}
            id="file-input"
            aria-hidden="true"
          />
        </div>
      ) : (
        <div className="uploader-actions">
          <button
            id="analyze-button"
            className="btn btn-primary"
            onClick={onAnalyze}
            disabled={isAnalyzing}
            aria-label="Start document analysis"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {isAnalyzing ? <><Loader size={18} className="lucide-spin" /> Analyzing…</> : <><Microscope size={18} /> Analyze Document</>}
          </button>
          <button
            id="remove-document-button"
            className="btn btn-danger"
            onClick={handleRemove}
            disabled={isAnalyzing}
            aria-label="Remove selected document"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <X size={18} /> Remove
          </button>
        </div>
      )}

      {error && (
        <div className="error-box" style={{ marginTop: '1rem' }} role="alert">
          <span className="error-icon" style={{ display: 'flex' }}><AlertTriangle size={24} /></span>
          <div>
            <div className="error-title">File Error</div>
            <div className="error-message">{error}</div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useRef } from 'react'
import { UploadCloud, File, AlertCircle, X, CheckCircle2 } from 'lucide-react'

const EVIDENCE_TYPES = ['Image', 'Fingerprint', 'Signature', 'Document', 'Other']
const ALLOWED_EXTS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.pdf']
const MAX_SIZE_MB = 25

export default function EvidenceModal({
  isOpen,
  caseId,
  onUpload,
  onCancel,
  loading = false,
}) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [evidenceName, setEvidenceName] = useState('')
  const [evidenceType, setEvidenceType] = useState('Image')
  const [description, setDescription] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState(null)

  const fileInputRef = useRef(null)

  if (!isOpen) return null

  const handleFileSelect = (file) => {
    setError(null)
    if (!file) return

    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(
        `Unsupported file type '${ext}'. Supported formats: ${ALLOWED_EXTS.join(', ')}`
      )
      return
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File size exceeds maximum allowed ${MAX_SIZE_MB} MB limit.`)
      return
    }

    setSelectedFile(file)

    // Auto-fill evidence name if empty
    if (!evidenceName.trim()) {
      const base = file.name.substring(0, file.name.lastIndexOf('.')) || file.name
      setEvidenceName(base.replace(/[-_]/g, ' '))
    }

    // Auto-guess type from extension or name
    if (ext === '.pdf') {
      setEvidenceType('Document')
    } else if (file.name.toLowerCase().includes('fingerprint') || file.name.toLowerCase().includes('fvc')) {
      setEvidenceType('Fingerprint')
    } else if (file.name.toLowerCase().includes('sign') || file.name.toLowerCase().includes('sig')) {
      setEvidenceType('Signature')
    } else {
      setEvidenceType('Image')
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!selectedFile) {
      setError('Please select an evidence file to upload.')
      return
    }
    if (!evidenceName.trim()) {
      setError('Evidence name is required.')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('evidence_name', evidenceName.trim())
    formData.append('evidence_type', evidenceType)
    formData.append('description', description.trim())

    onUpload(formData)
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <div className="modal-backdrop" onClick={onCancel} role="dialog" aria-modal="true">
      <div className="modal-window evidence-modal-window" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div className="modal-icon-badge badge-primary">
              <UploadCloud size={18} />
            </div>
            <div>
              <h3 className="modal-title">Upload Digital Evidence</h3>
              <p className="modal-subtitle">
                Acquiring digital evidence for Case <code style={{ fontFamily: 'var(--font-mono)' }}>{caseId}</code>
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onCancel} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="modal-body">
            {error && (
              <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
                <AlertCircle size={16} /> <span>{error}</span>
              </div>
            )}

            {/* Drop Zone */}
            <div
              className={`dropzone ${isDragging ? 'dragging' : ''} ${selectedFile ? 'has-file' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: 'none' }}
                accept=".jpg,.jpeg,.png,.webp,.bmp,.tif,.tiff,.pdf"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              />

              {selectedFile ? (
                <div className="dropzone-file-info">
                  <div className="file-icon-wrapper">
                    <File size={28} />
                  </div>
                  <div>
                    <div className="file-name">{selectedFile.name}</div>
                    <div className="file-meta">
                      {formatFileSize(selectedFile.size)} • Cryptographic SHA-256 will be calculated on upload
                    </div>
                  </div>
                  <div style={{ marginLeft: 'auto', color: 'var(--risk-low)' }}>
                    <CheckCircle2 size={20} />
                  </div>
                </div>
              ) : (
                <div className="dropzone-prompt">
                  <UploadCloud size={36} className="dropzone-icon" />
                  <p className="dropzone-text">
                    <strong>Click to browse</strong> or drag & drop evidence file here
                  </p>
                  <p className="dropzone-subtext">
                    Supported: JPG, JPEG, PNG, WEBP, BMP, TIFF, PDF (Max {MAX_SIZE_MB} MB)
                  </p>
                </div>
              )}
            </div>

            <div className="form-group" style={{ marginTop: '1.25rem' }}>
              <label className="form-label required">Evidence Title / Identifier</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g., Questioned Deed of Sale Page 1"
                value={evidenceName}
                onChange={(e) => setEvidenceName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label required">Evidence Type</label>
              <select
                className="form-control"
                value={evidenceType}
                onChange={(e) => setEvidenceType(e.target.value)}
              >
                {EVIDENCE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Evidence Custody & Acquisition Notes</label>
              <textarea
                className="form-control textarea"
                rows={2}
                placeholder="Source of file, imaging device, seizing officer, or pertinent forensic chain-of-custody notes..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !selectedFile}
            >
              {loading ? 'Uploading & Hashing...' : 'Upload & Register Evidence'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

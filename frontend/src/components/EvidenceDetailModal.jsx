import { useState } from 'react'
import {
  FileText,
  Download,
  ShieldCheck,
  Copy,
  Check,
  AlertTriangle,
  X,
  Play,
  HardDrive,
  Hash,
  Eye,
} from 'lucide-react'
import { verifyEvidenceIntegrity, runEvidenceAnalysis } from '../api/caseApi'

export default function EvidenceDetailModal({
  isOpen,
  evidence,
  onClose,
  onEvidenceUpdated,
  onArchive,
}) {
  const [copied, setCopied] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [integrityResult, setIntegrityResult] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)

  if (!isOpen || !evidence) return null

  const handleCopyHash = () => {
    navigator.clipboard.writeText(evidence.sha256_hash)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleVerifyIntegrity = async () => {
    setVerifying(true)
    setError(null)
    try {
      const res = await verifyEvidenceIntegrity(evidence.evidence_id)
      setIntegrityResult(res)
    } catch (err) {
      setError(err.message || 'Failed to verify file integrity.')
    } finally {
      setVerifying(false)
    }
  }

  const handleRunAnalysis = async () => {
    setAnalyzing(true)
    setError(null)
    try {
      const res = await runEvidenceAnalysis(evidence.evidence_id)
      setAnalysisResult(res)
      if (onEvidenceUpdated) onEvidenceUpdated()
    } catch (err) {
      setError(err.message || 'Forensic analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const isImage =
    evidence.mime_type?.startsWith('image/') ||
    ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'].some((ext) =>
      evidence.original_filename?.toLowerCase().endsWith(ext)
    )

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-window evidence-detail-window" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div className="modal-icon-badge badge-primary">
              <FileText size={18} />
            </div>
            <div>
              <h3 className="modal-title">{evidence.evidence_name}</h3>
              <p className="modal-subtitle">
                Evidence ID: <code style={{ fontFamily: 'var(--font-mono)' }}>{evidence.evidence_id}</code>
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: '75vh', overflowY: 'auto' }}>
          {error && (
            <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
              <AlertTriangle size={16} /> <span>{error}</span>
            </div>
          )}

          {/* Top Actions Bar */}
          <div className="evidence-actions-bar">
            <a
              href={`/api/evidence/${evidence.evidence_id}/download`}
              className="btn btn-secondary btn-sm"
              download={evidence.original_filename}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={15} /> Download Original
            </a>

            <button
              className="btn btn-secondary btn-sm"
              onClick={handleVerifyIntegrity}
              disabled={verifying}
            >
              <ShieldCheck size={15} /> {verifying ? 'Recalculating SHA-256...' : 'Verify SHA-256 Integrity'}
            </button>

            <button
              className="btn btn-primary btn-sm"
              onClick={handleRunAnalysis}
              disabled={analyzing}
            >
              <Play size={15} /> {analyzing ? 'Analyzing in Engine...' : 'Run Forensic Analysis'}
            </button>

            {evidence.status !== 'Archived' && onArchive && (
              <button
                className="btn btn-secondary btn-sm btn-archive"
                onClick={() => onArchive(evidence)}
              >
                Archive
              </button>
            )}
          </div>

          {/* Integrity Verification Feedback Banner */}
          {integrityResult && (
            <div
              className={`integrity-result-card ${
                integrityResult.matches ? 'integrity-match' : 'integrity-mismatch'
              }`}
              style={{ marginTop: '1rem', marginBottom: '1rem' }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                <div className="integrity-icon-col">
                  {integrityResult.matches ? (
                    <ShieldCheck size={24} style={{ color: 'var(--risk-low)' }} />
                  ) : (
                    <AlertTriangle size={24} style={{ color: 'var(--risk-high)' }} />
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <div className="integrity-header-line">
                    <span className="integrity-status-text">
                      {integrityResult.status}
                    </span>
                    <span className="integrity-timestamp">
                      {new Date(integrityResult.verified_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="integrity-explanation">{integrityResult.explanation}</p>
                  <div className="hash-comparison-box">
                    <div>
                      <span className="hash-label">Baseline Recorded Hash:</span>
                      <code className="hash-code">{integrityResult.recorded_hash}</code>
                    </div>
                    {integrityResult.calculated_hash && (
                      <div style={{ marginTop: '0.25rem' }}>
                        <span className="hash-label">Recalculated Disk Hash:</span>
                        <code className="hash-code">{integrityResult.calculated_hash}</code>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Analysis Execution Result Alert */}
          {analysisResult && (
            <div className="alert alert-success" style={{ marginTop: '1rem', marginBottom: '1rem' }}>
              <ShieldCheck size={18} />
              <div>
                <strong>Forensic Analysis Complete ({analysisResult.module_type}):</strong>{' '}
                {analysisResult.result_summary} — Verdict: <strong>{analysisResult.verdict}</strong>
              </div>
            </div>
          )}

          {/* Preview Card */}
          <div className="evidence-preview-container">
            <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Eye size={16} /> Safe Content Preview
            </div>

            {isImage ? (
              <div className="image-preview-wrapper">
                <img
                  src={`/api/evidence/${evidence.evidence_id}/preview`}
                  alt={evidence.evidence_name}
                  className="evidence-img-preview"
                  onError={(e) => {
                    e.target.style.display = 'none'
                  }}
                />
              </div>
            ) : evidence.original_filename?.toLowerCase().endsWith('.pdf') ? (
              <div className="document-preview-placeholder">
                <FileText size={48} style={{ color: 'var(--accent-cyan)', opacity: 0.8 }} />
                <p style={{ marginTop: '0.5rem', fontWeight: 600 }}>PDF Forensic Document</p>
                <p className="text-muted text-sm">{evidence.original_filename}</p>
                <a
                  href={`/api/evidence/${evidence.evidence_id}/download`}
                  className="btn btn-secondary btn-sm"
                  style={{ marginTop: '0.75rem' }}
                >
                  <Download size={14} /> Open / Download File
                </a>
              </div>
            ) : (
              <div className="document-preview-placeholder">
                <HardDrive size={48} style={{ color: 'var(--text-muted)' }} />
                <p style={{ marginTop: '0.5rem', fontWeight: 600 }}>Binary Evidence File</p>
                <p className="text-muted text-sm">{evidence.original_filename}</p>
              </div>
            )}
          </div>

          {/* Stored Metadata Grid */}
          <div className="metadata-grid" style={{ marginTop: '1.25rem' }}>
            <div className="meta-card">
              <span className="meta-card-label">Case Identifier</span>
              <span className="meta-card-value">{evidence.case_id}</span>
            </div>

            <div className="meta-card">
              <span className="meta-card-label">Evidence Type</span>
              <span className="meta-card-value">
                <span className="badge badge-type">{evidence.evidence_type}</span>
              </span>
            </div>

            <div className="meta-card">
              <span className="meta-card-label">Original Filename</span>
              <span className="meta-card-value font-mono">{evidence.original_filename}</span>
            </div>

            <div className="meta-card">
              <span className="meta-card-label">File Size</span>
              <span className="meta-card-value">{formatFileSize(evidence.file_size)}</span>
            </div>

            <div className="meta-card">
              <span className="meta-card-label">MIME Type</span>
              <span className="meta-card-value font-mono">{evidence.mime_type}</span>
            </div>

            <div className="meta-card">
              <span className="meta-card-label">Upload Timestamp</span>
              <span className="meta-card-value">
                {evidence.uploaded_at ? new Date(evidence.uploaded_at).toLocaleString() : 'N/A'}
              </span>
            </div>
          </div>

          {/* Cryptographic Hash Section */}
          <div className="hash-container" style={{ marginTop: '1.25rem' }}>
            <div className="hash-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Hash size={16} />
                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>SHA-256 Baseline Fingerprint</span>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={handleCopyHash}
                title="Copy complete SHA-256 hash"
              >
                {copied ? <Check size={14} style={{ color: 'var(--risk-low)' }} /> : <Copy size={14} />}
                <span style={{ marginLeft: '4px' }}>{copied ? 'Copied' : 'Copy Hash'}</span>
              </button>
            </div>
            <code className="full-hash-block">{evidence.sha256_hash}</code>
            <p className="hash-note">
              Calculated upon evidence acquisition. Used as an immutable reference to verify that the
              file content has not changed while in the digital custody of DeceptionLens.
            </p>
          </div>

          {/* Description / Chain of Custody */}
          {evidence.description && (
            <div style={{ marginTop: '1.25rem' }}>
              <span className="meta-card-label">Acquisition & Custody Details</span>
              <p className="evidence-notes-text">{evidence.description}</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Layers,
  Printer,
  ShieldAlert,
  ShieldCheck,
  Tag,
  User,
  X,
} from 'lucide-react'
import { getSavedReport, reportDownloadUrl, verifyReport } from '../api/reportApi'

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function verdictBadge(verdict = '') {
  const v = verdict.toLowerCase()
  if (v.includes('low') || v.includes('authentic') || v.includes('consistent')) return 'badge-success'
  if (v.includes('high') || v.includes('forgery') || v.includes('suspicious')) return 'badge-danger'
  return 'badge-warning'
}

/**
 * Displays a saved, sealed report snapshot (as generated — not the live case).
 * Render with `key={reportId}` so each report starts from fresh state.
 */
export default function SavedReportModal({ reportId, onClose, onVerified }) {
  const [saved, setSaved] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [verification, setVerification] = useState(null)
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    if (!reportId) return undefined
    let isMounted = true
    getSavedReport(reportId)
      .then((data) => isMounted && setSaved(data))
      .catch((err) => isMounted && setError(err.message || 'Failed to load report.'))
      .finally(() => isMounted && setLoading(false))
    return () => {
      isMounted = false
    }
  }, [reportId])

  if (!reportId) return null

  const handleVerify = async () => {
    setVerifying(true)
    try {
      const result = await verifyReport(reportId)
      setVerification(result)
      onVerified?.(reportId, result)
    } catch (err) {
      setError(err.message || 'Verification failed.')
    } finally {
      setVerifying(false)
    }
  }

  const report = saved?.content

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="saved-report-title">
      <div
        className="modal-window report-modal-window"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '900px', width: '95vw', maxHeight: '90vh' }}
      >
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', minWidth: 0 }}>
            <div className="modal-icon-badge badge-primary">
              <FileText size={18} />
            </div>
            <div style={{ minWidth: 0 }}>
              <h3 className="modal-title" id="saved-report-title">{saved?.title || 'Saved Forensic Report'}</h3>
              <p className="modal-subtitle">Sealed snapshot · {reportId}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {saved && (
              <>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => window.print()} title="Print or save as PDF">
                  <Printer size={15} /> Print / PDF
                </button>
                <a className="btn btn-secondary btn-sm" href={reportDownloadUrl(reportId)} title="Download JSON">
                  <Download size={15} /> JSON
                </a>
              </>
            )}
            <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="modal-body print-area" style={{ overflowY: 'auto', maxHeight: 'calc(90vh - 130px)', padding: '1.5rem' }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              <div className="loading-spinner" style={{ margin: '0 auto 1rem auto' }} />
              <p>Loading saved report…</p>
            </div>
          )}

          {error && (
            <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {saved && report && (
            <div className="report-content">
              {/* Seal */}
              <div className="dl-seal-box">
                <div style={{ minWidth: 0, flex: '1 1 320px' }}>
                  <div className="report-label">Report seal (SHA-256)</div>
                  <code>{saved.sha256_hash}</code>
                  {verification && (
                    <div className={`dl-verify-result ${verification.matches ? 'ok' : 'bad'}`}>
                      {verification.matches ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
                      {verification.status}: {verification.explanation}
                    </div>
                  )}
                </div>
                <button type="button" className="btn btn-primary btn-sm" onClick={handleVerify} disabled={verifying}>
                  <ShieldCheck size={15} /> {verifying ? 'Verifying…' : 'Verify integrity'}
                </button>
              </div>

              {/* Banner */}
              <div className="report-banner" style={{ borderBottom: '2px solid var(--border-dim)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                      DeceptionLens Digital Forensics Laboratory
                    </h2>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
                      Automated Authenticity &amp; Forgery Detection Report
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{report.report_id}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Generated: {new Date(report.generated_at).toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>By: {saved.generated_by}</div>
                  </div>
                </div>
              </div>

              {/* Examiner notes */}
              {saved.notes && (
                <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                  <h4 className="report-section-title"><User size={16} /> Examiner Notes</h4>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', margin: 0 }}>{saved.notes}</p>
                </div>
              )}

              {/* Case overview */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title"><Tag size={16} /> Case Overview</h4>
                <div className="report-grid">
                  <div className="report-grid-item">
                    <span className="report-label">Case Identifier:</span>
                    <span className="report-val mono">{report.case_overview.case_id}</span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Case Title:</span>
                    <span className="report-val">{report.case_overview.title}</span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Primary Forensic Type:</span>
                    <span className="report-val">{report.case_overview.case_type}</span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Lead Investigator:</span>
                    <span className="report-val">{report.case_overview.investigator}</span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Investigation Priority:</span>
                    <span className={`badge badge-priority-${(report.case_overview.priority || '').toLowerCase()}`}>
                      {report.case_overview.priority}
                    </span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Status at Report Time:</span>
                    <span className={`badge badge-status-${(report.case_overview.status || '').toLowerCase().replace(/\s+/g, '-')}`}>
                      {report.case_overview.status}
                    </span>
                  </div>
                  <div className="report-grid-item full-width">
                    <span className="report-label">Investigation Synopsis:</span>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {report.case_overview.description || 'No detailed synopsis recorded.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Evidence */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <ShieldCheck size={16} /> Digital Evidence Inventory ({report.evidence_summary.total_items} Items)
                </h4>
                {report.evidence_summary.items.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No digital evidence items were registered to this case at report time.
                  </p>
                ) : (
                  <div className="table-responsive">
                    <table className="report-table">
                      <thead>
                        <tr><th>Evidence ID</th><th>Name / Source</th><th>Type</th><th>Size</th><th>SHA-256</th></tr>
                      </thead>
                      <tbody>
                        {report.evidence_summary.items.map((item) => (
                          <tr key={item.evidence_id}>
                            <td className="mono">{item.evidence_id}</td>
                            <td>
                              <strong>{item.evidence_name}</strong>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.original_filename}</div>
                            </td>
                            <td><span className="badge badge-secondary">{item.evidence_type}</span></td>
                            <td>{formatFileSize(item.file_size_bytes)}</td>
                            <td><code className="report-hash" title={item.sha256_hash}>{item.sha256_hash}</code></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Analyses */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <Layers size={16} /> Forensic Analysis Records ({report.forensic_analysis_records.length} Executed)
                </h4>
                {report.forensic_analysis_records.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No forensic analysis had been run on this case's evidence at report time.
                  </p>
                ) : (
                  <div className="table-responsive">
                    <table className="report-table">
                      <thead>
                        <tr><th>Record ID</th><th>Evidence</th><th>Module</th><th>Verdict</th><th>Result Summary</th><th>Date</th></tr>
                      </thead>
                      <tbody>
                        {report.forensic_analysis_records.map((rec) => (
                          <tr key={rec.record_id}>
                            <td className="mono">{rec.record_id}</td>
                            <td className="mono">{rec.evidence_id}</td>
                            <td>{rec.module_type}</td>
                            <td><span className={`badge ${verdictBadge(rec.verdict)}`}>{rec.verdict}</span></td>
                            <td>{rec.result_summary}</td>
                            <td>{rec.created_at ? new Date(rec.created_at).toLocaleDateString() : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Audit trail */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <Clock size={16} /> Chain of Custody &amp; Audit Trail ({report.audit_trail.length} Events)
                </h4>
                <div className="report-audit-list">
                  {report.audit_trail.map((evt, idx) => (
                    <div key={evt.event_id || idx} className="report-audit-item">
                      <div className="report-audit-time">{evt.created_at ? new Date(evt.created_at).toLocaleString() : 'N/A'}</div>
                      <div className="report-audit-main">
                        <span className="badge badge-action">{evt.action_type}</span>
                        <span className="report-audit-actor">by {evt.actor}</span>
                        {evt.details && Object.keys(evt.details).length > 0 && (
                          <span className="report-audit-details">{JSON.stringify(evt.details)}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="report-disclaimer-box">
                <strong>Forensic Disclaimer:</strong> {report.forensic_disclaimer}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

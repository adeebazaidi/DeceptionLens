import { useState, useEffect } from 'react'
import {
  FileText,
  Printer,
  Download,
  X,
  ShieldCheck,
  AlertCircle,
  Copy,
  Check,
  User,
  Tag,
  Clock,
  Layers,
} from 'lucide-react'
import { getCaseReport } from '../api/caseApi'

export default function ReportModal({ isOpen, caseId, onClose }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copiedHash, setCopiedHash] = useState(null)

  useEffect(() => {
    if (!isOpen || !caseId) {
      setReport(null)
      setError(null)
      return
    }

    let isMounted = true
    async function loadReport() {
      setLoading(true)
      setError(null)
      try {
        const data = await getCaseReport(caseId)
        if (isMounted) setReport(data)
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to generate forensic report.')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadReport()

    return () => {
      isMounted = false
    }
  }, [isOpen, caseId])

  if (!isOpen) return null

  const handleCopyHash = (hash) => {
    navigator.clipboard.writeText(hash)
    setCopiedHash(hash)
    setTimeout(() => setCopiedHash(null), 2000)
  }

  const handlePrint = () => {
    window.print()
  }

  const handleExportJson = () => {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Forensic_Report_${caseId}_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-window report-modal-window"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '900px', width: '95vw', maxHeight: '90vh' }}
      >
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div className="modal-icon-badge badge-primary">
              <FileText size={18} />
            </div>
            <div>
              <h3 className="modal-title">Forensic Investigation Report</h3>
              <p className="modal-subtitle">
                Official Case Summary &amp; Chain-of-Custody Document
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {report && (
              <>
                <button
                  type="button"
                  id="print-report-button"
                  className="btn btn-secondary btn-sm"
                  onClick={handlePrint}
                  title="Print official report"
                >
                  <Printer size={15} /> Print
                </button>
                <button
                  type="button"
                  id="export-json-button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleExportJson}
                  title="Export raw JSON"
                >
                  <Download size={15} /> JSON
                </button>
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
              <p>Compiling forensic case report and verifying chain-of-custody...</p>
            </div>
          )}

          {error && (
            <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {report && !loading && (
            <div className="report-content">
              {/* Header document banner */}
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
                    <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                      {report.report_id}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Generated: {new Date(report.generated_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* Case Overview */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <Tag size={16} /> Case Overview
                </h4>
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
                    <span className="report-val">
                      <User size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} />
                      {report.case_overview.investigator}
                    </span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Investigation Priority:</span>
                    <span className={`badge badge-priority-${(report.case_overview.priority || '').toLowerCase()}`}>
                      {report.case_overview.priority}
                    </span>
                  </div>
                  <div className="report-grid-item">
                    <span className="report-label">Current Status:</span>
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

              {/* Evidence Inventory */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <ShieldCheck size={16} /> Digital Evidence Inventory ({report.evidence_summary.total_items} Items)
                </h4>
                {report.evidence_summary.items.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No digital evidence items registered to this case.
                  </p>
                ) : (
                  <div className="table-responsive">
                    <table className="report-table">
                      <thead>
                        <tr>
                          <th>Evidence ID</th>
                          <th>Name / Source</th>
                          <th>Type</th>
                          <th>Size</th>
                          <th>Cryptographic Baseline (SHA-256)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.evidence_summary.items.map((item) => (
                          <tr key={item.evidence_id}>
                            <td className="mono">{item.evidence_id}</td>
                            <td>
                              <strong>{item.evidence_name}</strong>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {item.original_filename}
                              </div>
                            </td>
                            <td>
                              <span className="badge badge-secondary">{item.evidence_type}</span>
                            </td>
                            <td>{formatFileSize(item.file_size_bytes)}</td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                <code className="report-hash" title={item.sha256_hash}>
                                  {item.sha256_hash.substring(0, 16)}...
                                </code>
                                <button
                                  type="button"
                                  className="btn-icon-subtle"
                                  onClick={() => handleCopyHash(item.sha256_hash)}
                                  title="Copy complete SHA-256 hash"
                                >
                                  {copiedHash === item.sha256_hash ? (
                                    <Check size={13} style={{ color: 'var(--risk-low)' }} />
                                  ) : (
                                    <Copy size={13} />
                                  )}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Forensic Analysis Findings */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <Layers size={16} /> Forensic Analysis Records ({report.forensic_analysis_records.length} Executed)
                </h4>
                {report.forensic_analysis_records.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No automated forensic analysis modules have been run on this case's evidence yet.
                  </p>
                ) : (
                  <div className="table-responsive">
                    <table className="report-table">
                      <thead>
                        <tr>
                          <th>Record ID</th>
                          <th>Evidence Target</th>
                          <th>Module</th>
                          <th>Analytical Verdict</th>
                          <th>Result Summary</th>
                          <th>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.forensic_analysis_records.map((rec) => (
                          <tr key={rec.record_id}>
                            <td className="mono">{rec.record_id}</td>
                            <td className="mono">{rec.evidence_id}</td>
                            <td>{rec.module_type}</td>
                            <td>
                              <span
                                className={`badge ${
                                  rec.verdict?.toLowerCase().includes('low') || rec.verdict?.toLowerCase().includes('authentic')
                                    ? 'badge-success'
                                    : rec.verdict?.toLowerCase().includes('high') || rec.verdict?.toLowerCase().includes('forgery')
                                    ? 'badge-danger'
                                    : 'badge-warning'
                                }`}
                              >
                                {rec.verdict}
                              </span>
                            </td>
                            <td>{rec.result_summary}</td>
                            <td>{rec.created_at ? new Date(rec.created_at).toLocaleDateString() : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Audit Trail Timeline */}
              <div className="report-section" style={{ marginBottom: '1.5rem' }}>
                <h4 className="report-section-title">
                  <Clock size={16} /> Chain of Custody &amp; Audit Trail ({report.audit_trail.length} Events)
                </h4>
                <div className="report-audit-list">
                  {report.audit_trail.map((evt, idx) => (
                    <div key={evt.event_id || idx} className="report-audit-item">
                      <div className="report-audit-time">
                        {evt.created_at ? new Date(evt.created_at).toLocaleString() : 'N/A'}
                      </div>
                      <div className="report-audit-main">
                        <span className="badge badge-action">{evt.action_type}</span>
                        <span className="report-audit-actor">by {evt.actor}</span>
                        {evt.details && Object.keys(evt.details).length > 0 && (
                          <span className="report-audit-details">
                            {JSON.stringify(evt.details)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Legal Disclaimer */}
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

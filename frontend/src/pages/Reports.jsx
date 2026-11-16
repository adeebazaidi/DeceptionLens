import { useCallback, useEffect, useState } from 'react'
import {
  AlertTriangle,
  Archive,
  ArchiveRestore,
  CheckCircle2,
  Download,
  Eye,
  FilePlus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import { fetchCases } from '../api/caseApi'
import { fetchReports, generateReport, reportDownloadUrl, updateReportStatus, verifyReport } from '../api/reportApi'
import SavedReportModal from '../components/SavedReportModal.jsx'
import '../styles/reports.css'

const EMPTY_FORM = { case_id: '', generated_by: '', title: '', notes: '' }

/** Reports tab of the Dashboard & Reports module. */
export default function ReportsView() {
  const [cases, setCases] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [generating, setGenerating] = useState(false)

  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('Final')

  const [verifications, setVerifications] = useState({}) // report_id -> verify result
  const [viewing, setViewing] = useState(null)
  const [notification, setNotification] = useState(null)

  const notify = useCallback((message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 4000)
  }, [])

  const loadReports = useCallback(async () => {
    try {
      const data = await fetchReports({ search: search.trim(), status: statusFilter })
      setReports(data.reports)
    } catch (err) {
      notify(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter, notify])

  useEffect(() => {
    loadReports()
  }, [loadReports])

  useEffect(() => {
    fetchCases({ limit: 100, sort_by: 'created_at', sort_order: 'desc' })
      .then((data) => setCases(data.cases))
      .catch((err) => notify(`Could not load cases: ${err.message}`, 'error'))
  }, [notify])

  const handleCaseChange = (caseId) => {
    const selected = cases.find((c) => c.case_id === caseId)
    setForm((f) => ({
      ...f,
      case_id: caseId,
      generated_by: f.generated_by || selected?.investigator || '',
    }))
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!form.case_id || form.generated_by.trim().length < 2) {
      notify('Select a case and enter the examiner name (at least 2 characters).', 'error')
      return
    }
    setGenerating(true)
    try {
      const created = await generateReport(form)
      notify(`Report ${created.report_id} generated and sealed.`)
      setForm(EMPTY_FORM)
      if (statusFilter !== 'Final' && statusFilter !== 'all') setStatusFilter('Final')
      else loadReports()
      setViewing(created.report_id)
    } catch (err) {
      notify(err.message, 'error')
    } finally {
      setGenerating(false)
    }
  }

  const handleVerify = async (reportId) => {
    try {
      const result = await verifyReport(reportId)
      setVerifications((v) => ({ ...v, [reportId]: result }))
    } catch (err) {
      notify(err.message, 'error')
    }
  }

  const handleStatus = async (report, nextStatus) => {
    if (nextStatus === 'Archived' && !window.confirm(`Archive report ${report.report_id}? It stays stored and can be restored.`)) {
      return
    }
    try {
      await updateReportStatus(report.report_id, nextStatus)
      notify(`Report ${report.report_id} ${nextStatus === 'Archived' ? 'archived' : 'restored'}.`)
      loadReports()
    } catch (err) {
      notify(err.message, 'error')
    }
  }

  return (
    <section id="reports-view">
      {notification && (
        <div className={`toast-alert toast-${notification.type}`} role="status" aria-live="polite">
          {notification.type === 'error' ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          <span>{notification.message}</span>
        </div>
      )}

      <div className="dl-view-toolbar">
        <p>Generate official case reports, keep them as SHA-256-sealed snapshots, and verify they were never altered.</p>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            setLoading(true)
            loadReports()
          }}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {/* Generate */}
      <section className="dl-panel dl-panel-wide">
        <h2 className="dl-panel-title">Generate a new report</h2>
        <p className="dl-panel-sub">
          Captures the case exactly as it is now — evidence, hashes, analysis results, and audit trail — and seals it.
        </p>
        <form onSubmit={handleGenerate} className="dl-form-grid">
          <div className="form-group">
            <label className="form-label required" htmlFor="report-case">Case</label>
            <select
              id="report-case"
              className="form-control"
              value={form.case_id}
              onChange={(e) => handleCaseChange(e.target.value)}
            >
              <option value="">Select a case…</option>
              {cases.map((c) => (
                <option key={c.case_id} value={c.case_id}>{c.case_id} — {c.title}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label required" htmlFor="report-examiner">Generated by</label>
            <input
              id="report-examiner"
              className="form-control"
              value={form.generated_by}
              onChange={(e) => setForm((f) => ({ ...f, generated_by: e.target.value }))}
              placeholder="Examiner name"
              maxLength={128}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="report-title">Title (optional)</label>
            <input
              id="report-title"
              className="form-control"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Leave blank for default title"
              maxLength={255}
            />
          </div>
          <div className="form-group full">
            <label className="form-label" htmlFor="report-notes">Examiner notes / conclusions (optional)</label>
            <textarea
              id="report-notes"
              className="form-control textarea"
              rows={3}
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              maxLength={5000}
            />
          </div>
          <div className="full">
            <button type="submit" className="btn btn-primary" disabled={generating}>
              <FilePlus size={16} /> {generating ? 'Generating…' : 'Generate & seal report'}
            </button>
          </div>
        </form>
      </section>

      {/* Filters */}
      <div className="cases-toolbar" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', padding: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border-dim)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
        <div style={{ flex: '1 1 240px', position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            className="form-control"
            placeholder="Search report ID, title, case ID, or examiner…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '2.25rem' }}
            aria-label="Search reports"
          />
        </div>
        <div style={{ flex: '0 1 180px' }}>
          <select className="form-control" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label="Report status">
            <option value="Final">Active reports</option>
            <option value="Archived">Archived reports</option>
            <option value="all">All reports</option>
          </select>
        </div>
      </div>

      {/* List */}
      <section className="dl-panel">
        <h2 className="dl-panel-title">Saved reports ({reports.length})</h2>
        <p className="dl-panel-sub">Newest first. Generating, downloading, verifying, and archiving are recorded in the case audit trail.</p>

        {loading && reports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            <div className="loading-spinner" style={{ margin: '0 auto 0.75rem auto' }} />
            Loading reports…
          </div>
        ) : reports.length === 0 ? (
          <p className="dl-empty">No reports match. Generate one above.</p>
        ) : (
          <div className="table-responsive">
            <table className="dl-table">
              <thead>
                <tr>
                  <th>Report</th>
                  <th>Case</th>
                  <th>Examiner</th>
                  <th>Contents</th>
                  <th>Generated</th>
                  <th>Seal</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => {
                  const v = verifications[r.report_id]
                  return (
                    <tr key={r.report_id}>
                      <td>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{r.title}</div>
                        <div className="dl-mono">{r.report_id}</div>
                        {r.status === 'Archived' && <span className="badge badge-secondary" style={{ marginTop: '0.25rem' }}>Archived</span>}
                      </td>
                      <td>
                        <div>{r.case_title}</div>
                        <div className="dl-mono">{r.case_id}</div>
                      </td>
                      <td>{r.generated_by}</td>
                      <td className="dl-muted">
                        {r.evidence_count} evidence<br />
                        {r.analysis_count} {r.analysis_count === 1 ? 'analysis' : 'analyses'}
                      </td>
                      <td className="dl-muted">{r.created_at ? new Date(r.created_at).toLocaleString() : 'N/A'}</td>
                      <td>
                        <code className="dl-mono" title={r.sha256_hash}>{r.sha256_hash.slice(0, 12)}…</code>
                        {v && (
                          <div className={`dl-verify-result ${v.matches ? 'ok' : 'bad'}`}>
                            {v.matches ? <ShieldCheck size={13} /> : <ShieldAlert size={13} />}
                            {v.status}
                          </div>
                        )}
                      </td>
                      <td>
                        <div className="dl-actions">
                          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setViewing(r.report_id)}>
                            <Eye size={14} /> View
                          </button>
                          <a className="btn btn-secondary btn-sm" href={reportDownloadUrl(r.report_id)}>
                            <Download size={14} /> JSON
                          </a>
                          <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleVerify(r.report_id)}>
                            <ShieldCheck size={14} /> Verify
                          </button>
                          {r.status === 'Archived' ? (
                            <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleStatus(r, 'Final')}>
                              <ArchiveRestore size={14} /> Restore
                            </button>
                          ) : (
                            <button type="button" className="btn btn-danger btn-sm" onClick={() => handleStatus(r, 'Archived')}>
                              <Archive size={14} /> Archive
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <SavedReportModal
        key={viewing || 'none'}
        reportId={viewing}
        onClose={() => setViewing(null)}
        onVerified={(id, result) => setVerifications((v) => ({ ...v, [id]: result }))}
      />
    </section>
  )
}

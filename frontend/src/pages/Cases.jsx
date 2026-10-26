import { useState, useEffect, useCallback } from 'react'
import {
  FolderPlus,
  FolderOpen,
  Search,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  Clock,
  User,
  Tag,
  Download,
  Trash2,
  Edit3,
  CheckCircle2,
  UploadCloud,
  ChevronLeft,
  ChevronRight,
  Eye,
  Copy,
  Check,
  Layers,
  ArrowUpDown,
  FileCheck,
} from 'lucide-react'

import {
  fetchCases,
  createCase,
  getCaseDetails,
  updateCase,
  updateCaseStatus,
  archiveCase,
  uploadEvidence,
  updateEvidenceStatus,
  getCaseAuditLogs,
  fetchDashboardStats,
} from '../api/caseApi'

import CaseModal from '../components/CaseModal.jsx'
import EvidenceModal from '../components/EvidenceModal.jsx'
import EvidenceDetailModal from '../components/EvidenceDetailModal.jsx'
import ConfirmModal from '../components/ConfirmModal.jsx'
import ReportModal from '../components/ReportModal.jsx'

const CASE_TYPES = [
  'All Types',
  'Image Forgery',
  'Fingerprint Verification',
  'Signature Verification',
  'Document Analysis',
  'Other',
]

const PRIORITIES = ['All Priorities', 'Low', 'Medium', 'High', 'Critical']
const STATUSES = ['All Statuses', 'Open', 'In Progress', 'Under Review', 'Closed']

export default function Cases() {
  // ── Dashboard Stats State ──────────────────────────────────────────────────
  const [stats, setStats] = useState({
    total_cases: 0,
    open_cases: 0,
    in_progress_cases: 0,
    under_review_cases: 0,
    closed_cases: 0,
    total_evidence: 0,
  })

  // ── Filters & Search State ─────────────────────────────────────────────────
  const [search, setSearch] = useState('')
  const [selectedCaseType, setSelectedCaseType] = useState('All Types')
  const [selectedPriority, setSelectedPriority] = useState('All Priorities')
  const [selectedStatus, setSelectedStatus] = useState('All Statuses')
  const [includeArchived, setIncludeArchived] = useState(false)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [page, setPage] = useState(1)
  const [limit] = useState(8)

  // ── Cases List State ───────────────────────────────────────────────────────
  const [cases, setCases] = useState([])
  const [totalCases, setTotalCases] = useState(0)
  const [loadingCases, setLoadingCases] = useState(false)
  const [casesError, setCasesError] = useState(null)

  // ── Selected Case & Detail State ───────────────────────────────────────────
  const [selectedCaseId, setSelectedCaseId] = useState(null)
  const [selectedCase, setSelectedCase] = useState(null)
  const [loadingCaseDetail, setLoadingCaseDetail] = useState(false)
  const [activeTab, setActiveTab] = useState('evidence') // 'evidence' | 'audit' | 'analysis'
  const [auditLogs, setAuditLogs] = useState([])
  const [loadingAuditLogs, setLoadingAuditLogs] = useState(false)

  // ── Modals State ───────────────────────────────────────────────────────────
  const [isCaseModalOpen, setIsCaseModalOpen] = useState(false)
  const [caseModalMode, setCaseModalMode] = useState('create') // 'create' | 'edit'
  const [caseModalInitialData, setCaseModalInitialData] = useState(null)
  const [caseModalLoading, setCaseModalLoading] = useState(false)

  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false)
  const [evidenceModalLoading, setEvidenceModalLoading] = useState(false)

  const [selectedEvidenceForDetail, setSelectedEvidenceForDetail] = useState(null)
  const [isEvidenceDetailModalOpen, setIsEvidenceDetailModalOpen] = useState(false)

  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false)
  const [confirmConfig, setConfirmConfig] = useState({
    title: '',
    message: '',
    confirmText: 'Confirm',
    confirmVariant: 'danger',
    onConfirm: () => {},
  })
  const [confirmLoading, setConfirmLoading] = useState(false)

  const [isReportModalOpen, setIsReportModalOpen] = useState(false)
  const [copiedCaseId, setCopiedCaseId] = useState(null)
  const [copiedHash, setCopiedHash] = useState(null)
  const [notification, setNotification] = useState(null)

  // ── Toast Helper ───────────────────────────────────────────────────────────
  const showToast = (message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 4000)
  }

  // ── Load Dashboard Stats ───────────────────────────────────────────────────
  const loadStats = useCallback(async () => {
    try {
      const data = await fetchDashboardStats()
      setStats(data)
    } catch {
      // Non-blocking fallback
    }
  }, [])

  // ── Load Cases List ────────────────────────────────────────────────────────
  const loadCases = useCallback(async () => {
    setLoadingCases(true)
    setCasesError(null)
    try {
      const params = {
        page,
        limit,
        sort_by: sortBy,
        sort_order: sortOrder,
        include_archived: includeArchived,
      }
      if (search.trim()) params.search = search.trim()
      if (selectedCaseType !== 'All Types') params.case_type = selectedCaseType
      if (selectedPriority !== 'All Priorities') params.priority = selectedPriority
      if (selectedStatus !== 'All Statuses') params.status = selectedStatus

      const data = await fetchCases(params)
      setCases(data.cases || [])
      setTotalCases(data.total || 0)

      // If currently selected case is no longer in list, or not set yet, pick first case if available
      if (data.cases && data.cases.length > 0) {
        if (!selectedCaseId || !data.cases.some((c) => c.case_id === selectedCaseId)) {
          setSelectedCaseId(data.cases[0].case_id)
        }
      } else {
        setSelectedCaseId(null)
        setSelectedCase(null)
      }
    } catch (err) {
      setCasesError(err.message || 'Failed to load forensic cases.')
    } finally {
      setLoadingCases(false)
    }
  }, [page, limit, sortBy, sortOrder, includeArchived, search, selectedCaseType, selectedPriority, selectedStatus, selectedCaseId])

  // ── Load Selected Case Details ─────────────────────────────────────────────
  const loadCaseDetails = useCallback(async (caseId) => {
    if (!caseId) {
      setSelectedCase(null)
      return
    }
    setLoadingCaseDetail(true)
    try {
      const data = await getCaseDetails(caseId)
      setSelectedCase(data)
    } catch (err) {
      showToast(err.message || 'Failed to load case details.', 'error')
    } finally {
      setLoadingCaseDetail(false)
    }
  }, [])

  // ── Load Audit Logs for Selected Case ──────────────────────────────────────
  const loadAuditLogs = useCallback(async (caseId) => {
    if (!caseId) {
      setAuditLogs([])
      return
    }
    setLoadingAuditLogs(true)
    try {
      const data = await getCaseAuditLogs(caseId)
      setAuditLogs(data.audit_logs || [])
    } catch {
      setAuditLogs([])
    } finally {
      setLoadingAuditLogs(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    loadStats()
  }, [loadStats])

  useEffect(() => {
    loadCases()
  }, [loadCases])

  // Load details whenever selectedCaseId changes
  useEffect(() => {
    if (selectedCaseId) {
      loadCaseDetails(selectedCaseId)
      if (activeTab === 'audit') {
        loadAuditLogs(selectedCaseId)
      }
    }
  }, [selectedCaseId, loadCaseDetails, activeTab, loadAuditLogs])

  // Reload audit logs when switching to audit tab
  useEffect(() => {
    if (activeTab === 'audit' && selectedCaseId) {
      loadAuditLogs(selectedCaseId)
    }
  }, [activeTab, selectedCaseId, loadAuditLogs])

  // ── Case Actions ───────────────────────────────────────────────────────────
  const handleOpenCreateCase = () => {
    setCaseModalMode('create')
    setCaseModalInitialData(null)
    setIsCaseModalOpen(true)
  }

  const handleOpenEditCase = (caseItem) => {
    setCaseModalMode('edit')
    setCaseModalInitialData(caseItem)
    setIsCaseModalOpen(true)
  }

  const handleSaveCase = async (formData) => {
    setCaseModalLoading(true)
    try {
      if (caseModalMode === 'create') {
        const created = await createCase(formData)
        showToast(`Case '${created.case_id}' successfully created.`)
        setIsCaseModalOpen(false)
        await loadStats()
        setSelectedCaseId(created.case_id)
        await loadCases()
      } else {
        const updated = await updateCase(caseModalInitialData.case_id, formData)
        showToast(`Case '${updated.case_id}' updated.`)
        setIsCaseModalOpen(false)
        await loadStats()
        await loadCases()
        await loadCaseDetails(updated.case_id)
      }
    } catch (err) {
      showToast(err.message || 'Operation failed.', 'error')
    } finally {
      setCaseModalLoading(false)
    }
  }

  const handleStatusChange = async (newStatus) => {
    if (!selectedCase || selectedCase.status === newStatus) return
    try {
      await updateCaseStatus(selectedCase.case_id, newStatus, `Status transitioned to ${newStatus}`)
      showToast(`Case status updated to ${newStatus}.`)
      await loadStats()
      await loadCases()
      await loadCaseDetails(selectedCase.case_id)
      if (activeTab === 'audit') loadAuditLogs(selectedCase.case_id)
    } catch (err) {
      showToast(err.message || 'Failed to update case status.', 'error')
    }
  }

  const handleConfirmArchiveCase = (caseItem) => {
    setConfirmConfig({
      title: 'Archive Forensic Case',
      message: `Are you sure you want to archive '${caseItem.case_id}: ${caseItem.title}'? All associated evidence files and audit records will remain securely stored and accessible via 'Include Archived'.`,
      confirmText: 'Archive Case',
      confirmVariant: 'danger',
      onConfirm: async () => {
        setConfirmLoading(true)
        try {
          await archiveCase(caseItem.case_id)
          showToast(`Case '${caseItem.case_id}' has been archived.`)
          setIsConfirmModalOpen(false)
          await loadStats()
          await loadCases()
        } catch (err) {
          showToast(err.message || 'Failed to archive case.', 'error')
        } finally {
          setConfirmLoading(false)
        }
      },
    })
    setIsConfirmModalOpen(true)
  }

  // ── Evidence Actions ───────────────────────────────────────────────────────
  const handleOpenUploadEvidence = () => {
    if (!selectedCase) return
    setIsEvidenceModalOpen(true)
  }

  const handleUploadEvidence = async (formData) => {
    if (!selectedCase) return
    setEvidenceModalLoading(true)
    try {
      const res = await uploadEvidence(selectedCase.case_id, formData)
      showToast(`Evidence '${res.evidence_name}' (${res.evidence_id}) successfully acquired.`)
      setIsEvidenceModalOpen(false)
      await loadStats()
      await loadCaseDetails(selectedCase.case_id)
      if (activeTab === 'audit') loadAuditLogs(selectedCase.case_id)
    } catch (err) {
      showToast(err.message || 'Evidence upload failed.', 'error')
    } finally {
      setEvidenceModalLoading(false)
    }
  }

  const handleInspectEvidence = (evidenceItem) => {
    setSelectedEvidenceForDetail(evidenceItem)
    setIsEvidenceDetailModalOpen(true)
  }

  const handleArchiveEvidence = (evidenceItem) => {
    setConfirmConfig({
      title: 'Archive Evidence Item',
      message: `Are you sure you want to archive evidence '${evidenceItem.evidence_name}' (${evidenceItem.evidence_id})? The physical file and SHA-256 baseline are preserved.`,
      confirmText: 'Archive Evidence',
      confirmVariant: 'danger',
      onConfirm: async () => {
        setConfirmLoading(true)
        try {
          await updateEvidenceStatus(evidenceItem.evidence_id, 'Archived', 'Archived by examiner request.')
          showToast(`Evidence item archived.`)
          setIsConfirmModalOpen(false)
          setIsEvidenceDetailModalOpen(false)
          await loadStats()
          await loadCaseDetails(selectedCase.case_id)
        } catch (err) {
          showToast(err.message || 'Failed to archive evidence.', 'error')
        } finally {
          setConfirmLoading(false)
        }
      },
    })
    setIsConfirmModalOpen(true)
  }

  const handleCopyCaseId = (id) => {
    navigator.clipboard.writeText(id)
    setCopiedCaseId(id)
    setTimeout(() => setCopiedCaseId(null), 2000)
  }

  const handleCopyHash = (hash) => {
    navigator.clipboard.writeText(hash)
    setCopiedHash(hash)
    setTimeout(() => setCopiedHash(null), 2000)
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const totalPages = Math.max(1, Math.ceil(totalCases / limit))

  return (
    <main className="cases-page" id="cases-page" style={{ padding: '1.5rem 2rem 4rem 2rem', minHeight: 'calc(100vh - 70px)' }}>
      {/* Toast Alert */}
      {notification && (
        <div
          className={`toast-alert toast-${notification.type}`}
          role="status"
          aria-live="polite"
        >
          {notification.type === 'error' ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="cases-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <div className="hero-badge" style={{ marginBottom: '0.5rem' }}>
            <span className="hero-badge-dot" aria-hidden="true" />
            Digital Chain of Custody
          </div>
          <h1 className="page-title" style={{ margin: 0, fontSize: '2rem', fontWeight: 800 }}>
            Case &amp; Evidence Management
          </h1>
          <p className="page-subtitle" style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Investigative case registry, digital evidence custody chain, and cryptographic SHA-256 integrity verification.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            type="button"
            id="refresh-cases-btn"
            className="btn btn-secondary"
            onClick={() => {
              loadStats()
              loadCases()
              if (selectedCaseId) loadCaseDetails(selectedCaseId)
            }}
            disabled={loadingCases}
            title="Refresh database records"
          >
            <RefreshCw size={16} className={loadingCases ? 'spin' : ''} /> Refresh
          </button>

          <button
            type="button"
            id="create-new-case-btn"
            className="btn btn-primary"
            onClick={handleOpenCreateCase}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            <FolderPlus size={18} /> New Case
          </button>
        </div>
      </div>

      {/* Dashboard Statistics Bar */}
      <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="stat-card" onClick={() => setSelectedStatus('All Statuses')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Total Cases</div>
          <div className="stat-value">{stats.total_cases || 0}</div>
          <div className="stat-sub">Registered Records</div>
        </div>

        <div className="stat-card stat-open" onClick={() => setSelectedStatus('Open')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Open Cases</div>
          <div className="stat-value" style={{ color: 'var(--risk-low)' }}>{stats.open_cases || 0}</div>
          <div className="stat-sub">Initial Intake</div>
        </div>

        <div className="stat-card stat-progress" onClick={() => setSelectedStatus('In Progress')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">In Progress</div>
          <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>{stats.in_progress_cases || 0}</div>
          <div className="stat-sub">Active Analysis</div>
        </div>

        <div className="stat-card stat-review" onClick={() => setSelectedStatus('Under Review')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Under Review</div>
          <div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>{stats.under_review_cases || 0}</div>
          <div className="stat-sub">Peer Verification</div>
        </div>

        <div className="stat-card stat-closed" onClick={() => setSelectedStatus('Closed')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Closed</div>
          <div className="stat-value" style={{ color: 'var(--text-muted)' }}>{stats.closed_cases || 0}</div>
          <div className="stat-sub">Concluded Audits</div>
        </div>

        <div className="stat-card stat-evidence">
          <div className="stat-label">Active Evidence</div>
          <div className="stat-value" style={{ color: 'var(--accent-teal)' }}>{stats.total_evidence || 0}</div>
          <div className="stat-sub">Verified Files</div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="cases-toolbar" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', padding: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border-dim)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem' }}>
        {/* Search */}
        <div style={{ flex: '1 1 240px', position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            id="case-search-input"
            className="form-control"
            placeholder="Search Case ID or Title..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            style={{ paddingLeft: '2.25rem' }}
          />
        </div>

        {/* Case Type Filter */}
        <div style={{ flex: '0 1 180px' }}>
          <select
            id="case-type-filter"
            className="form-control"
            value={selectedCaseType}
            onChange={(e) => {
              setSelectedCaseType(e.target.value)
              setPage(1)
            }}
          >
            {CASE_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Priority Filter */}
        <div style={{ flex: '0 1 150px' }}>
          <select
            id="case-priority-filter"
            className="form-control"
            value={selectedPriority}
            onChange={(e) => {
              setSelectedPriority(e.target.value)
              setPage(1)
            }}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div style={{ flex: '0 1 150px' }}>
          <select
            id="case-status-filter"
            className="form-control"
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value)
              setPage(1)
            }}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Sort Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <select
            id="case-sort-by"
            className="form-control"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{ width: '130px' }}
          >
            <option value="created_at">Date Created</option>
            <option value="updated_at">Last Updated</option>
            <option value="title">Case Title</option>
            <option value="priority">Priority</option>
          </select>

          <button
            type="button"
            className="btn btn-secondary btn-icon"
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            title={`Sort order: ${sortOrder.toUpperCase()}`}
            aria-label="Toggle sort order"
          >
            <ArrowUpDown size={15} />
          </button>
        </div>

        {/* Archive Toggle */}
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            id="case-include-archived"
            checked={includeArchived}
            onChange={(e) => {
              setIncludeArchived(e.target.checked)
              setPage(1)
            }}
          />
          Show Archived
        </label>
      </div>

      {/* Master-Detail Split Workspace */}
      <div className="cases-workspace" style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Cases List */}
        <div className="cases-list-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 0.25rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              CASES REGISTRY ({totalCases})
            </span>
            {totalCases > 0 && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Page {page} of {totalPages}
              </span>
            )}
          </div>

          {casesError && (
            <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={16} /> <span>{casesError}</span>
            </div>
          )}

          {loadingCases && (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-dim)' }}>
              <div className="loading-spinner" style={{ margin: '0 auto 0.75rem auto' }} />
              <p style={{ fontSize: '0.875rem' }}>Loading forensic cases...</p>
            </div>
          )}

          {!loadingCases && cases.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem 1.5rem', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-dim)' }}>
              <FolderOpen size={40} style={{ color: 'var(--text-muted)', margin: '0 auto 0.75rem auto', opacity: 0.6 }} />
              <h4 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>No Cases Found</h4>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                No forensic cases match your current filter criteria.
              </p>
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleOpenCreateCase}>
                <FolderPlus size={14} /> Create First Case
              </button>
            </div>
          )}

          {!loadingCases && cases.map((c) => {
            const isSelected = selectedCaseId === c.case_id
            return (
              <div
                key={c.case_id}
                id={`case-card-${c.case_id}`}
                className={`case-card ${isSelected ? 'case-card-active' : ''}`}
                onClick={() => setSelectedCaseId(c.case_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setSelectedCaseId(c.case_id)
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <span className="case-id-badge mono">{c.case_id}</span>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    <span className={`badge badge-priority-${(c.priority || 'medium').toLowerCase()}`}>
                      {c.priority}
                    </span>
                    <span className={`badge badge-status-${(c.status || 'open').toLowerCase().replace(/\s+/g, '-')}`}>
                      {c.status}
                    </span>
                  </div>
                </div>

                <h3 className="case-card-title">{c.title}</h3>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <Tag size={12} /> {c.case_type}
                  </span>
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-dim)', paddingTop: '0.5rem', marginTop: '0.5rem', fontSize: '0.78rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    <User size={12} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '3px' }} />
                    {c.investigator}
                  </span>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button
                      type="button"
                      className="btn-icon-subtle"
                      title="Edit Case"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleOpenEditCase(c)
                      }}
                      aria-label="Edit case"
                    >
                      <Edit3 size={13} />
                    </button>
                    {!c.is_archived && (
                      <button
                        type="button"
                        className="btn-icon-subtle text-danger"
                        title="Archive Case"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleConfirmArchiveCase(c)
                        }}
                        aria-label="Archive case"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
              <button
                type="button"
                id="cases-prev-page"
                className="btn btn-secondary btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft size={14} /> Previous
              </button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {page} / {totalPages}
              </span>
              <button
                type="button"
                id="cases-next-page"
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Case Details & Workspace */}
        <div className="case-detail-workspace">
          {!selectedCase && !loadingCaseDetail && (
            <div className="empty-workspace-placeholder" style={{ textAlign: 'center', padding: '5rem 2rem', background: 'var(--bg-card)', border: '1px solid var(--border-dim)', borderRadius: 'var(--radius-lg)' }}>
              <FolderOpen size={56} style={{ color: 'var(--accent-cyan)', opacity: 0.5, margin: '0 auto 1.5rem auto' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>No Case Selected</h2>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '420px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
                Select an existing forensic investigation from the registry on the left, or create a new case to begin acquiring and analyzing evidence.
              </p>
              <button type="button" className="btn btn-primary" onClick={handleOpenCreateCase}>
                <FolderPlus size={16} /> Create New Case
              </button>
            </div>
          )}

          {loadingCaseDetail && (
            <div style={{ textAlign: 'center', padding: '5rem 2rem', background: 'var(--bg-card)', border: '1px solid var(--border-dim)', borderRadius: 'var(--radius-lg)' }}>
              <div className="loading-spinner" style={{ margin: '0 auto 1rem auto' }} />
              <p style={{ color: 'var(--text-muted)' }}>Loading case workspace...</p>
            </div>
          )}

          {selectedCase && !loadingCaseDetail && (
            <div className="case-detail-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-dim)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {/* Detail Header Banner */}
              <div className="case-detail-header" style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-dim)', background: 'linear-gradient(180deg, rgba(167, 22, 102, 0.05) 0%, transparent 100%)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                  <div style={{ flex: '1 1 300px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                      <span className="case-id-badge mono" style={{ fontSize: '0.85rem' }}>
                        {selectedCase.case_id}
                      </span>
                      <button
                        type="button"
                        className="btn-icon-subtle"
                        onClick={() => handleCopyCaseId(selectedCase.case_id)}
                        title="Copy Case ID"
                      >
                        {copiedCaseId === selectedCase.case_id ? <Check size={14} style={{ color: 'var(--risk-low)' }} /> : <Copy size={14} />}
                      </button>
                      <span className={`badge badge-priority-${(selectedCase.priority || 'medium').toLowerCase()}`}>
                        {selectedCase.priority} Priority
                      </span>
                    </div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                      {selectedCase.title}
                    </h2>
                  </div>

                  {/* Actions Toolbar */}
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    {/* Status Dropdown */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Status:</span>
                      <select
                        id="case-status-selector"
                        className="form-control form-control-sm"
                        value={selectedCase.status}
                        onChange={(e) => handleStatusChange(e.target.value)}
                        style={{ fontWeight: 600, width: '135px' }}
                      >
                        <option value="Open">Open</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Under Review">Under Review</option>
                        <option value="Closed">Closed</option>
                      </select>
                    </div>

                    <button
                      type="button"
                      id="upload-evidence-top-btn"
                      className="btn btn-primary btn-sm"
                      onClick={handleOpenUploadEvidence}
                    >
                      <UploadCloud size={15} /> Upload Evidence
                    </button>

                    <button
                      type="button"
                      id="view-report-top-btn"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setIsReportModalOpen(true)}
                    >
                      <FileCheck size={15} /> View Report
                    </button>

                    <button
                      type="button"
                      className="btn btn-secondary btn-sm btn-icon"
                      onClick={() => handleOpenEditCase(selectedCase)}
                      title="Edit Case Parameters"
                    >
                      <Edit3 size={15} />
                    </button>

                    <button
                      type="button"
                      className="btn btn-secondary btn-sm btn-icon text-danger"
                      onClick={() => handleConfirmArchiveCase(selectedCase)}
                      title="Archive Case"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                {/* Metadata Summary Line */}
                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Investigator: </span>
                    <strong>{selectedCase.investigator}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Category: </span>
                    <strong>{selectedCase.case_type}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Opened: </span>
                    {new Date(selectedCase.created_at).toLocaleString()}
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Last Modified: </span>
                    {new Date(selectedCase.updated_at).toLocaleString()}
                  </div>
                </div>

                {/* Synopsis */}
                {selectedCase.description && (
                  <p style={{ marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--text-secondary)', background: 'var(--bg-card-hover)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--accent-cyan)' }}>
                    {selectedCase.description}
                  </p>
                )}
              </div>

              {/* Workspace Navigation Tabs */}
              <div className="case-tabs" style={{ display: 'flex', borderBottom: '1px solid var(--border-dim)', background: 'var(--bg-card)' }}>
                <button
                  type="button"
                  id="tab-evidence-btn"
                  className={`case-tab ${activeTab === 'evidence' ? 'active' : ''}`}
                  onClick={() => setActiveTab('evidence')}
                >
                  <ShieldCheck size={16} /> Digital Evidence ({selectedCase.evidence ? selectedCase.evidence.length : 0})
                </button>
                <button
                  type="button"
                  id="tab-audit-btn"
                  className={`case-tab ${activeTab === 'audit' ? 'active' : ''}`}
                  onClick={() => setActiveTab('audit')}
                >
                  <Clock size={16} /> Chain of Custody &amp; Audit Trail
                </button>
                <button
                  type="button"
                  id="tab-analysis-btn"
                  className={`case-tab ${activeTab === 'analysis' ? 'active' : ''}`}
                  onClick={() => setActiveTab('analysis')}
                >
                  <Layers size={16} /> Findings ({selectedCase.analysis_records ? selectedCase.analysis_records.length : 0})
                </button>
              </div>

              {/* Tab 1: Evidence Items Grid */}
              {activeTab === 'evidence' && (
                <div style={{ padding: '1.5rem' }}>
                  {(!selectedCase.evidence || selectedCase.evidence.length === 0) ? (
                    <div style={{ textAlign: 'center', padding: '3.5rem 1.5rem', background: 'var(--bg-card-hover)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-dim)' }}>
                      <UploadCloud size={44} style={{ color: 'var(--accent-cyan)', opacity: 0.7, margin: '0 auto 0.75rem auto' }} />
                      <h4 style={{ fontSize: '1.1rem', marginBottom: '0.35rem' }}>No Digital Evidence Uploaded</h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto 1.25rem auto' }}>
                        Upload questioned images, fingerprints, signatures, or documents to establish baseline cryptographic hashes and conduct forensic testing.
                      </p>
                      <button
                        type="button"
                        id="upload-evidence-empty-btn"
                        className="btn btn-primary"
                        onClick={handleOpenUploadEvidence}
                      >
                        <UploadCloud size={16} /> Upload First Evidence File
                      </button>
                    </div>
                  ) : (
                    <div className="evidence-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                      {selectedCase.evidence.map((ev) => (
                        <div key={ev.evidence_id} className="evidence-card" id={`evidence-card-${ev.evidence_id}`}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                              <span className="evidence-type-badge">{ev.evidence_type}</span>
                              <span className="badge badge-secondary" style={{ fontSize: '0.7rem' }}>
                                {formatFileSize(ev.file_size)}
                              </span>
                            </div>
                            <span className={`badge ${ev.status === 'Active' ? 'badge-success' : 'badge-secondary'}`}>
                              {ev.status}
                            </span>
                          </div>

                          <h4 className="evidence-card-name" title={ev.evidence_name}>
                            {ev.evidence_name}
                          </h4>
                          <div className="evidence-card-file" title={ev.original_filename}>
                            {ev.original_filename}
                          </div>

                          {/* Cryptographic Hash snippet */}
                          <div className="evidence-hash-box">
                            <span className="evidence-hash-label">SHA-256 Baseline:</span>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <code className="evidence-hash-code" title={ev.sha256_hash}>
                                {ev.sha256_hash.substring(0, 14)}...{ev.sha256_hash.substring(ev.sha256_hash.length - 8)}
                              </code>
                              <button
                                type="button"
                                className="btn-icon-subtle"
                                onClick={() => handleCopyHash(ev.sha256_hash)}
                                title="Copy full SHA-256 hash"
                              >
                                {copiedHash === ev.sha256_hash ? (
                                  <Check size={12} style={{ color: 'var(--risk-low)' }} />
                                ) : (
                                  <Copy size={12} />
                                )}
                              </button>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="evidence-card-actions">
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleInspectEvidence(ev)}
                              style={{ flex: 1 }}
                            >
                              <Eye size={14} /> Inspect &amp; Verify
                            </button>

                            <a
                              href={`/api/evidence/${ev.evidence_id}/download`}
                              className="btn btn-secondary btn-sm btn-icon"
                              download={ev.original_filename}
                              target="_blank"
                              rel="noreferrer"
                              title="Download original file"
                            >
                              <Download size={14} />
                            </a>

                            <button
                              type="button"
                              className="btn btn-secondary btn-sm btn-icon text-danger"
                              onClick={() => handleArchiveEvidence(ev)}
                              title="Archive evidence"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Chain of Custody & Audit Trail */}
              {activeTab === 'audit' && (
                <div style={{ padding: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                      Chain-of-Custody Timeline
                    </h3>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => loadAuditLogs(selectedCase.case_id)}
                      disabled={loadingAuditLogs}
                    >
                      <RefreshCw size={14} className={loadingAuditLogs ? 'spin' : ''} /> Refresh Log
                    </button>
                  </div>

                  {loadingAuditLogs && (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      <div className="loading-spinner" style={{ margin: '0 auto 0.5rem auto' }} />
                      <p>Loading chronological chain of custody...</p>
                    </div>
                  )}

                  {!loadingAuditLogs && auditLogs.length === 0 && (
                    <p style={{ color: 'var(--text-muted)', fontStyle: 'italic', textAlign: 'center', padding: '2rem' }}>
                      No audit events recorded for this case yet.
                    </p>
                  )}

                  {!loadingAuditLogs && auditLogs.length > 0 && (
                    <div className="audit-timeline">
                      {auditLogs.map((log) => {
                        let parsedDetails = {}
                        try {
                          parsedDetails = typeof log.details === 'string' ? JSON.parse(log.details) : log.details || {}
                        } catch {
                          parsedDetails = { raw: log.details }
                        }

                        return (
                          <div key={log.event_id} className="audit-timeline-item">
                            <div className="audit-timeline-marker" />
                            <div className="audit-timeline-content">
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                                <div>
                                  <span className="badge badge-action">{log.action_type}</span>
                                  <span style={{ marginLeft: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>
                                    {log.actor}
                                  </span>
                                </div>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                  {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                                </span>
                              </div>

                              {log.evidence_id && (
                                <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: '0.25rem', fontFamily: 'var(--font-mono)' }}>
                                  Target Evidence: {log.evidence_id}
                                </div>
                              )}

                              {Object.keys(parsedDetails).length > 0 && (
                                <pre className="audit-details-box">
                                  {JSON.stringify(parsedDetails, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Analysis Records */}
              {activeTab === 'analysis' && (
                <div style={{ padding: '1.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>
                    Automated Forensic Analysis Records
                  </h3>

                  {(!selectedCase.analysis_records || selectedCase.analysis_records.length === 0) ? (
                    <div style={{ textAlign: 'center', padding: '3rem 1.5rem', background: 'var(--bg-card-hover)', borderRadius: 'var(--radius-md)' }}>
                      <Layers size={40} style={{ color: 'var(--text-muted)', margin: '0 auto 0.75rem auto', opacity: 0.6 }} />
                      <h4 style={{ fontSize: '1rem', marginBottom: '0.35rem' }}>No Analysis Records Yet</h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto' }}>
                        To run automated forensic analysis, switch to the <strong>Digital Evidence</strong> tab, click <strong>Inspect &amp; Verify</strong> on any evidence item, and select <strong>Run Forensic Analysis</strong>.
                      </p>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {selectedCase.analysis_records.map((rec) => (
                        <div key={rec.record_id} className="analysis-summary-card">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
                                  {rec.record_id}
                                </span>
                                <span className="badge badge-secondary">{rec.module_type}</span>
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
                              </div>
                              <p style={{ margin: '0.4rem 0 0 0', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                                {rec.result_summary}
                              </p>
                            </div>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              {rec.created_at ? new Date(rec.created_at).toLocaleString() : 'N/A'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Modals ───────────────────────────────────────────────────────────── */}
      {/* Create / Edit Case Modal */}
      <CaseModal
        isOpen={isCaseModalOpen}
        mode={caseModalMode}
        initialData={caseModalInitialData}
        onSave={handleSaveCase}
        onCancel={() => setIsCaseModalOpen(false)}
        loading={caseModalLoading}
      />

      {/* Upload Evidence Modal */}
      <EvidenceModal
        isOpen={isEvidenceModalOpen}
        caseId={selectedCase?.case_id || ''}
        onUpload={handleUploadEvidence}
        onCancel={() => setIsEvidenceModalOpen(false)}
        loading={evidenceModalLoading}
      />

      {/* Evidence Detail & Integrity Inspector Modal */}
      <EvidenceDetailModal
        isOpen={isEvidenceDetailModalOpen}
        evidence={selectedEvidenceForDetail}
        onClose={() => setIsEvidenceDetailModalOpen(false)}
        onEvidenceUpdated={async () => {
          if (selectedCaseId) {
            await loadCaseDetails(selectedCaseId)
            await loadStats()
          }
        }}
        onArchive={(ev) => handleArchiveEvidence(ev)}
      />

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={isConfirmModalOpen}
        title={confirmConfig.title}
        message={confirmConfig.message}
        confirmText={confirmConfig.confirmText}
        confirmVariant={confirmConfig.confirmVariant}
        onConfirm={confirmConfig.onConfirm}
        onCancel={() => setIsConfirmModalOpen(false)}
        loading={confirmLoading}
      />

      {/* Forensic Report Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        caseId={selectedCase?.case_id || ''}
        onClose={() => setIsReportModalOpen(false)}
      />
    </main>
  )
}

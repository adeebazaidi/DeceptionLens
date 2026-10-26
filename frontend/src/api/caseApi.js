/**
 * caseApi.js
 * ==========
 * REST API client for DeceptionLens Case & Evidence Management Module.
 */

const API_BASE = '/api'

/**
 * Fetch paginated cases with search and multi-criteria filters.
 */
export async function fetchCases(params = {}) {
  const query = new URLSearchParams()
  if (params.search) query.append('search', params.search)
  if (params.case_type) query.append('case_type', params.case_type)
  if (params.priority) query.append('priority', params.priority)
  if (params.status) query.append('status', params.status)
  if (params.include_archived) query.append('include_archived', 'true')
  if (params.sort_by) query.append('sort_by', params.sort_by)
  if (params.sort_order) query.append('sort_order', params.sort_order)
  if (params.page) query.append('page', params.page)
  if (params.limit) query.append('limit', params.limit)

  const res = await fetch(`${API_BASE}/cases?${query.toString()}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch cases (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Create a new forensic case.
 */
export async function createCase(caseData) {
  const res = await fetch(`${API_BASE}/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(caseData),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to create case (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Retrieve case details, associated evidence, and analysis records.
 */
export async function getCaseDetails(caseId) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to get case details (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Update case details (preserving case ID).
 */
export async function updateCase(caseId, updateData) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateData),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update case (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Update case status with optional notes.
 */
export async function updateCaseStatus(caseId, status, notes = '') {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, notes }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update case status (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Soft-archive a case safely.
 */
export async function archiveCase(caseId) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to archive case (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Generate a comprehensive forensic case report.
 */
export async function getCaseReport(caseId) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/report`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to generate case report (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Upload digital evidence to a specific case.
 */
export async function uploadEvidence(caseId, formData) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/evidence`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Evidence upload failed (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Retrieve evidence items for a case.
 */
export async function getCaseEvidence(caseId) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/evidence`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to get case evidence (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Retrieve complete evidence metadata.
 */
export async function getEvidenceDetails(evidenceId) {
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(evidenceId)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to get evidence details (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Recalculate and verify SHA-256 integrity of evidence on disk.
 */
export async function verifyEvidenceIntegrity(evidenceId) {
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(evidenceId)}/verify-integrity`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Integrity check failed (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Update evidence status (e.g. Active -> Archived).
 */
export async function updateEvidenceStatus(evidenceId, status, reason = '') {
  const query = new URLSearchParams({ status })
  if (reason) query.append('reason', reason)
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(evidenceId)}/status?${query.toString()}`, {
    method: 'PATCH',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update evidence status (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Run automated forensic analysis on stored evidence and link results.
 */
export async function runEvidenceAnalysis(evidenceId) {
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(evidenceId)}/run-analysis`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Forensic analysis run failed (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Retrieve audit logs for a case.
 */
export async function getCaseAuditLogs(caseId) {
  const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/audit-logs`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to get audit logs (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Retrieve audit logs for a specific evidence item.
 */
export async function getEvidenceAuditLogs(evidenceId) {
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(evidenceId)}/audit-logs`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to get evidence audit logs (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Fetch aggregated dashboard statistics.
 */
export async function fetchDashboardStats() {
  const res = await fetch(`${API_BASE}/cases/stats/summary`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch stats (HTTP ${res.status})`)
  }
  return res.json()
}

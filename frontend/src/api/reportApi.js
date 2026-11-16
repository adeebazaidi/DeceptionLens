/**
 * reportApi.js
 * ============
 * REST API client for the DeceptionLens Dashboard & Report Management Module.
 */

const API_BASE = '/api'

async function request(url, options, fallbackMessage) {
  const res = await fetch(url, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `${fallbackMessage} (HTTP ${res.status})`)
  }
  return res.json()
}

/**
 * Fetch the system-wide dashboard overview.
 */
export function fetchDashboardOverview() {
  return request(`${API_BASE}/dashboard/overview`, undefined, 'Failed to load dashboard')
}

/**
 * Generate and save a SHA-256-sealed report for a case.
 */
export function generateReport({ case_id, generated_by, title, notes }) {
  return request(
    `${API_BASE}/reports`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id, generated_by, title: title || null, notes: notes || null }),
    },
    'Failed to generate report'
  )
}

/**
 * List saved reports. status: 'Final' (default) | 'Archived' | 'all'.
 */
export function fetchReports({ search, status, case_id } = {}) {
  const query = new URLSearchParams()
  if (search) query.append('search', search)
  if (status) query.append('status', status)
  if (case_id) query.append('case_id', case_id)
  return request(`${API_BASE}/reports?${query.toString()}`, undefined, 'Failed to load reports')
}

/**
 * Fetch a saved report including its full content.
 */
export function getSavedReport(reportId) {
  return request(`${API_BASE}/reports/${encodeURIComponent(reportId)}`, undefined, 'Failed to load report')
}

/**
 * Re-hash a saved report and compare it with its SHA-256 seal.
 */
export function verifyReport(reportId) {
  return request(
    `${API_BASE}/reports/${encodeURIComponent(reportId)}/verify`,
    { method: 'POST' },
    'Failed to verify report'
  )
}

/**
 * Archive or restore a saved report. status: 'Final' | 'Archived'.
 */
export function updateReportStatus(reportId, status, reason = '') {
  return request(
    `${API_BASE}/reports/${encodeURIComponent(reportId)}/status`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, reason }),
    },
    'Failed to update report status'
  )
}

/**
 * URL that downloads a saved report as JSON (the download is audit-logged).
 */
export function reportDownloadUrl(reportId) {
  return `${API_BASE}/reports/${encodeURIComponent(reportId)}/download`
}

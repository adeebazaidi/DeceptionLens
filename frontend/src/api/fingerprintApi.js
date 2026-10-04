/**
 * fingerprintApi.js
 * =================
 * REST API client for DeceptionLens Fingerprint Verification module.
 */

const API_BASE = '/api/fingerprint'

/**
 * Compare two fingerprint images using minutiae-based matching.
 * @param {File} referenceFile - The baseline reference fingerprint image file.
 * @param {File} questionedFile - The questioned/query fingerprint image file.
 * @param {number} [threshold] - Optional custom similarity threshold (0-100).
 * @returns {Promise<Object>} Parsed JSON verification response.
 */
export async function compareFingerprints(referenceFile, questionedFile, threshold = null) {
  const formData = new FormData()
  formData.append('reference', referenceFile)
  formData.append('questioned', questionedFile)

  if (threshold !== null && threshold !== undefined) {
    formData.append('threshold', threshold.toString())
  }

  let response
  try {
    response = await fetch(`${API_BASE}/compare`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error(
      networkError.message || 'Cannot reach the forensic analysis server. Please ensure the backend is running on port 8000.'
    )
  }

  if (response.status === 502 || response.status === 503 || response.status === 504) {
    throw new Error(
      'Cannot connect to the backend server (HTTP 502). Please ensure the backend server is running on port 8000 (`uvicorn main:app --reload --port 8000`).'
    )
  }

  let data
  try {
    data = await response.json()
  } catch {
    throw new Error(`Unexpected server response format (HTTP ${response.status}).`)
  }

  if (!response.ok) {
    const detail = data?.detail || `Server error (HTTP ${response.status}).`
    if (response.status === 400) {
      throw new Error(`Invalid file upload: ${detail}`)
    }
    if (response.status === 413) {
      throw new Error(`File too large: ${detail}`)
    }
    if (response.status === 422) {
      throw new Error(detail)
    }
    throw new Error(detail)
  }

  return data
}

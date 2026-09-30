/**
 * signatureApi.js
 * ================
 * REST API client for Signature Forgery Detection.
 */

const API_BASE = '/api/signature'

/**
 * Analyze signature file(s).
 * @param {File} queryFile - Suspect signature file.
 * @param {File|null} referenceFile - Optional reference genuine signature file.
 * @returns {Promise<Object>} Parsed JSON response.
 */
export async function analyzeSignature(queryFile, referenceFile = null) {
  const formData = new FormData()
  formData.append('file', queryFile)

  if (referenceFile) {
    formData.append('reference_file', referenceFile)
  }

  let response
  try {
    response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error(
      'Cannot reach the analysis server. Please ensure the backend is running on port 8000.'
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
    throw new Error(`Unexpected server response (HTTP ${response.status}).`)
  }

  if (!response.ok) {
    const detail = data?.detail || `Server error (HTTP ${response.status}).`
    if (response.status === 400) {
      throw new Error(`Invalid signature file: ${detail}`)
    }
    if (response.status === 413) {
      throw new Error(`File too large. ${detail}`)
    }
    throw new Error(detail)
  }

  return data
}

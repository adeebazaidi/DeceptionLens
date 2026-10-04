/**
 * imageApi.js
 * ===========
 * REST API client for DeceptionLens backend.
 */

const API_BASE = '/api/image'

/**
 * Analyze an image file.
 * @param {File} file - The image file to analyze.
 * @returns {Promise<Object>} Parsed JSON response from backend.
 */
export async function analyzeImage(file) {
  const formData = new FormData()
  formData.append('file', file)

  let response
  try {
    response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error(
      networkError.message || 'Cannot reach the analysis server. Please ensure the backend is running on port 8000.'
    )
  }

  if (response.status === 502 || response.status === 503 || response.status === 504) {
    throw new Error(
      'Cannot connect to the backend server (HTTP 502). Please ensure the backend server is running on port 8000 (`uvicorn main:app --reload --port 8000`).'
    )
  }

  // Parse JSON body
  let data
  try {
    data = await response.json()
  } catch {
    throw new Error(`Unexpected server response (HTTP ${response.status}).`)
  }

  if (!response.ok) {
    // Use backend's detail message if available
    const detail = data?.detail || `Server error (HTTP ${response.status}).`
    if (response.status === 400) {
      throw new Error(`Invalid file: ${detail}`)
    }
    if (response.status === 413) {
      throw new Error(`File too large. ${detail}`)
    }
    if (response.status === 422) {
      throw new Error('Please select an image file before analyzing.')
    }
    throw new Error(detail)
  }

  return data
}

import { useState } from 'react'
import { Upload, FileText, CheckCircle2, RefreshCw, Layers, ShieldCheck } from 'lucide-react'

export default function SignatureUploader({ onAnalyze, loading }) {
  const [mode, setMode] = useState('STANDALONE') // 'STANDALONE' | 'COMPARISON'
  const [queryFile, setQueryFile] = useState(null)
  const [queryPreview, setQueryPreview] = useState(null)
  const [refFile, setRefFile] = useState(null)
  const [refPreview, setRefPreview] = useState(null)
  const [dragActiveQuery, setDragActiveQuery] = useState(false)
  const [dragActiveRef, setDragActiveRef] = useState(false)

  const handleQueryChange = (file) => {
    if (!file) return
    setQueryFile(file)
    setQueryPreview(URL.createObjectURL(file))
  }

  const handleRefChange = (file) => {
    if (!file) return
    setRefFile(file)
    setRefPreview(URL.createObjectURL(file))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!queryFile) return
    onAnalyze(queryFile, mode === 'COMPARISON' ? refFile : null)
  }

  return (
    <div className="card uploader-card shadow-lg border-gradient">
      <div className="uploader-header">
        <h2 className="uploader-title">
          <ShieldCheck className="title-icon" size={24} />
          Signature Forgery Detection Engine
        </h2>
        <p className="uploader-desc">
          Screen handwritten signatures for stroke tremor, pen hesitation, and geometric anomalies, or compare against a genuine reference.
        </p>

        {/* Mode Selector */}
        <div className="mode-toggle-bar" role="tablist" aria-label="Analysis Mode">
          <button
            type="button"
            className={`mode-btn ${mode === 'STANDALONE' ? 'active' : ''}`}
            onClick={() => setMode('STANDALONE')}
          >
            <FileText size={16} /> Standalone Screening
          </button>
          <button
            type="button"
            className={`mode-btn ${mode === 'COMPARISON' ? 'active' : ''}`}
            onClick={() => setMode('COMPARISON')}
          >
            <Layers size={16} /> 1-vs-1 Reference Verification
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="uploader-form">
        <div className={`signature-dropzones-grid ${mode === 'COMPARISON' ? 'dual-grid' : 'single-grid'}`}>
          {/* Query Signature Upload Zone */}
          <div className="dropzone-container">
            <label className="dropzone-label">
              <span>Query Signature (Suspect)</span>
              <span className="required-badge">Required</span>
            </label>
            <div
              className={`drop-area ${dragActiveQuery ? 'drag-active' : ''} ${queryFile ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragActiveQuery(true) }}
              onDragLeave={() => setDragActiveQuery(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragActiveQuery(false)
                if (e.dataTransfer.files?.[0]) handleQueryChange(e.dataTransfer.files[0])
              }}
            >
              {queryPreview ? (
                <div className="sig-preview-box">
                  <img src={queryPreview} alt="Query Signature Preview" className="sig-preview-img" />
                  <div className="preview-meta">
                    <span className="file-name">{queryFile.name}</span>
                    <button
                      type="button"
                      className="btn-clear-sig"
                      onClick={() => { setQueryFile(null); setQueryPreview(null) }}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ) : (
                <label htmlFor="query-file-input" className="dropzone-placeholder">
                  <Upload size={32} className="upload-icon" />
                  <span className="upload-prompt">Drop suspect signature here or click to browse</span>
                  <span className="upload-hint">Supports PNG, JPG, WEBP (Max 10 MB)</span>
                  <input
                    id="query-file-input"
                    type="file"
                    accept="image/png, image/jpeg, image/webp"
                    className="file-input-hidden"
                    onChange={(e) => handleQueryChange(e.target.files?.[0])}
                  />
                </label>
              )}
            </div>
          </div>

          {/* Reference Signature Upload Zone (Comparison Mode) */}
          {mode === 'COMPARISON' && (
            <div className="dropzone-container">
              <label className="dropzone-label">
                <span>Reference Signature (Genuine)</span>
                <span className="optional-badge">1-vs-1 Target</span>
              </label>
              <div
                className={`drop-area ${dragActiveRef ? 'drag-active' : ''} ${refFile ? 'has-file' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragActiveRef(true) }}
                onDragLeave={() => setDragActiveRef(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setDragActiveRef(false)
                  if (e.dataTransfer.files?.[0]) handleRefChange(e.dataTransfer.files[0])
                }}
              >
                {refPreview ? (
                  <div className="sig-preview-box">
                    <img src={refPreview} alt="Reference Signature Preview" className="sig-preview-img" />
                    <div className="preview-meta">
                      <span className="file-name">{refFile.name}</span>
                      <button
                        type="button"
                        className="btn-clear-sig"
                        onClick={() => { setRefFile(null); setRefPreview(null) }}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ) : (
                  <label htmlFor="ref-file-input" className="dropzone-placeholder">
                    <Upload size={32} className="upload-icon" />
                    <span className="upload-prompt">Drop reference signature here or click to browse</span>
                    <span className="upload-hint">Supports PNG, JPG, WEBP (Max 10 MB)</span>
                    <input
                      id="ref-file-input"
                      type="file"
                      accept="image/png, image/jpeg, image/webp"
                      className="file-input-hidden"
                      onChange={(e) => handleRefChange(e.target.files?.[0])}
                    />
                  </label>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="uploader-actions">
          <button
            type="submit"
            className="btn btn-primary btn-analyze-sig"
            disabled={!queryFile || (mode === 'COMPARISON' && !refFile) || loading}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className="spinner" /> Analyzing Signature Forensic Indicators...
              </>
            ) : (
              <>
                <CheckCircle2 size={18} /> Run Signature Forgery Analysis
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

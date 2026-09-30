import { useState } from 'react'
import {
  Fingerprint,
  GitCompare,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Layers,
  Sparkles,
  Info,
  Clock,
  Target,
  ArrowRight,
} from 'lucide-react'
import FingerprintUploader from '../components/FingerprintUploader.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import { compareFingerprints } from '../api/fingerprintApi.js'

export default function FingerprintComparison() {
  const [refFile, setRefFile] = useState(null)
  const [questFile, setQuestFile] = useState(null)
  const [isComparing, setIsComparing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('comparison') // 'comparison' | 'reference' | 'questioned'

  function handleRefSelect(file) {
    setRefFile(file)
    setResult(null)
    setError('')
  }

  function handleQuestSelect(file) {
    setQuestFile(file)
    setResult(null)
    setError('')
  }

  async function handleCompare() {
    if (!refFile || !questFile) return

    setIsComparing(true)
    setResult(null)
    setError('')

    try {
      const data = await compareFingerprints(refFile, questFile)
      setResult(data)
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during fingerprint comparison.')
    } finally {
      setIsComparing(false)
    }
  }

  const isReady = refFile && questFile && !isComparing
  const hasResult = result && result.success
  const isMatch = result?.result === 'Likely Match'

  return (
    <main className="analysis-page" id="fingerprint-page">
      {/* Header */}
      <div className="page-header">
        <div className="hero-badge" style={{ marginBottom: '0.75rem' }}>
          <span className="hero-badge-dot" aria-hidden="true" />
          Biometric Verification Module
        </div>
        <h1 className="page-title">Fingerprint Comparison</h1>
        <p className="page-subtitle">
          Compare two fingerprint samples using image preprocessing and minutiae-based feature matching.
        </p>
      </div>

      {/* Upload Section */}
      <div className="card section-spacer">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <GitCompare size={20} style={{ color: 'var(--accent-cyan)' }} />
              Impression Pair Input
            </div>
            <div className="card-subtitle">
              Provide a known reference impression and a questioned forensic query.
            </div>
          </div>
        </div>

        <div className="fingerprint-upload-grid">
          <FingerprintUploader
            title="Reference Fingerprint"
            subtitle="Known exemplar impression"
            file={refFile}
            onFileSelect={handleRefSelect}
            disabled={isComparing}
            badgeColor="cyan"
          />

          <FingerprintUploader
            title="Questioned Fingerprint"
            subtitle="Latent or inquiry impression"
            file={questFile}
            onFileSelect={handleQuestSelect}
            disabled={isComparing}
            badgeColor="teal"
          />
        </div>

        {/* Compare Action Bar */}
        <div className="fingerprint-action-bar">
          <button
            id="compare-fingerprints-btn"
            className="btn btn-primary btn-compare-fingerprint"
            type="button"
            disabled={!isReady}
            onClick={handleCompare}
          >
            {isComparing ? (
              <>
                <span className="loading-spinner-sm" aria-hidden="true" />
                Processing Minutiae...
              </>
            ) : (
              <>
                <GitCompare size={18} />
                Compare Fingerprints
              </>
            )}
          </button>
          {!isReady && !isComparing && (
            <span className="action-hint" style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              {!refFile && !questFile
                ? 'Upload both fingerprint impressions to initiate comparison'
                : !refFile
                ? 'Upload Reference fingerprint to continue'
                : 'Upload Questioned fingerprint to continue'}
            </span>
          )}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="section-spacer">
          <ErrorMessage message={error} onDismiss={() => setError('')} />
        </div>
      )}

      {/* Loading state */}
      {isComparing && (
        <div className="card section-spacer">
          <Loading />
          <div style={{ textAlign: 'center', marginTop: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Extracting ridge flow, skeletonizing ridges, and computing minutiae alignment...
          </div>
        </div>
      )}

      {/* Results Section */}
      {hasResult && (
        <>
          {/* Main Verdict Card */}
          <div className="card section-spacer fingerprint-verdict-card">
            <div className="verdict-banner-content">
              <div className="verdict-status-box">
                <div
                  className={`verdict-icon-bubble ${isMatch ? 'match' : 'non-match'}`}
                  aria-hidden="true"
                >
                  {isMatch ? <CheckCircle2 size={36} /> : <XCircle size={36} />}
                </div>
                <div>
                  <div className="verdict-tag">{isMatch ? 'VERIFICATION POSITIVE' : 'VERIFICATION NEGATIVE'}</div>
                  <div className={`verdict-title ${isMatch ? 'text-match' : 'text-non-match'}`}>
                    {result.result}
                  </div>
                  <div className="verdict-desc">
                    {isMatch
                      ? 'Geometric minutiae alignment and topological pairing exceed verification threshold.'
                      : 'Distinguishable minutiae correspondences are insufficient to support a verified match.'}
                  </div>
                </div>
              </div>

              {/* Similarity Score Radial / Gauge */}
              <div className="similarity-gauge-box">
                <div className="similarity-score-value">
                  {result.similarity_score.toFixed(1)}<span className="similarity-pct">%</span>
                </div>
                <div className="similarity-score-label">Similarity Score</div>
                <div className="similarity-progress-track">
                  <div
                    className={`similarity-progress-fill ${isMatch ? 'fill-match' : 'fill-non-match'}`}
                    style={{ width: `${Math.min(100, Math.max(0, result.similarity_score))}%` }}
                  />
                  <div
                    className="threshold-marker"
                    style={{ left: `${result.threshold}%` }}
                    title={`Threshold: ${result.threshold}%`}
                  />
                </div>
                <div className="threshold-legend">
                  <span>0%</span>
                  <span className="threshold-label">Threshold: {result.threshold}%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Overview Grid */}
          <div className="overview-grid section-spacer">
            <div className="overview-card">
              <div className="overview-label">Reference Minutiae</div>
              <div className="overview-value cyan">
                {result.reference_minutiae}
              </div>
              <div className="overview-subtext" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {result.details?.reference_endings ?? '—'} Endings · {result.details?.reference_bifurcations ?? '—'} Bifurcations
              </div>
            </div>

            <div className="overview-card">
              <div className="overview-label">Questioned Minutiae</div>
              <div className="overview-value teal">
                {result.questioned_minutiae}
              </div>
              <div className="overview-subtext" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {result.details?.questioned_endings ?? '—'} Endings · {result.details?.questioned_bifurcations ?? '—'} Bifurcations
              </div>
            </div>

            <div className="overview-card">
              <div className="overview-label">Matched Minutiae</div>
              <div className={`overview-value ${isMatch ? 'green' : 'amber'}`}>
                {result.matched_minutiae}
              </div>
              <div className="overview-subtext" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Pairing Tolerance: ±18px, ±37°
              </div>
            </div>

            <div className="overview-card">
              <div className="overview-label">Processing Time</div>
              <div className="overview-value" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock size={18} style={{ color: 'var(--text-muted)' }} />
                {result.processing_time}s
              </div>
              <div className="overview-subtext" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Deterministic crossing-number pipeline
              </div>
            </div>
          </div>

          {/* Visual Analysis Section */}
          <div className="card section-spacer">
            <div className="visual-analysis-header">
              <div>
                <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Layers size={20} style={{ color: 'var(--accent-cyan)' }} />
                  Forensic Visual Analysis
                </div>
                <div className="card-subtitle">
                  Inspect detected minutiae topology and spatial correspondence vectors.
                </div>
              </div>

              {/* View Switcher Tabs */}
              <div className="view-tabs" role="tablist">
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === 'comparison'}
                  className={`view-tab-btn ${activeTab === 'comparison' ? 'active' : ''}`}
                  onClick={() => setActiveTab('comparison')}
                >
                  <GitCompare size={16} /> Comparison Map
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === 'reference'}
                  className={`view-tab-btn ${activeTab === 'reference' ? 'active' : ''}`}
                  onClick={() => setActiveTab('reference')}
                >
                  Reference Stages
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === 'questioned'}
                  className={`view-tab-btn ${activeTab === 'questioned' ? 'active' : ''}`}
                  onClick={() => setActiveTab('questioned')}
                >
                  Questioned Stages
                </button>
              </div>
            </div>

            {/* Minutiae Legend */}
            <div className="minutiae-legend-bar">
              <span className="legend-title">Legend:</span>
              <span className="legend-item">
                <span className="legend-dot dot-ending" />
                Ridge Ending (CN=1)
              </span>
              <span className="legend-item">
                <span className="legend-dot dot-bifurcation" />
                Bifurcation (CN=3)
              </span>
              <span className="legend-item">
                <span className="legend-dot dot-match" />
                Matched Correspondence
              </span>
            </div>

            {/* Tab 1: Comparison Map */}
            {activeTab === 'comparison' && (
              <div className="comparison-viz-container">
                {result.visualizations?.comparison ? (
                  <div className="img-frame">
                    <img
                      src={result.visualizations.comparison}
                      alt="Fingerprint minutiae comparison map"
                      className="comparison-full-img"
                    />
                  </div>
                ) : (
                  <div className="placeholder-viz">Comparison visualization not available.</div>
                )}
                {result.details?.alignment && (
                  <div className="alignment-details-badge">
                    <strong>Optimal Rigid Alignment:</strong> Rotation: {result.details.alignment.rotation_degrees}° · Translation: (Δx: {result.details.alignment.translation_x}px, Δy: {result.details.alignment.translation_y}px)
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Reference Stages */}
            {activeTab === 'reference' && (
              <div className="pipeline-stages-grid">
                <div className="stage-card">
                  <div className="stage-label">Ridge Enhancement (CLAHE + Top-Hat)</div>
                  <div className="stage-img-frame">
                    <img
                      src={result.visualizations?.reference_enhanced}
                      alt="Reference Enhanced"
                      className="stage-img"
                    />
                  </div>
                </div>

                <div className="stage-card">
                  <div className="stage-label">1-Pixel Ridge Skeleton</div>
                  <div className="stage-img-frame">
                    <img
                      src={result.visualizations?.reference_skeleton}
                      alt="Reference Skeleton"
                      className="stage-img"
                    />
                  </div>
                </div>

                <div className="stage-card">
                  <div className="stage-label">Detected Minutiae Overlay</div>
                  <div className="stage-img-frame">
                    <img
                      src={result.visualizations?.reference_minutiae}
                      alt="Reference Minutiae"
                      className="stage-img"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Questioned Stages */}
            {activeTab === 'questioned' && (
              <div className="pipeline-stages-grid">
                <div className="stage-card">
                  <div className="stage-label">Ridge Enhancement (CLAHE + Top-Hat)</div>
                  <div className="stage-img-frame">
                    <img
                      src={result.visualizations?.questioned_enhanced}
                      alt="Questioned Enhanced"
                      className="stage-img"
                    />
                  </div>
                </div>

                <div className="stage-card">
                  <div className="stage-label">1-Pixel Ridge Skeleton</div>
                  <div className="stage-img-frame">
                    <img
                      src={result.visualizations?.questioned_skeleton}
                      alt="Questioned Skeleton"
                      className="stage-img"
                    />
                  </div>
                </div>

                <div className="stage-card">
                  <div className="stage-label">Detected Minutiae Overlay</div>
                  <div className="stage-img-frame">
                    <img
                      src={result.visualizations?.questioned_minutiae}
                      alt="Questioned Minutiae"
                      className="stage-img"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Forensic Disclaimer */}
          <div className="hero-disclaimer" role="note" style={{ marginTop: '1.5rem' }}>
            <strong>Forensic Biometric Disclaimer</strong><br />
            DeceptionLens fingerprint verification is designed as an investigative decision-support tool.
            Minutiae extraction and geometric matching provide mathematical similarity indices and
            do not constitute conclusive legal proof of individual identity.
          </div>
        </>
      )}
    </main>
  )
}

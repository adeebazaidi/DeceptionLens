import { useState } from 'react'
import { AlertTriangle, CheckCircle, ShieldAlert, Layers, Activity, Info, Eye, Percent, BarChart3, HelpCircle, AlertOctagon } from 'lucide-react'

// Helper SVG Ring Gauge Component for Professional UI
function RingGauge({ percentage, label, color = 'cyan', size = 96 }) {
  const strokeWidth = 8
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const validPct = Math.min(Math.max(parseFloat(percentage) || 0, 0), 100)
  const strokeDashoffset = circumference - (validPct / 100) * circumference

  return (
    <div className="ring-gauge-box">
      <div className="ring-svg-wrapper" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="ring-svg">
          <circle
            className="ring-bg"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={strokeWidth}
          />
          <circle
            className={`ring-progress ring-${color}`}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </svg>
        <span className="ring-val-text">{validPct.toFixed(1)}%</span>
      </div>
      <span className="ring-label-text">{label}</span>
    </div>
  )
}

export default function SignaturePanel({ data }) {
  const [activeTab, setActiveTab] = useState('TREMOR') // 'TREMOR' | 'BINARY' | 'SKELETON' | 'OVERLAY'
  const [showFormulaInfo, setShowFormulaInfo] = useState(false)

  if (!data?.analysis) return null

  const { mode, query_features, reference_features, standalone_assessment, comparison, visual_urls } = data.analysis

  const isComparison = mode === 'COMPARISON' && comparison
  const riskLevel = isComparison ? comparison.risk_level : standalone_assessment.risk_level
  const reasons = isComparison ? comparison.reasons : standalone_assessment.reasons

  // Percentage calculations
  const matchPct = isComparison ? comparison.match_percentage : parseFloat((100 - (standalone_assessment.forgery_risk_percentage ?? 25.0)).toFixed(1))
  const riskPct = isComparison
    ? parseFloat(comparison.forgery_risk_percentage ?? (100 - comparison.match_percentage).toFixed(1))
    : parseFloat(standalone_assessment.forgery_risk_percentage ?? 25.0)

  const ssimPct = isComparison ? (comparison.ssim * 100).toFixed(1) : 0
  const profileSimPct = isComparison ? (comparison.profile_similarity * 100).toFixed(1) : 0
  const centroidShiftPct = isComparison ? (comparison.centroid_shift * 100).toFixed(1) : 0
  const centroidAlignPct = isComparison ? Math.max(0, 100 - comparison.centroid_shift * 300).toFixed(1) : 0
  const tremorPct = (query_features.tremor_score * 100).toFixed(1)
  const fillDensityPct = (query_features.fill_factor * 100).toFixed(1)

  const getRiskBadge = (level) => {
    switch (level) {
      case 'LOW':
        return (
          <span className="status-badge risk-low">
            <CheckCircle size={16} /> Genuine Signature (Low Risk • {riskPct}% Risk)
          </span>
        )
      case 'MEDIUM':
        return (
          <span className="status-badge risk-medium">
            <AlertTriangle size={16} /> Suspicious (Medium Risk • {riskPct}% Risk)
          </span>
        )
      case 'HIGH':
        return (
          <span className="status-badge risk-high">
            <ShieldAlert size={16} /> Forgery Likely (High Risk • {riskPct}% Risk)
          </span>
        )
      default:
        return null
    }
  }

  const getVerdictLabel = () => {
    if (isComparison) return comparison.verdict
    if (riskLevel === 'HIGH') return 'FORGERY_LIKELY'
    if (riskLevel === 'MEDIUM') return 'SUSPICIOUS'
    return 'GENUINE_MATCH'
  }

  return (
    <div className="signature-panel-container">
      {/* Overview Banner */}
      <div className="card shadow-lg signature-overview-card border-gradient">
        <div className="overview-header">
          <div className="overview-title-group">
            <h3 className="panel-title">Forensic Signature Verification Summary</h3>
            <span className="mode-badge">{isComparison ? '1-vs-1 Reference Comparison' : 'Standalone Screening'}</span>
          </div>
          <div className="badge-group">{getRiskBadge(riskLevel)}</div>
        </div>

        {/* PROFESSIONAL HERO DISPLAY WITH SVG GAUGES */}
        <div className="match-score-hero">
          <div className="ring-gauges-container">
            <RingGauge
              percentage={matchPct}
              label={isComparison ? 'Structural Match' : 'Fluidity Score'}
              color="magenta"
            />
            <RingGauge
              percentage={riskPct}
              label="Forgery Risk"
              color={riskLevel === 'HIGH' ? 'rose' : riskLevel === 'MEDIUM' ? 'amber' : 'green'}
            />
          </div>

          <div className="verdict-details-pro">
            <div className="verdict-badge-row">
              <span className="verdict-tag-label">FORENSIC VERDICT:</span>
              <span className={`verdict-pill-badge verdict-${getVerdictLabel().toLowerCase()}`}>
                <span className="pulse-dot"></span> {getVerdictLabel().replace('_', ' ')}
              </span>
            </div>

            <div className="hero-metrics-chips">
              {isComparison ? (
                <>
                  <div className="metric-chip">
                    <span className="chip-key">SSIM Match</span>
                    <span className="chip-val">{ssimPct}%</span>
                  </div>
                  <div className="metric-chip">
                    <span className="chip-key">Centroid Shift</span>
                    <span className="chip-val">{centroidShiftPct}%</span>
                  </div>
                  <div className="metric-chip">
                    <span className="chip-key">Profile Correlation</span>
                    <span className="chip-val">{profileSimPct}%</span>
                  </div>
                  <div className="metric-chip chip-highlight">
                    <span className="chip-key">Forgery Risk</span>
                    <span className="chip-val">{riskPct}%</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="metric-chip">
                    <span className="chip-key">Hesitation Tremor</span>
                    <span className="chip-val">{tremorPct}%</span>
                  </div>
                  <div className="metric-chip">
                    <span className="chip-key">Ink Fill Density</span>
                    <span className="chip-val">{fillDensityPct}%</span>
                  </div>
                  <div className="metric-chip">
                    <span className="chip-key">Aspect Ratio</span>
                    <span className="chip-val">{query_features.aspect_ratio}</span>
                  </div>
                  <div className="metric-chip chip-highlight">
                    <span className="chip-key">Forgery Risk</span>
                    <span className="chip-val">{riskPct}%</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Diagnostic Reasons */}
        <div className="reasons-box">
          <h4 className="box-sub-title"><Info size={16} /> Key Forensic Observations</h4>
          <ul className="reasons-list">
            {reasons.map((reason, idx) => (
              <li key={idx} className="reason-item">{reason}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* DETAILED FORENSIC PERCENTAGE BREAKDOWN GRID */}
      <div className="card shadow-lg percentage-breakdown-card">
        <div className="breakdown-header">
          <h3 className="panel-title">
            <Percent size={20} className="title-icon-cyan" /> Detailed Forensic Weight &amp; Risk Percentage Breakdown
          </h3>
          <button
            className="btn-formula-toggle"
            onClick={() => setShowFormulaInfo(!showFormulaInfo)}
            title="View mathematical weights formula"
          >
            <HelpCircle size={16} /> {showFormulaInfo ? 'Hide Formula' : 'View Formula'}
          </button>
        </div>

        {showFormulaInfo && (
          <div className="formula-info-box">
            <h4 className="formula-title"><BarChart3 size={16} /> Weighted Composite Match &amp; Risk Formula</h4>
            {isComparison ? (
              <>
                <div className="formula-code">
                  <code>
                    Match Score = (40% × SSIM) + (30% × Profile Sim) + (15% × Centroid Alignment) + (15% × Aspect Ratio Alignment)
                    <br />
                    Forgery Risk Percentage = 100% - Match Score = {riskPct}%
                  </code>
                </div>
                <ul className="formula-bullets">
                  <li><strong>Structural Match Score ({matchPct}%):</strong> Weighted structural and projection alignment between signatures.</li>
                  <li><strong>Forgery Risk Percentage ({riskPct}%):</strong> Mathematical complement reflecting total forgery threat level.</li>
                  <li><strong>SSIM (40% Weight):</strong> Fine pixel-level stroke curvature overlap ({ssimPct}%).</li>
                  <li><strong>Profile Sim (30% Weight):</strong> Cosine similarity of horizontal &amp; vertical ink density profiles ({profileSimPct}%).</li>
                  <li><strong>Centroid Alignment (15% Weight):</strong> Center-of-mass spatial displacement penalty ({centroidShiftPct}% shift).</li>
                </ul>
              </>
            ) : (
              <>
                <div className="formula-code">
                  <code>
                    Standalone Forgery Risk = (70% × Stroke Tremor Jitter Score) + (30% × Density/Aspect Anomaly Penalty) = {riskPct}%
                  </code>
                </div>
                <ul className="formula-bullets">
                  <li><strong>Stroke Tremor Index ({tremorPct}%):</strong> Edge gradient micro-vibrations along skeleton contour lines.</li>
                  <li><strong>Ink Fill Density ({fillDensityPct}%):</strong> Ratio of signature ink pixels to overall bounding box area.</li>
                  <li><strong>Aspect Ratio ({query_features.aspect_ratio}):</strong> Structural width-to-height ratio of pen strokes.</li>
                </ul>
              </>
            )}
          </div>
        )}

        <div className="pct-grid">
          {/* Forgery Risk Percentage Card */}
          <div className="pct-card risk-highlight-card">
            <div className="pct-card-top">
              <span className="pct-label"><AlertOctagon size={14} /> Forgery Risk Level</span>
              <span className="pct-weight">Threat Index</span>
            </div>
            <div className="pct-value-row">
              <span className={`pct-value ${riskLevel === 'HIGH' ? 'rose' : riskLevel === 'MEDIUM' ? 'amber' : 'green'}`}>
                {riskPct}%
              </span>
              <span className="pct-status-tag">{riskLevel} Risk</span>
            </div>
            <div className="pct-bar-container">
              <div className={`pct-bar-fill ${riskLevel === 'HIGH' ? 'rose-fill' : riskLevel === 'MEDIUM' ? 'amber-fill' : 'green-fill'}`} style={{ width: `${Math.min(riskPct, 100)}%` }}></div>
            </div>
            <p className="pct-desc">Overall probability of signature manipulation / forgery.</p>
          </div>

          {/* Stroke Tremor Card */}
          <div className="pct-card">
            <div className="pct-card-top">
              <span className="pct-label">Stroke Hesitation Jitter</span>
              <span className="pct-weight">Tremor Score</span>
            </div>
            <div className="pct-value-row">
              <span className={`pct-value ${tremorPct > 45 ? 'rose' : 'green'}`}>{tremorPct}%</span>
              <span className="pct-status-tag">{tremorPct > 45 ? 'High Tremor Jitter' : 'Fluid Stroke'}</span>
            </div>
            <div className="pct-bar-container">
              <div className={`pct-bar-fill ${tremorPct > 45 ? 'rose-fill' : 'green-fill'}`} style={{ width: `${Math.min(tremorPct, 100)}%` }}></div>
            </div>
            <p className="pct-desc">Edge curvature micro-vibration &amp; pen hesitation index.</p>
          </div>

          {/* Ink Fill Density Card */}
          <div className="pct-card">
            <div className="pct-card-top">
              <span className="pct-label">Ink Fill Density</span>
              <span className="pct-weight">Ink Ratio</span>
            </div>
            <div className="pct-value-row">
              <span className="pct-value teal">{fillDensityPct}%</span>
              <span className="pct-status-tag">{fillDensityPct < 5 || fillDensityPct > 45 ? 'Anomalous' : 'Normal'}</span>
            </div>
            <div className="pct-bar-container">
              <div className="pct-bar-fill teal-fill" style={{ width: `${Math.min(fillDensityPct * 2, 100)}%` }}></div>
            </div>
            <p className="pct-desc">Percentage of canvas area covered by signature ink strokes.</p>
          </div>

          {/* Signature Fluidity Score Card */}
          <div className="pct-card">
            <div className="pct-card-top">
              <span className="pct-label">Signature Fluidity Score</span>
              <span className="pct-weight">Authenticity</span>
            </div>
            <div className="pct-value-row">
              <span className="pct-value cyan">{matchPct}%</span>
              <span className="pct-status-tag">{matchPct >= 75 ? 'Smooth' : matchPct >= 50 ? 'Moderate' : 'Shaky'}</span>
            </div>
            <div className="pct-bar-container">
              <div className="pct-bar-fill cyan-fill" style={{ width: `${Math.min(matchPct, 100)}%` }}></div>
            </div>
            <p className="pct-desc">Natural muscle-memory stroke speed &amp; continuity score.</p>
          </div>

          {/* If Comparison mode, show SSIM & Centroid Shift as well */}
          {isComparison && (
            <>
              <div className="pct-card">
                <div className="pct-card-top">
                  <span className="pct-label">Structural Similarity (SSIM)</span>
                  <span className="pct-weight">40% Weight</span>
                </div>
                <div className="pct-value-row">
                  <span className="pct-value cyan">{ssimPct}%</span>
                  <span className="pct-status-tag">{ssimPct >= 75 ? 'Strong' : ssimPct >= 50 ? 'Moderate' : 'Weak'}</span>
                </div>
                <div className="pct-bar-container">
                  <div className="pct-bar-fill cyan-fill" style={{ width: `${Math.min(ssimPct, 100)}%` }}></div>
                </div>
                <p className="pct-desc">Pixel-level stroke trajectory &amp; curvature alignment score.</p>
              </div>

              <div className="pct-card">
                <div className="pct-card-top">
                  <span className="pct-label">Centroid Shift Distance</span>
                  <span className="pct-weight">15% Weight</span>
                </div>
                <div className="pct-value-row">
                  <span className="pct-value amber">{centroidShiftPct}%</span>
                  <span className="pct-status-tag">Shift ({centroidAlignPct}% Match)</span>
                </div>
                <div className="pct-bar-container">
                  <div className="pct-bar-fill amber-fill" style={{ width: `${Math.min(centroidAlignPct, 100)}%` }}></div>
                </div>
                <p className="pct-desc">Center-of-gravity displacement relative to canvas bounds.</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Visual Analysis Heatmaps */}
      <div className="card shadow-lg signature-visuals-card">
        <div className="visuals-header">
          <h3 className="panel-title"><Eye size={20} /> Visual Forensic Layers</h3>
          <div className="heatmap-tabs" role="tablist">
            <button
              className={`tab-btn ${activeTab === 'TREMOR' ? 'active' : ''}`}
              onClick={() => setActiveTab('TREMOR')}
            >
              <Activity size={15} /> Stroke Tremor Heatmap
            </button>
            <button
              className={`tab-btn ${activeTab === 'BINARY' ? 'active' : ''}`}
              onClick={() => setActiveTab('BINARY')}
            >
              Binarized Ink
            </button>
            <button
              className={`tab-btn ${activeTab === 'SKELETON' ? 'active' : ''}`}
              onClick={() => setActiveTab('SKELETON')}
            >
              Skeleton Topology
            </button>
            {isComparison && visual_urls.comparison_overlay_url && (
              <button
                className={`tab-btn ${activeTab === 'OVERLAY' ? 'active' : ''}`}
                onClick={() => setActiveTab('OVERLAY')}
              >
                <Layers size={15} /> Reference Overlay
              </button>
            )}
          </div>
        </div>

        <div className="heatmap-display-area">
          {activeTab === 'TREMOR' && (
            <div className="heatmap-view">
              <div className="img-wrapper">
                <img src={visual_urls.tremor_url} alt="Stroke Tremor Heatmap" className="heatmap-img" />
              </div>
              <div className="heatmap-legend">
                <span className="legend-item"><span className="legend-color smooth"></span> Smooth Fluid Stroke (Normal)</span>
                <span className="legend-item"><span className="legend-color shaky"></span> Pen Hesitation Jitter (High Tremor)</span>
              </div>
            </div>
          )}

          {activeTab === 'BINARY' && (
            <div className="heatmap-view">
              <div className="img-wrapper">
                <img src={visual_urls.binary_url} alt="Binarized Ink Mask" className="heatmap-img" />
              </div>
              <p className="image-caption">Otsu-binarized and normalized signature ink extraction.</p>
            </div>
          )}

          {activeTab === 'SKELETON' && (
            <div className="heatmap-view">
              <div className="img-wrapper">
                <img src={visual_urls.skeleton_url} alt="Skeleton Topology" className="heatmap-img" />
              </div>
              <p className="image-caption">1-pixel wide morphological skeleton for stroke trajectory analysis.</p>
            </div>
          )}

          {activeTab === 'OVERLAY' && isComparison && (
            <div className="heatmap-view">
              <div className="img-wrapper">
                <img src={visual_urls.comparison_overlay_url} alt="Reference Overlay Heatmap" className="heatmap-img" />
              </div>
              <div className="heatmap-legend">
                <span className="legend-item"><span className="legend-color match-green"></span> Green: Matching Strokes</span>
                <span className="legend-item"><span className="legend-color extra-red"></span> Red: Extra Strokes (Query)</span>
                <span className="legend-item"><span className="legend-color missing-blue"></span> Blue: Missing Strokes (Reference)</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Forensic Metrics Breakdown Table */}
      <div className="card shadow-lg signature-metrics-card">
        <h3 className="panel-title">Extracted Signature Metrics</h3>
        <div className="table-responsive">
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Forensic Feature</th>
                <th>Query Signature</th>
                {isComparison && <th>Reference Signature</th>}
                {isComparison && <th>Delta / Deviation</th>}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Overall Forgery Risk Level</td>
                <td>
                  <span className={`metric-tag ${riskLevel === 'HIGH' ? 'tag-warn' : riskLevel === 'MEDIUM' ? 'tag-warn' : 'tag-good'}`}>
                    {riskPct}% Risk ({riskLevel})
                  </span>
                </td>
                {isComparison && <td>—</td>}
                {isComparison && <td>{riskPct}% Forgery Risk</td>}
              </tr>
              <tr>
                <td>Stroke Tremor Index</td>
                <td>
                  <span className={`metric-tag ${query_features.tremor_score > 0.45 ? 'tag-warn' : 'tag-good'}`}>
                    {query_features.tremor_score} ({tremorPct}%)
                  </span>
                </td>
                {isComparison && (
                  <td>
                    <span className="metric-tag tag-good">{reference_features.tremor_score}</span>
                  </td>
                )}
                {isComparison && <td>{Math.abs(query_features.tremor_score - reference_features.tremor_score).toFixed(4)}</td>}
              </tr>
              <tr>
                <td>Aspect Ratio (W/H)</td>
                <td>{query_features.aspect_ratio}</td>
                {isComparison && <td>{reference_features.aspect_ratio}</td>}
                {isComparison && <td>{comparison.aspect_ratio_diff}</td>}
              </tr>
              <tr>
                <td>Ink Fill Density Ratio</td>
                <td>{fillDensityPct}%</td>
                {isComparison && <td>{(reference_features.fill_factor * 100).toFixed(2)}%</td>}
                {isComparison && <td>{(comparison.density_diff * 100).toFixed(2)}%</td>}
              </tr>
              <tr>
                <td>Center of Mass (X, Y)</td>
                <td>({query_features.centroid[0]}, {query_features.centroid[1]})</td>
                {isComparison && <td>({reference_features.centroid[0]}, {reference_features.centroid[1]})</td>}
                {isComparison && <td>{centroidShiftPct}% shift</td>}
              </tr>
              <tr>
                <td>Connected Pen Strokes</td>
                <td>{query_features.connected_components}</td>
                {isComparison && <td>{reference_features.connected_components}</td>}
                {isComparison && <td>{Math.abs(query_features.connected_components - reference_features.connected_components)}</td>}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

import { ShieldCheck, AlertTriangle, ShieldAlert, Info } from 'lucide-react'

export default function ResultCard({ result, mlPrediction }) {
  if (!result) return null

  const { risk_level, reason } = result
  const riskClass = risk_level?.toLowerCase() || 'low'

  const RiskIcon = { 
    low: ShieldCheck, 
    medium: AlertTriangle, 
    high: ShieldAlert 
  }[riskClass] || Info

  const mlAvailable = mlPrediction?.available === true

  return (
    <div id="result-card" className={`result-card ${riskClass}`} role="region" aria-label="Preliminary analysis result">
      <div className="result-header">
        <div>
          <div className="result-label">Preliminary Analysis</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div className={`risk-badge ${riskClass}`}>
              <span aria-hidden="true" style={{ display: 'flex' }}><RiskIcon size={16} /></span>
              {risk_level}
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Risk Level
            </span>
          </div>
        </div>
      </div>

      {reason && reason.length > 0 && (
        <div className="result-indicators">
          <h4>Potential Indicators</h4>
          <div className="indicator-list">
            {reason.map((r, i) => (
              <div key={i} className="indicator-item">
                <div className="indicator-dot" aria-hidden="true" />
                {r}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="result-disclaimer">
        This is a <strong>preliminary screening result</strong> for research and educational purposes.
        It does not establish that the image has been forged or manipulated. Entropy variation, ELA,
        noise, and texture outputs are analytical indicators only.
      </div>

      {/* ML Prediction Section */}
      <div className="ml-prediction-section">
        <div className="ml-title">ML Prediction</div>
        {!mlAvailable ? (
          <div className="ml-not-available">
            {mlPrediction?.message || 'ML model has not been trained yet.'}
          </div>
        ) : (
          <div className="ml-result">
            <span
              id="ml-label"
              className={`ml-label${mlPrediction.label === 'SUSPICIOUS' ? ' suspicious' : ' authentic'}`}
            >
              {mlPrediction.label}
            </span>
            {mlPrediction.probability_suspicious != null && (
              <span className="ml-prob">
                Probability (suspicious): {(mlPrediction.probability_suspicious * 100).toFixed(1)}%
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

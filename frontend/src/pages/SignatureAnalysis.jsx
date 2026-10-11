import { useState } from 'react'
import SignatureUploader from '../components/SignatureUploader.jsx'
import SignaturePanel from '../components/SignaturePanel.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import { analyzeSignature } from '../api/signatureApi.js'

export default function SignatureAnalysis() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAnalyze = async (queryFile, referenceFile) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await analyzeSignature(queryFile, referenceFile)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Signature analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="analysis-page" id="main-content">
      <div className="page-header">
        <h1 className="page-title">Signature Forgery Detection</h1>
        <p className="page-subtitle">
          Detect pen hesitation, stroke tremor anomalies, and compare suspect signatures against reference genuine samples.
        </p>
      </div>

      <div className="section-spacer">
        <SignatureUploader onAnalyze={handleAnalyze} loading={loading} />
      </div>

      {loading && (
        <div className="card section-spacer">
          <Loading 
            message="Analyzing signature..." 
            steps={[
              { id: 'prep',       label: 'Preprocessing signature image' },
              { id: 'skeleton',   label: 'Extracting signature skeleton' },
              { id: 'tremor',     label: 'Analyzing tremor metrics' },
              { id: 'compare',    label: 'Performing forensic comparison' },
            ]}
            durations={[600, 800, 800, 500]}
          />
        </div>
      )}

      {error && (
        <div className="section-spacer">
          <ErrorMessage message={error} onRetry={() => setError(null)} />
        </div>
      )}

      {result && (
        <div className="section-spacer">
          <SignaturePanel data={result} />
        </div>
      )}
    </main>
  )
}

import { useState } from 'react'
import { analyzeImage } from '../api/imageApi.js'
import ImageUploader from '../components/ImageUploader.jsx'
import ImagePreview from '../components/ImagePreview.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EntropyPanel from '../components/EntropyPanel.jsx'
import ElaPanel from '../components/ElaPanel.jsx'
import NoisePanel from '../components/NoisePanel.jsx'
import TexturePanel from '../components/TexturePanel.jsx'
import MetadataPanel from '../components/MetadataPanel.jsx'
import ResultCard from '../components/ResultCard.jsx'
import { UploadCloud } from 'lucide-react'

function formatBytes(b) {
  if (!b) return '—'
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / (1024 * 1024)).toFixed(2)} MB`
}

export default function ImageAnalysis() {
  const [file, setFile] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  function handleFileSelect(f) {
    setFile(f)
    setResult(null)
    setError('')
  }

  async function handleAnalyze() {
    if (!file) return
    setIsAnalyzing(true)
    setResult(null)
    setError('')

    try {
      const data = await analyzeImage(file)
      setResult(data)
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const hasResult = result && result.success

  return (
    <main className="analysis-page" id="analysis-page">
      <div className="page-header">
        <h1 className="page-title">Image Analysis</h1>
        <p className="page-subtitle">
          Upload an image to perform preliminary forensic screening.
        </p>
      </div>

      {/* Upload & Preview */}
      <div className="card section-spacer">
        <div className="card-header">
          <div className="card-icon card-icon-cyan" aria-hidden="true"><UploadCloud size={24} /></div>
          <div>
            <div className="card-title">Upload Evidence</div>
            <div className="card-subtitle">JPG · JPEG · PNG · WEBP · max 10 MB</div>
          </div>
        </div>

        <ImageUploader
          file={file}
          onFileSelect={handleFileSelect}
          onAnalyze={handleAnalyze}
          isAnalyzing={isAnalyzing}
        />

        {file && !isAnalyzing && (
          <div style={{ marginTop: '1.25rem' }}>
            <ImagePreview
              file={file}
              imageInfo={hasResult ? result.image_info : null}
            />
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="section-spacer">
          <ErrorMessage message={error} onDismiss={() => setError('')} />
        </div>
      )}

      {/* Loading */}
      {isAnalyzing && (
        <div className="card section-spacer">
          <Loading />
        </div>
      )}

      {/* Results */}
      {hasResult && (
        <>
          {/* Overview cards */}
          <div className="overview-grid section-spacer">
            <div className="overview-card">
              <div className="overview-label">Global Entropy</div>
              <div className="overview-value cyan">
                {result.entropy?.global?.toFixed(2)}
              </div>
            </div>
            <div className="overview-card">
              <div className="overview-label">Entropy Variation</div>
              <div className="overview-value">
                {result.entropy?.std_local?.toFixed(3)}
              </div>
            </div>
            <div className="overview-card">
              <div className="overview-label">ELA Mean</div>
              <div className="overview-value teal" style={{ color: 'var(--accent-teal)' }}>
                {result.ela?.mean?.toFixed(2)}
              </div>
            </div>
            <div className="overview-card">
              <div className="overview-label">Risk Level</div>
              <div
                className={`overview-value${
                  result.preliminary_result?.risk_level === 'HIGH'
                    ? ' rose'
                    : result.preliminary_result?.risk_level === 'MEDIUM'
                    ? ' amber'
                    : ' green'
                }`}
                style={{
                  color:
                    result.preliminary_result?.risk_level === 'HIGH'
                      ? 'var(--risk-high)'
                      : result.preliminary_result?.risk_level === 'MEDIUM'
                      ? 'var(--risk-medium)'
                      : 'var(--risk-low)',
                }}
              >
                {result.preliminary_result?.risk_level}
              </div>
            </div>
          </div>

          {/* Result Card */}
          <div className="section-spacer">
            <ResultCard
              result={result.preliminary_result}
              mlPrediction={result.ml_prediction}
            />
          </div>

          {/* Analysis panels — 2 columns */}
          <div className="analysis-grid section-spacer">
            <EntropyPanel entropy={result.entropy} originalFile={file} />
            <ElaPanel ela={result.ela} originalFile={file} />
          </div>

          <div className="analysis-grid section-spacer">
            <NoisePanel noise={result.noise} />
            <TexturePanel texture={result.texture} />
          </div>

          {/* Metadata - full width */}
          <div className="section-spacer">
            <MetadataPanel
              metadata={result.metadata}
              imageInfo={result.image_info}
            />
          </div>
        </>
      )}
    </main>
  )
}

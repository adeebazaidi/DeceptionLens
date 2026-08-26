function formatBytes(b) {
  if (!b) return '—'
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / (1024 * 1024)).toFixed(2)} MB`
}

function MetaRow({ label, value }) {
  return (
    <div className="metadata-row">
      <span className="metadata-key">{label}</span>
      <span className={`metadata-val${!value ? ' metadata-null' : ''}`}>
        {value ?? 'Not available'}
      </span>
    </div>
  )
}

export default function MetadataPanel({ metadata, imageInfo }) {
  if (!metadata && !imageInfo) return null

  const exif = metadata?.exif
  const hasExif = exif && typeof exif === 'object' && Object.keys(exif).length > 0

  // Exclude low-value binary or known-noisy keys from EXIF display
  const SKIP_KEYS = ['MakerNote', 'UserComment', 'PrintImageMatching', 'ComponentsConfiguration']
  const exifEntries = hasExif
    ? Object.entries(exif).filter(([k]) => !SKIP_KEYS.includes(k)).slice(0, 30)
    : []

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon card-icon-rose" aria-hidden="true">🗂️</div>
        <div>
          <div className="card-title">Image Information</div>
          <div className="card-subtitle">Format, dimensions, and available metadata</div>
        </div>
      </div>

      <div className="metadata-table">
        <MetaRow label="Format"      value={metadata?.format || imageInfo?.format} />
        <MetaRow
          label="Dimensions"
          value={
            (metadata?.width && metadata?.height)
              ? `${metadata.width} × ${metadata.height} px`
              : imageInfo?.width
              ? `${imageInfo.width} × ${imageInfo.height} px`
              : null
          }
        />
        <MetaRow
          label="File Size"
          value={formatBytes(metadata?.file_size_bytes || imageInfo?.file_size)}
        />
        <MetaRow label="Color Mode"  value={metadata?.mode} />
        <MetaRow label="Software"    value={metadata?.software} />
      </div>

      {hasExif && exifEntries.length > 0 && (
        <div className="exif-section">
          <div className="exif-title">EXIF Data</div>
          <div className="exif-grid">
            {exifEntries.map(([k, v]) => (
              <div key={k} className="exif-item">
                <div className="exif-key">{k}</div>
                <div className="exif-val">{String(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!hasExif && (
        <div className="disclaimer-note" style={{ marginTop: '0.75rem' }}>
          ℹ️ No EXIF data found. This is common for PNG images, screenshots, and images
          that have been processed or re-saved. Absence of metadata does not indicate manipulation.
        </div>
      )}
    </div>
  )
}

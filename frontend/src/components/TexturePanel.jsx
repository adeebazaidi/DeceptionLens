const FEATURES = [
  { key: 'contrast',      label: 'Contrast',      desc: 'Local intensity variation' },
  { key: 'dissimilarity', label: 'Dissimilarity',  desc: 'Linear distance difference' },
  { key: 'homogeneity',   label: 'Homogeneity',   desc: 'Element distribution uniformity' },
  { key: 'energy',        label: 'Energy',         desc: 'Sum of squared elements' },
  { key: 'correlation',   label: 'Correlation',    desc: 'Linear grey-level dependency' },
]

export default function TexturePanel({ texture }) {
  if (!texture) return null

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon card-icon-amber" aria-hidden="true">🔲</div>
        <div>
          <div className="card-title">Texture Analysis</div>
          <div className="card-subtitle">GLCM (Gray-Level Co-occurrence Matrix)</div>
        </div>
      </div>

      <table className="forensic-table" aria-label="GLCM texture features">
        <thead>
          <tr>
            <th>Feature</th>
            <th>Description</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {FEATURES.map(({ key, label, desc }) => (
            <tr key={key}>
              <td>{label}</td>
              <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{desc}</td>
              <td>{texture[key] != null ? Number(texture[key]).toFixed(6) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

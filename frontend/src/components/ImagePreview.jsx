function formatBytes(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function ImagePreview({ file, imageInfo }) {
  const objectUrl = file ? URL.createObjectURL(file) : null

  return (
    <div className="image-preview-box">
      <div className="image-preview-header">Selected Evidence</div>
      {objectUrl && (
        <img
          src={objectUrl}
          alt="Selected image preview"
          className="image-preview-img"
          id="preview-image"
          onLoad={() => URL.revokeObjectURL(objectUrl)}
        />
      )}
      <div className="image-preview-meta">
        <div className="meta-item">
          <span className="meta-key">Filename</span>
          <span className="meta-val">{file?.name || '—'}</span>
        </div>
        {imageInfo ? (
          <>
            <div className="meta-item">
              <span className="meta-key">Dimensions</span>
              <span className="meta-val">{imageInfo.width} × {imageInfo.height}</span>
            </div>
            <div className="meta-item">
              <span className="meta-key">Format</span>
              <span className="meta-val">{imageInfo.format || '—'}</span>
            </div>
            <div className="meta-item">
              <span className="meta-key">File Size</span>
              <span className="meta-val">{formatBytes(imageInfo.file_size)}</span>
            </div>
          </>
        ) : (
          <div className="meta-item">
            <span className="meta-key">Size</span>
            <span className="meta-val">{formatBytes(file?.size)}</span>
          </div>
        )}
      </div>
    </div>
  )
}

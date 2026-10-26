import { useState, useEffect } from 'react'
import { FolderPlus, Edit3, X, AlertCircle } from 'lucide-react'

const CASE_TYPES = [
  'Image Forgery',
  'Fingerprint Verification',
  'Signature Verification',
  'Document Analysis',
  'Other',
]

const PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
const STATUSES = ['Open', 'In Progress', 'Under Review', 'Closed']

export default function CaseModal({
  isOpen,
  mode = 'create', // 'create' | 'edit'
  initialData = null,
  onSave,
  onCancel,
  loading = false,
}) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    case_type: 'Image Forgery',
    investigator: 'Inspector Alex Vance',
    priority: 'Medium',
    status: 'Open',
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (initialData && mode === 'edit') {
      setFormData({
        title: initialData.title || '',
        description: initialData.description || '',
        case_type: initialData.case_type || 'Image Forgery',
        investigator: initialData.investigator || '',
        priority: initialData.priority || 'Medium',
        status: initialData.status || 'Open',
      })
    } else {
      setFormData({
        title: '',
        description: '',
        case_type: 'Image Forgery',
        investigator: 'Inspector Alex Vance',
        priority: 'Medium',
        status: 'Open',
      })
    }
    setErrors({})
  }, [initialData, mode, isOpen])

  if (!isOpen) return null

  const validate = () => {
    const errs = {}
    if (!formData.title.trim()) {
      errs.title = 'Case Title is required.'
    } else if (formData.title.trim().length < 3) {
      errs.title = 'Case Title must be at least 3 characters long.'
    }

    if (!formData.investigator.trim()) {
      errs.investigator = 'Investigator Name is required.'
    }

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return
    onSave(formData)
  }

  return (
    <div className="modal-backdrop" onClick={onCancel} role="dialog" aria-modal="true">
      <div className="modal-window case-modal-window" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div className="modal-icon-badge badge-primary">
              {mode === 'create' ? <FolderPlus size={18} /> : <Edit3 size={18} />}
            </div>
            <div>
              <h3 className="modal-title">
                {mode === 'create' ? 'Create New Forensic Case' : `Edit Case: ${initialData?.case_id}`}
              </h3>
              <p className="modal-subtitle">
                {mode === 'create'
                  ? 'Initialize an official digital forensic case record with automated chain-of-custody tracking.'
                  : 'Update investigation parameters and priority.'}
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onCancel} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="modal-body">
            {mode === 'edit' && (
              <div className="form-group">
                <label className="form-label">Case Identifier</label>
                <input
                  type="text"
                  className="form-control"
                  value={initialData?.case_id || ''}
                  disabled
                  readOnly
                  style={{ backgroundColor: 'var(--bg-card-hover)', cursor: 'not-allowed', fontFamily: 'var(--font-mono)' }}
                />
                <span className="form-hint">Case ID is permanent and immutable for chain of custody.</span>
              </div>
            )}

            <div className="form-group">
              <label className="form-label required">Case Title</label>
              <input
                type="text"
                className={`form-control ${errors.title ? 'is-invalid' : ''}`}
                placeholder="e.g., Forensic Audit of Questioned Bank Draft"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                autoFocus
              />
              {errors.title && (
                <div className="form-error">
                  <AlertCircle size={14} /> {errors.title}
                </div>
              )}
            </div>

            <div className="form-row">
              <div className="form-group col-half">
                <label className="form-label required">Primary Forensic Type</label>
                <select
                  className="form-control"
                  value={formData.case_type}
                  onChange={(e) => setFormData({ ...formData, case_type: e.target.value })}
                >
                  {CASE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group col-half">
                <label className="form-label required">Priority Level</label>
                <select
                  className="form-control"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group col-half">
                <label className="form-label required">Lead Investigator</label>
                <input
                  type="text"
                  className={`form-control ${errors.investigator ? 'is-invalid' : ''}`}
                  placeholder="e.g., Inspector Sarah Connor"
                  value={formData.investigator}
                  onChange={(e) => setFormData({ ...formData, investigator: e.target.value })}
                />
                {errors.investigator && (
                  <div className="form-error">
                    <AlertCircle size={14} /> {errors.investigator}
                  </div>
                )}
              </div>

              <div className="form-group col-half">
                <label className="form-label required">Initial Status</label>
                <select
                  className="form-control"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Investigation Synopsis / Description</label>
              <textarea
                className="form-control textarea"
                rows={3}
                placeholder="Provide incident context, source of questioned materials, and scope of requested laboratory analysis..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading
                ? 'Saving Record...'
                : mode === 'create'
                ? 'Create Forensic Case'
                : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, FileText, RefreshCw } from 'lucide-react'
import { fetchDashboardOverview } from '../api/reportApi'
import '../styles/reports.css'

// Verdicts use the app's reserved risk colours, always paired with the verdict text.
function verdictColor(verdict = '') {
  const v = verdict.toUpperCase()
  if (v.includes('HIGH') || v.includes('SUSPICIOUS') || v.includes('FORG')) return 'var(--risk-high)'
  if (v.includes('MEDIUM')) return 'var(--risk-medium)'
  if (v.includes('LOW') || v.includes('CONSISTENT') || v.includes('AUTHENTIC')) return 'var(--risk-low)'
  return 'var(--text-muted)'
}

function formatDay(isoDate, opts = { day: 'numeric', month: 'short' }) {
  return new Date(`${isoDate}T00:00:00Z`).toLocaleDateString(undefined, { ...opts, timeZone: 'UTC' })
}

function formatDateTime(iso) {
  return iso ? new Date(iso).toLocaleString() : 'N/A'
}

/** Horizontal bar list for one series; widths are proportional to the largest value. */
function BarList({ rows, color = 'var(--accent-cyan)', colorFor, unit }) {
  if (!rows || rows.length === 0) {
    return <p className="dl-empty">No records yet.</p>
  }
  const max = Math.max(1, ...rows.map((r) => r.count))
  return (
    <div className="dl-barlist">
      {rows.map((row) => {
        const fill = colorFor ? colorFor(row.label) : color
        return (
          <div
            key={row.label}
            className="dl-barlist-row"
            tabIndex={0}
            title={`${row.label}: ${row.count} ${unit}`}
            aria-label={`${row.label}: ${row.count} ${unit}`}
          >
            <span className="dl-barlist-label">
              {colorFor && <span className="dl-status-dot" style={{ background: fill }} aria-hidden="true" />}
              {row.label}
            </span>
            <span className="dl-barlist-track">
              {row.count > 0 && (
                <span className="dl-bar" style={{ width: `calc((100% - 2.5rem) * ${row.count / max})`, background: fill }} />
              )}
              <span className="dl-barlist-value">{row.count}</span>
            </span>
          </div>
        )
      })}
    </div>
  )
}

/** Column chart of audit events per day, with a per-column hover/focus tooltip. */
function ActivityChart({ data }) {
  const [hover, setHover] = useState(null)
  const [width, setWidth] = useState(560)
  const containerRef = useRef(null)

  // Draw at the container's real pixel width so text and bars keep their size.
  useEffect(() => {
    const el = containerRef.current
    if (!el) return undefined
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(280, Math.round(entry.contentRect.width))))
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const W = width
  const H = 190
  const pad = { l: 28, r: 8, t: 18, b: 24 }
  const plotW = W - pad.l - pad.r
  const plotH = H - pad.t - pad.b
  const slot = plotW / data.length
  const barW = Math.min(24, slot * 0.6)
  const maxV = Math.max(...data.map((d) => d.events), 0)
  const top = Math.max(4, Math.ceil(maxV / 4) * 4)
  const ticks = [0, top / 2, top]
  const y = (v) => pad.t + plotH - (v / top) * plotH
  const maxIndex = maxV > 0 ? data.findIndex((d) => d.events === maxV) : -1

  const columnPath = (x, yTop, w, h) => {
    const r = Math.min(4, h, w / 2)
    return `M${x},${yTop + h} V${yTop + r} Q${x},${yTop} ${x + r},${yTop} H${x + w - r} Q${x + w},${yTop} ${x + w},${yTop + r} V${yTop + h} Z`
  }

  const hovered = hover !== null ? data[hover] : null

  return (
    <div className="dl-activity" ref={containerRef}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Audit events per day over the last 14 days">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="var(--bg-card-hover)" strokeWidth="1" />
            <text x={pad.l - 6} y={y(t) + 3} textAnchor="end" className="dl-axis-text">{t}</text>
          </g>
        ))}
        {data.map((d, i) => {
          const cx = pad.l + slot * i + slot / 2
          const h = (d.events / top) * plotH
          return (
            <g
              key={d.date}
              className="dl-activity-col"
              tabIndex={0}
              aria-label={`${formatDay(d.date)}: ${d.events} events`}
              onPointerEnter={() => setHover(i)}
              onPointerLeave={() => setHover(null)}
              onFocus={() => setHover(i)}
              onBlur={() => setHover(null)}
            >
              <rect x={pad.l + slot * i} y={pad.t} width={slot} height={plotH} fill="transparent" />
              {h > 0 && (
                <path className="dl-activity-bar" d={columnPath(cx - barW / 2, y(d.events), barW, h)} fill="var(--accent-cyan)" />
              )}
              {i === maxIndex && (
                <text x={cx} y={y(d.events) - 5} textAnchor="middle" className="dl-value-text">{d.events}</text>
              )}
              {(slot >= 48 || i % 2 === (data.length - 1) % 2) && (
                <text x={cx} y={H - 6} textAnchor="middle" className="dl-axis-text">{formatDay(d.date)}</text>
              )}
            </g>
          )
        })}
      </svg>
      {hovered && (
        <div
          className="dl-tooltip"
          style={{
            left: `${((pad.l + slot * hover + slot / 2) / W) * 100}%`,
            top: `calc(${(y(hovered.events) / H) * 100}% - 8px)`,
          }}
        >
          <strong>{hovered.events} events</strong>
          {formatDay(hovered.date, { weekday: 'short', day: 'numeric', month: 'short' })}
        </div>
      )}
    </div>
  )
}

/** Dashboard tab of the Dashboard & Reports module. */
export default function DashboardView() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      setData(await fetchDashboardOverview())
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load dashboard.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const totals = data?.totals

  return (
    <section id="dashboard-view">
      <div className="dl-view-toolbar">
        <p>Cases, evidence, analysis outcomes, integrity checks, and report activity across the lab.</p>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            setLoading(true)
            load()
          }}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {error && (
        <div className="toast-alert toast-error" role="alert" style={{ position: 'static', marginBottom: '1rem' }}>
          <AlertTriangle size={18} /> <span>{error}</span>
        </div>
      )}

      {loading && !data && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 1rem auto' }} />
          <p>Loading dashboard…</p>
        </div>
      )}

      {data && (
        <>
          {/* Headline figures */}
          <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            <div className="stat-card">
              <div className="stat-label">Active cases</div>
              <div className="stat-value">{totals.active_cases}</div>
              <div className="stat-sub">{totals.archived_cases} archived</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Active evidence</div>
              <div className="stat-value">{totals.active_evidence}</div>
              <div className="stat-sub">Files in custody</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Analyses run</div>
              <div className="stat-value">{totals.analyses}</div>
              <div className="stat-sub">Across all modules</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Saved reports</div>
              <div className="stat-value">{totals.reports}</div>
              <div className="stat-sub">SHA-256 sealed</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Integrity checks</div>
              <div className="stat-value">{totals.integrity_checks}</div>
              <div className="stat-sub" style={{ color: totals.integrity_mismatches > 0 ? 'var(--risk-high)' : undefined }}>
                {totals.integrity_mismatches > 0
                  ? `⚠ ${totals.integrity_mismatches} failed check${totals.integrity_mismatches === 1 ? '' : 's'}`
                  : 'All checks passed'}
              </div>
            </div>
          </div>

          {/* Activity */}
          <section className="dl-panel dl-panel-wide">
            <h2 className="dl-panel-title">Activity — last 14 days</h2>
            <p className="dl-panel-sub">Audit-trail events per day (cases, evidence, analyses, integrity checks, reports)</p>
            <ActivityChart data={data.activity} />
          </section>

          {/* Breakdowns */}
          <div className="dl-panel-grid">
            <section className="dl-panel">
              <h2 className="dl-panel-title">Cases by status</h2>
              <p className="dl-panel-sub">Active cases in each workflow stage</p>
              <BarList rows={data.cases_by_status} unit="cases" />
            </section>
            <section className="dl-panel">
              <h2 className="dl-panel-title">Cases by priority</h2>
              <p className="dl-panel-sub">Active cases, most urgent first</p>
              <BarList rows={data.cases_by_priority} unit="cases" />
            </section>
            <section className="dl-panel">
              <h2 className="dl-panel-title">Cases by type</h2>
              <p className="dl-panel-sub">Active cases per investigation category</p>
              <BarList rows={data.cases_by_type} unit="cases" />
            </section>
            <section className="dl-panel">
              <h2 className="dl-panel-title">Evidence by type</h2>
              <p className="dl-panel-sub">Active evidence items</p>
              <BarList rows={data.evidence_by_type} unit="items" />
            </section>
            <section className="dl-panel">
              <h2 className="dl-panel-title">Analysis verdicts</h2>
              <p className="dl-panel-sub">Outcome of every analysis run on stored evidence</p>
              <BarList rows={data.analysis_verdicts} colorFor={verdictColor} unit="analyses" />
            </section>
            <section className="dl-panel">
              <h2 className="dl-panel-title">Analyses by module</h2>
              <p className="dl-panel-sub">Which forensic modules are used most</p>
              <BarList rows={data.analyses_by_module} unit="analyses" />
            </section>
          </div>

          {/* Recent activity tables */}
          <div className="dl-panel-grid">
            <section className="dl-panel">
              <h2 className="dl-panel-title">Recent analyses</h2>
              <p className="dl-panel-sub">Latest forensic module runs</p>
              {data.recent_analyses.length === 0 ? (
                <p className="dl-empty">No analyses have been run yet.</p>
              ) : (
                <div className="table-responsive">
                  <table className="dl-table">
                    <thead>
                      <tr><th>Evidence</th><th>Module</th><th>Verdict</th><th>When</th></tr>
                    </thead>
                    <tbody>
                      {data.recent_analyses.map((a) => (
                        <tr key={a.record_id}>
                          <td>
                            <div className="dl-mono">{a.evidence_id}</div>
                            <div className="dl-muted">{a.case_id}</div>
                          </td>
                          <td>{a.module_type}</td>
                          <td>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                              <span className="dl-status-dot" style={{ background: verdictColor(a.verdict) }} aria-hidden="true" />
                              {a.verdict}
                            </span>
                          </td>
                          <td className="dl-muted">{formatDateTime(a.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="dl-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                <div>
                  <h2 className="dl-panel-title">Recent reports</h2>
                  <p className="dl-panel-sub">Latest saved, sealed case reports</p>
                </div>
                <Link to="/dashboard?tab=reports" className="btn btn-secondary btn-sm">
                  <FileText size={14} /> All reports
                </Link>
              </div>
              {data.recent_reports.length === 0 ? (
                <p className="dl-empty">No reports have been generated yet.</p>
              ) : (
                <div className="table-responsive">
                  <table className="dl-table">
                    <thead>
                      <tr><th>Report</th><th>Examiner</th><th>Generated</th></tr>
                    </thead>
                    <tbody>
                      {data.recent_reports.map((r) => (
                        <tr key={r.report_id}>
                          <td>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{r.title}</div>
                            <div className="dl-mono">{r.report_id}</div>
                          </td>
                          <td>{r.generated_by}</td>
                          <td className="dl-muted">{formatDateTime(r.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  )
}

import { useSearchParams } from 'react-router-dom'
import { FileText, LayoutDashboard } from 'lucide-react'
import DashboardView from './Dashboard.jsx'
import ReportsView from './Reports.jsx'
import '../styles/reports.css'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'reports', label: 'Reports', icon: FileText },
]

/** Dashboard & Report Management module: one page, two tabs (?tab=dashboard|reports). */
export default function DashboardReports() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') === 'reports' ? 'reports' : 'dashboard'

  return (
    <main className="dl-page" id="dashboard-reports-page">
      <div className="dl-page-header">
        <div>
          <div className="hero-badge" style={{ marginBottom: '0.5rem' }}>
            <span className="hero-badge-dot" aria-hidden="true" />
            Dashboard &amp; Report Management
          </div>
          <h1 className="page-title">Dashboard &amp; Reports</h1>
          <p>Lab-wide forensic overview and SHA-256-sealed case reports in one place.</p>
        </div>
      </div>

      <div className="dl-module-tabs" role="tablist" aria-label="Dashboard and reports">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            id={`tab-${id}-btn`}
            aria-selected={activeTab === id}
            className={`case-tab ${activeTab === id ? 'active' : ''}`}
            onClick={() => setSearchParams(id === 'dashboard' ? {} : { tab: id })}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      {activeTab === 'dashboard' ? <DashboardView /> : <ReportsView />}
    </main>
  )
}

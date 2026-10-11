import { useState } from 'react';
import { documentApi } from '../api/documentApi.js';
import DocumentUploader from '../components/DocumentUploader.jsx';
import Loading from '../components/Loading.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';
import { Shield, FileText, AlertTriangle, Users, MapPin, Calendar, Briefcase, IndianRupee, Search } from 'lucide-react';

export default function DocumentAnalysis() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [activePage, setActivePage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  const handleFileSelect = (f) => {
    setFile(f);
    setResult(null);
    setError('');
    setActivePage(1);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setError('');
    setResult(null);
    setActivePage(1);

    try {
      const data = await documentApi.analyzeDocument(file);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze document.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderEntityList = (items, icon) => {
    if (!items || items.length === 0) return <p className="text-secondary text-sm">None detected</p>;
    
    const uniqueVals = Array.from(new Set(items.map(i => i.value)));

    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {uniqueVals.map((val, idx) => {
           const matches = items.filter(i => i.value === val);
           const pages = Array.from(new Set(matches.map(m => m.page))).join(', ');
           return (
            <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', background: 'rgba(255, 255, 255, 0.03)', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-dim)' }}>
              <span className="text-secondary" style={{ display: 'flex', marginTop: '2px' }}>{icon}</span>
              <span className="fw-500" style={{ wordBreak: 'break-word', flex: 1 }}>{val}</span>
              <span className="text-xs text-muted" style={{ whiteSpace: 'nowrap' }}>Pg: {pages}</span>
            </li>
           )
        })}
      </ul>
    );
  };

  const highlightText = (text, query) => {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={index} style={{ backgroundColor: 'rgba(230, 136, 21, 0.4)', color: 'inherit', padding: '0 2px', borderRadius: '2px' }}>{part}</mark> : part
    );
  };

  const hasResult = result && result.document;

  return (
    <main className="analysis-page" id="document-analysis-page">
      <div className="page-header">
        <h1 className="page-title">Document Analysis</h1>
        <p className="page-subtitle">
          Extract information, entities, and analyze for internal inconsistencies.
        </p>
      </div>

      {/* Upload & Preview */}
      <div className="card section-spacer">
        <div className="card-header">
          <div className="card-icon card-icon-violet" aria-hidden="true"><FileText size={24} /></div>
          <div>
            <div className="card-title">Upload Document</div>
            <div className="card-subtitle">PDF · JPG · PNG · TIFF · max 20 MB</div>
          </div>
        </div>

        <DocumentUploader 
          file={file}
          onFileSelect={handleFileSelect}
          onAnalyze={handleAnalyze} 
          isAnalyzing={isAnalyzing} 
        />
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
          <Loading 
            message="Analyzing Document..." 
            steps={[
              { id: 'ocr',       label: 'Extracting text via OCR' },
              { id: 'nlp',       label: 'Identifying entities' },
              { id: 'normalize', label: 'Normalizing semantic info' },
              { id: 'consistency', label: 'Running consistency checks' },
              { id: 'report',    label: 'Structuring forensic report' },
            ]}
            durations={[900, 800, 600, 700, 500]}
          />
        </div>
      )}

      {/* Results */}
      {hasResult && (
        <>
          {/* Overview cards */}
          <div className="overview-grid section-spacer">
            <div className="overview-card">
              <div className="overview-label">Pages</div>
              <div className="overview-value cyan">
                {result.document.page_count}
              </div>
            </div>
            <div className="overview-card">
              <div className="overview-label">Entities Extracted</div>
              <div className="overview-value">
                {Object.values(result.entities).reduce((acc, curr) => acc + curr.length, 0)}
              </div>
            </div>
            <div className="overview-card">
              <div className="overview-label">Consistency Status</div>
              <div className="overview-value" style={{ 
                color: result.consistency_analysis.status.includes('No') ? 'var(--risk-low)' : 'var(--risk-medium)',
                fontSize: '1.25rem' 
              }}>
                {result.consistency_analysis.status}
              </div>
            </div>
            <div className="overview-card">
              <div className="overview-label">Issues Found</div>
              <div className={`overview-value ${result.consistency_analysis.issues?.length > 0 ? 'rose' : 'green'}`}>
                {result.consistency_analysis.issues?.length || 0}
              </div>
            </div>
          </div>

          {/* Analysis panels — 2 columns */}
          <div className="analysis-grid section-spacer">
            
            {/* Extracted Text Panel */}
            <div className="card">
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                  <div className="card-icon card-icon-cyan"><FileText size={20} /></div>
                  <div className="card-title">Extracted Text</div>
                </div>
                
                {result.document.page_count > 1 && (
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    {Array.from({ length: result.document.page_count }, (_, i) => i + 1).map(pageNum => (
                      <button 
                        key={pageNum}
                        onClick={() => setActivePage(pageNum)}
                        style={{
                          background: activePage === pageNum ? 'var(--accent-cyan)' : 'var(--bg-base)',
                          color: activePage === pageNum ? '#fff' : 'var(--text-secondary)',
                          border: `1px solid ${activePage === pageNum ? 'var(--accent-cyan)' : 'var(--border-dim)'}`,
                          borderRadius: '4px',
                          padding: '0.2rem 0.5rem',
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        {pageNum}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ marginBottom: '1rem', position: 'relative' }}>
                <Search size={16} className="text-muted" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
                <input 
                  type="text" 
                  placeholder="Search text..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem 0.5rem 0.5rem 2.25rem', 
                    borderRadius: 'var(--radius-sm)', 
                    border: '1px solid var(--border-dim)',
                    background: 'var(--bg-base)',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div style={{ 
                maxHeight: '600px', 
                overflowY: 'auto', 
                backgroundColor: 'rgba(0, 0, 0, 0.02)', 
                border: '1px solid var(--border-dim)',
                padding: '1.25rem', 
                borderRadius: 'var(--radius-md)' 
              }}>
                {(() => {
                  const pageData = result.pages.find(p => p.page_num === activePage);
                  if (!pageData) return <p className="text-muted text-sm">No text extracted.</p>;
                  return (
                    <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                      {highlightText(pageData.cleaned_text, searchQuery)}
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Entities Panel */}
            <div className="card">
              <div className="card-header">
                <div className="card-icon card-icon-teal"><Users size={20} /></div>
                <div className="card-title">Entities & Case Info</div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxHeight: '680px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                
                <div>
                  <h4 className="text-sm fw-600 mb-2" style={{ color: 'var(--text-primary)' }}>Persons</h4>
                  {renderEntityList(result.entities.persons, <Users size={14} />)}
                </div>

                <div>
                  <h4 className="text-sm fw-600 mb-2" style={{ color: 'var(--text-primary)' }}>Dates</h4>
                  {renderEntityList(result.entities.dates, <Calendar size={14} />)}
                </div>

                <div>
                  <h4 className="text-sm fw-600 mb-2" style={{ color: 'var(--text-primary)' }}>Locations / Organizations</h4>
                  {renderEntityList([...result.entities.locations, ...result.entities.organizations], <MapPin size={14} />)}
                </div>

                <div>
                  <h4 className="text-sm fw-600 mb-2" style={{ color: 'var(--text-primary)' }}>Monetary Values</h4>
                  {renderEntityList(result.entities.money, <IndianRupee size={14} />)}
                </div>

                <div style={{ height: '1px', background: 'var(--border-dim)', margin: '0.5rem 0' }} />

                <div>
                  <h4 className="text-sm fw-600 mb-2" style={{ color: 'var(--text-primary)' }}>Case Identifiers</h4>
                  {renderEntityList(result.case_information.case_numbers, <Briefcase size={14} />)}
                </div>

                <div>
                  <h4 className="text-sm fw-600 mb-2" style={{ color: 'var(--text-primary)' }}>Keywords</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {Array.from(new Set(result.case_information.keywords.map(k => k.value))).map((kw, i) => (
                      <span key={i} style={{ 
                        padding: '0.2rem 0.6rem', 
                        backgroundColor: 'var(--accent-teal)', 
                        color: 'white',
                        borderRadius: '999px', 
                        fontSize: '0.7rem', 
                        fontWeight: '600',
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase'
                      }}>
                        {kw}
                      </span>
                    ))}
                    {result.case_information.keywords.length === 0 && <span className="text-xs text-muted">None</span>}
                  </div>
                </div>

              </div>
            </div>
          </div>

          {/* Consistency Analysis - Full Width */}
          <div className="card section-spacer" style={{ borderColor: result.consistency_analysis.issues?.length > 0 ? 'rgba(248, 113, 113, 0.4)' : 'var(--border-dim)' }}>
            <div className="card-header">
              <div className={`card-icon ${result.consistency_analysis.issues?.length > 0 ? 'card-icon-rose' : 'card-icon-cyan'}`}>
                <Shield size={20} />
              </div>
              <div className="card-title">Consistency Analysis</div>
            </div>

            <div className="card-body">
              {result.consistency_analysis.issues && result.consistency_analysis.issues.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                    {result.consistency_analysis.issues.map((issue, idx) => (
                      <div key={idx} style={{ 
                        padding: '1.25rem', 
                        border: '1px solid rgba(248, 113, 113, 0.3)', 
                        borderRadius: 'var(--radius-md)', 
                        backgroundColor: 'rgba(248, 113, 113, 0.05)',
                        position: 'relative',
                        overflow: 'hidden'
                      }}>
                        <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: 'var(--accent-rose)' }} />
                        <h4 className="fw-600 text-sm mb-2" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--accent-rose)' }}>
                          <AlertTriangle size={16} /> {issue.title}
                          {issue.field && (
                            <span style={{ 
                              fontSize: '0.6rem', 
                              backgroundColor: 'var(--accent-rose)', 
                              color: 'white', 
                              padding: '0.15rem 0.4rem', 
                              borderRadius: '4px', 
                              marginLeft: 'auto',
                              letterSpacing: '0.05em'
                            }}>
                              {issue.field.replace('_', ' ').toUpperCase()}
                            </span>
                          )}
                        </h4>
                        <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>{issue.reason}</p>
                        
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          {issue.evidence.map((ev, i) => (
                            <div key={i} style={{ 
                              background: 'var(--bg-surface)', 
                              border: '1px solid var(--border-dim)', 
                              padding: '0.5rem 0.75rem', 
                              borderRadius: '4px' 
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                                <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{ev.value}</strong>
                                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Page {ev.page}</span>
                              </div>
                              <div style={{ fontStyle: 'italic', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>"{ev.source_text}"</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <div style={{ 
                  padding: '2rem', 
                  textAlign: 'center', 
                  backgroundColor: 'rgba(45, 212, 191, 0.05)', 
                  border: '1px solid rgba(45, 212, 191, 0.2)',
                  borderRadius: 'var(--radius-md)'
                }}>
                  <Shield size={32} style={{ color: 'var(--risk-low)', marginBottom: '1rem', opacity: 0.8 }} />
                  <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>No significant internal contradictions detected.</h4>
                  <p className="text-sm text-secondary">The extracted entities appear to be logically consistent across the document based on their semantic context.</p>
                </div>
              )}
            </div>
          </div>

        </>
      )}
    </main>
  );
}

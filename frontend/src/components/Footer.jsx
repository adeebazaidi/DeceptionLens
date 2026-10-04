import { Link } from 'react-router-dom'
import { ShieldAlert, Globe, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer style={{
      marginTop: 'auto',
      padding: '3rem 2rem 1.5rem',
      backgroundColor: 'var(--bg-surface, #ffffff)',
      borderTop: '1px solid var(--border-dim, #e2e8f0)',
      color: 'var(--text-secondary, #475569)',
      fontSize: '0.9rem',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      fontFamily: 'var(--font-sans, Inter, sans-serif)'
    }}>
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        gap: '2rem',
        maxWidth: '1200px',
        width: '100%',
        marginBottom: '2rem'
      }}>
        
        {/* Brand & Mission */}
        <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <img src="/logo.png" alt="DeceptionLens Logo" style={{ width: '32px', height: '32px', borderRadius: '8px' }} />
            <span style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary, #1e293b)' }}>DeceptionLens</span>
          </div>
          <p style={{ lineHeight: '1.6', margin: 0 }}>
            A next-generation digital forensics suite. Utilizing advanced algorithms to analyze image integrity, verify fingerprints, and detect signature forgeries with high precision.
          </p>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
            <a href="#" style={{ color: 'var(--text-secondary)', transition: 'color 0.2s' }}><Globe size={20} /></a>
            <a href="#" style={{ color: 'var(--text-secondary)', transition: 'color 0.2s' }}><Mail size={20} /></a>
          </div>
        </div>

        {/* Modules */}
        <div style={{ flex: '1 1 200px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h4 style={{ margin: 0, color: 'var(--text-primary, #1e293b)', fontWeight: '700', textTransform: 'uppercase', fontSize: '0.85rem', letterSpacing: '0.05em' }}>Analysis Modules</h4>
          <Link to="/analyze" style={{ color: 'var(--text-secondary)', textDecoration: 'none', transition: 'color 0.2s' }}>Image Forgery</Link>
          <Link to="/fingerprint" style={{ color: 'var(--text-secondary)', textDecoration: 'none', transition: 'color 0.2s' }}>Fingerprint Verification</Link>
          <Link to="/signature" style={{ color: 'var(--text-secondary)', textDecoration: 'none', transition: 'color 0.2s' }}>Signature Screening</Link>
        </div>

        {/* Legal & Notice */}
        <div style={{ flex: '1 1 250px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h4 style={{ margin: 0, color: 'var(--text-primary, #1e293b)', fontWeight: '700', textTransform: 'uppercase', fontSize: '0.85rem', letterSpacing: '0.05em' }}>Usage Notice</h4>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', padding: '1rem', background: 'var(--risk-high-bg, rgba(211,22,56,0.1))', borderRadius: '8px', color: 'var(--risk-high, #d31638)' }}>
            <ShieldAlert size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
            <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.5', fontWeight: '500' }}>
              Designed exclusively for research and educational purposes. Not intended as definitive legal proof.
            </p>
          </div>
        </div>
      </div>

      {/* Copyright */}
      <div style={{ 
        width: '100%', 
        borderTop: '1px solid var(--border-dim, #e2e8f0)', 
        paddingTop: '1.5rem', 
        textAlign: 'center',
        opacity: 0.8 
      }}>
        © {new Date().getFullYear()} DeceptionLens Team. All rights reserved.
      </div>
    </footer>
  )
}

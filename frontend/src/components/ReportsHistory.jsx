import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';

export default function ReportsHistory({ onSelect }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const listRef = useRef(null);

  const load = async () => {
    try {
      const res = await fetch('/api/reports');
      const data = await res.json();
      setReports(data);
    } catch {
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (!loading && listRef.current && reports.length > 0) {
      gsap.fromTo(listRef.current.children,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, stagger: 0.07, duration: 0.4, ease: 'power2.out' }
      );
    }
  }, [loading, reports]);

  const recColor = (rec) => ({
    BULLISH: 'var(--green)', BEARISH: 'var(--red)', NEUTRAL: 'var(--yellow)',
  }[rec?.toUpperCase()] || 'var(--text-secondary)');

  const handleSelect = async (ticker) => {
    try {
      const res = await fetch(`/api/report/${ticker}`);
      const data = await res.json();
      onSelect(data);
    } catch (e) {
      alert('Failed to load report: ' + e.message);
    }
  };

  if (loading) return (
    <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
      <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5 }}>
        Loading reports…
      </motion.span>
    </div>
  );

  if (reports.length === 0) return (
    <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
      <p style={{ fontSize: 32, marginBottom: 12 }}>📋</p>
      <p>No reports yet. Run your first analysis above.</p>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div className="section-title" style={{ marginBottom: 0 }}>Research History</div>
        <button className="btn btn-ghost" onClick={load} style={{ padding: '6px 14px', fontSize: 12 }}>
          ↻ Refresh
        </button>
      </div>
      <div ref={listRef} style={{ display: 'grid', gap: 12 }}>
        {reports.map((r, i) => (
          <motion.div
            key={r.filename}
            whileHover={{ scale: 1.01, x: 4 }}
            whileTap={{ scale: 0.99 }}
            onClick={() => handleSelect(r.ticker)}
            style={{
              display: 'grid',
              gridTemplateColumns: '60px 1fr auto auto',
              alignItems: 'center',
              gap: 16,
              padding: '14px 20px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-border)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <div style={{
              fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 16,
              color: 'var(--text-primary)',
            }}>
              {r.ticker}
            </div>
            <div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{r.date}</p>
              {r.current_price && (
                <p style={{ fontSize: 13, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  ${r.current_price?.toFixed(2)}
                </p>
              )}
            </div>
            <div>
              {r.margin_of_safety_pct != null && (
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 12,
                  color: r.margin_of_safety_pct > 0 ? 'var(--green)' : 'var(--red)',
                }}>
                  MoS: {r.margin_of_safety_pct > 0 ? '+' : ''}{r.margin_of_safety_pct?.toFixed(1)}%
                </span>
              )}
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
                color: recColor(r.recommendation), letterSpacing: '0.05em',
              }}>
                {r.recommendation}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

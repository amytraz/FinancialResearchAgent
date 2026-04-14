import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { gsap } from 'gsap';

import ParticleBackground from './components/ParticleBackground';
import ResearchProgress from './components/ResearchProgress';
import ResearchReport from './components/ResearchReport';
import ReportsHistory from './components/ReportsHistory';

/* ── Phase step mapping ─────────────────────────────────────── */
function phaseToStep(phase) {
  const map = { BOOT: 0, BOOT2: 1, OBSERVE: 2, ORIENT: 3, DECIDE: 4, ACT: 5 };
  return map[phase] ?? 0;
}

/* ── Ticker suggestions ─────────────────────────────────────── */
const SUGGESTIONS = ['NVDA', 'AAPL', 'TSLA', 'GOOGL', 'MSFT', 'AMZN', 'META', 'AMD'];

/* ── Hero Header ────────────────────────────────────────────── */
function HeroHeader() {
  const logoRef = useRef(null);
  const headingRef = useRef(null);

  useEffect(() => {
    const tl = gsap.timeline();
    tl.fromTo(logoRef.current,
      { opacity: 0, scale: 0.5, rotation: -180 },
      { opacity: 1, scale: 1, rotation: 0, duration: 1, ease: 'back.out(1.5)' }
    ).fromTo(headingRef.current.children,
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, stagger: 0.12, duration: 0.7, ease: 'power3.out' },
      '-=0.4'
    );
  }, []);

  return (
    <div style={{ textAlign: 'center', padding: '60px 20px 0' }}>
      {/* Logo */}
      <div ref={logoRef} style={{ marginBottom: 24 }}>
        <div style={{
          width: 72, height: 72, margin: '0 auto',
          background: 'linear-gradient(135deg, var(--accent), #0066FF)',
          borderRadius: '20px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 32, boxShadow: '0 8px 40px rgba(0,212,255,0.4)',
          position: 'relative',
        }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
            style={{
              position: 'absolute', inset: -3, borderRadius: 24,
              border: '1px solid var(--accent-border)',
              borderTopColor: 'var(--accent)',
            }}
          />
          📈
        </div>
      </div>

      <div ref={headingRef}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '4px 16px', background: 'var(--accent-dim)',
          border: '1px solid var(--accent-border)', borderRadius: 20,
          marginBottom: 20,
        }}>
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 2 }}
            style={{ width: 6, height: 6, background: 'var(--accent)', borderRadius: '50%' }}
          />
          <span style={{ fontSize: 11, color: 'var(--accent)', letterSpacing: '0.15em', fontFamily: 'var(--font-mono)' }}>
            AUTONOMOUS RESEARCH AGENT · v2.0
          </span>
        </div>

        <h1 style={{
          fontFamily: 'var(--font-display)', fontSize: 'clamp(36px, 6vw, 68px)',
          fontWeight: 800, lineHeight: 1.05,
          background: 'linear-gradient(135deg, #E6EDF3 0%, var(--accent) 50%, #0066FF 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundClip: 'text', marginBottom: 16,
        }}>
          ARA-1 Financial
          <br />Research Agent
        </h1>

        <p style={{
          fontSize: 'clamp(14px, 2vw, 17px)', color: 'var(--text-secondary)',
          maxWidth: 560, margin: '0 auto 12px', lineHeight: 1.7,
        }}>
          Institutional-grade equity analysis powered by autonomous AI.
          OODA loop architecture with deterministic DCF valuation engine.
        </p>

        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
          {['Parallel Data Collection', 'DCF Valuation', 'Bias-Free Decisions', 'Hedge-Fund Reports'].map((tag) => (
            <span key={tag} style={{
              fontSize: 11, color: 'var(--text-muted)', padding: '3px 10px',
              border: '1px solid var(--border)', borderRadius: 20,
            }}>
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Search Box ─────────────────────────────────────────────── */
function SearchBox({ onSubmit, loading }) {
  const [ticker, setTicker] = useState('');
  const inputRef = useRef(null);
  const formRef = useRef(null);

  useEffect(() => {
    gsap.fromTo(formRef.current,
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.7, ease: 'power3.out', delay: 0.8 }
    );
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const t = ticker.trim().toUpperCase();
    if (t) {
      gsap.to(formRef.current, { scale: 0.98, duration: 0.1, yoyo: true, repeat: 1 });
      onSubmit(t);
    }
  };

  return (
    <div ref={formRef} style={{ maxWidth: 600, margin: '0 auto', padding: '36px 20px 0' }}>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16, position: 'relative' }}>
          <input
            ref={inputRef}
            id="ticker-input"
            className="input"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter ticker symbol  (e.g. NVDA, AAPL, TSLA)"
            disabled={loading}
            maxLength={6}
            autoComplete="off"
            autoCorrect="off"
            spellCheck="false"
          />
          {ticker && (
            <motion.button
              type="button"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              onClick={() => setTicker('')}
              style={{
                position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-muted)', fontSize: 18,
              }}
            >
              ×
            </motion.button>
          )}
        </div>

        <button
          type="submit"
          id="run-research-btn"
          className="btn btn-primary"
          disabled={loading || !ticker.trim()}
          style={{ width: '100%', padding: '15px', fontSize: 15 }}
        >
          {loading ? (
            <>
              <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                ⟳
              </motion.span>
              Researching…
            </>
          ) : (
            <> 🔍 Run Institutional Research</>
          )}
        </button>
      </form>

      {/* Suggestions */}
      {!loading && (
        <div style={{ marginTop: 16, display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
          {SUGGESTIONS.map(s => (
            <motion.button
              key={s}
              whileHover={{ scale: 1.06, borderColor: 'var(--accent)' }}
              whileTap={{ scale: 0.95 }}
              onClick={() => { setTicker(s); inputRef.current?.focus(); }}
              style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                borderRadius: 6, padding: '4px 12px',
                fontFamily: 'var(--font-mono)', fontSize: 12,
                color: 'var(--text-secondary)', cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {s}
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Error card ─────────────────────────────────────────────── */
function ErrorCard({ message, onDismiss }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="card"
      style={{
        maxWidth: 540, margin: '24px auto',
        background: 'var(--red-dim)', borderColor: 'var(--red-border)',
        textAlign: 'center', padding: 32,
      }}
    >
      <p style={{ fontSize: 40, marginBottom: 12 }}>⚠️</p>
      <p style={{ fontSize: 16, fontWeight: 600, color: 'var(--red)', marginBottom: 8 }}>Research Failed</p>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>{message}</p>
      <button className="btn btn-ghost" onClick={onDismiss}>← Try Again</button>
    </motion.div>
  );
}

/* ── Main App ───────────────────────────────────────────────── */
export default function App() {
  const [state, setState] = useState('idle'); // idle | loading | done | error
  const [progress, setProgress] = useState({ phase: 'BOOT', message: '', step: 0 });
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('research'); // research | history
  const mainRef = useRef(null);

  const runResearch = useCallback(async (ticker) => {
    setState('loading');
    setError('');
    setReport(null);
    setProgress({ phase: 'BOOT', message: `Initialising ARA-1 for ${ticker}…`, step: 0 });

    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.event === 'status') {
              setProgress({
                phase: data.phase,
                message: data.message,
                step: phaseToStep(data.phase),
              });
            } else if (data.event === 'complete') {
              setReport(data.report);
              setState('done');
              // Scroll to report
              setTimeout(() => {
                mainRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }, 300);
            } else if (data.event === 'error') {
              setError(data.message);
              setState('error');
            }
          } catch {
            // skip malformed line
          }
        }
      }
    } catch (e) {
      setError(e.message || 'Connection failed. Is the server running?');
      setState('error');
    }
  }, []);

  const reset = () => {
    setState('idle');
    setReport(null);
    setError('');
  };

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <ParticleBackground />

      {/* Main content */}
      <div style={{ position: 'relative', zIndex: 1 }}>

        {/* Navigation */}
        <nav style={{
          position: 'sticky', top: 0, zIndex: 100,
          background: 'rgba(6, 11, 20, 0.85)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid var(--border)',
          padding: '0 24px',
        }}>
          <div style={{
            maxWidth: 1000, margin: '0 auto',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            height: 60,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 20 }}>📈</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>
                ARA-1
              </span>
              <span style={{ fontSize: 11, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>v2.0</span>
            </div>

            <div style={{ display: 'flex', gap: 4 }}>
              {['research', 'history'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    background: activeTab === tab ? 'var(--accent-dim)' : 'none',
                    border: '1px solid',
                    borderColor: activeTab === tab ? 'var(--accent-border)' : 'transparent',
                    borderRadius: 8, padding: '6px 16px',
                    color: activeTab === tab ? 'var(--accent)' : 'var(--text-secondary)',
                    cursor: 'pointer', fontSize: 13, fontWeight: 500,
                    transition: 'all 0.2s',
                    textTransform: 'capitalize',
                  }}
                >
                  {tab === 'research' ? '🔍 Research' : '📋 History'}
                </button>
              ))}
            </div>

            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              OODA · LangGraph · Groq
            </div>
          </div>
        </nav>

        {/* Tab: Research */}
        <AnimatePresence mode="wait">
          {activeTab === 'research' && (
            <motion.div
              key="research"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <HeroHeader />

              {/* Search (always visible when idle/error) */}
              <AnimatePresence>
                {(state === 'idle' || state === 'error') && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <SearchBox onSubmit={runResearch} loading={false} />
                  </motion.div>
                )}
                {state === 'loading' && (
                  <div style={{ padding: '40px 20px' }}>
                    <SearchBox onSubmit={() => {}} loading={true} />
                  </div>
                )}
              </AnimatePresence>

              {/* Progress */}
              <AnimatePresence>
                {state === 'loading' && (
                  <motion.div style={{ padding: '20px' }}>
                    <ResearchProgress
                      phase={progress.phase}
                      message={progress.message}
                      currentStep={progress.step}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Error */}
              <AnimatePresence>
                {state === 'error' && (
                  <motion.div style={{ padding: '0 20px' }}>
                    <ErrorCard message={error} onDismiss={reset} />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Report */}
              <AnimatePresence>
                {state === 'done' && report && (
                  <motion.div
                    ref={mainRef}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    style={{ padding: '40px 20px' }}
                  >
                    {/* Back button */}
                    <div style={{ maxWidth: 880, margin: '0 auto 24px' }}>
                      <button className="btn btn-ghost" onClick={reset} style={{ fontSize: 13 }}>
                        ← Run New Research
                      </button>
                    </div>
                    <ResearchReport report={report} />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Bottom padding */}
              <div style={{ height: 80 }} />
            </motion.div>
          )}

          {/* Tab: History */}
          {activeTab === 'history' && (
            <motion.div
              key="history"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ padding: '40px 20px', maxWidth: 800, margin: '0 auto' }}
            >
              <ReportsHistory onSelect={(r) => {
                setReport(r);
                setState('done');
                setActiveTab('research');
                setTimeout(() => {
                  mainRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 300);
              }} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <footer style={{
          textAlign: 'center', padding: '20px',
          borderTop: '1px solid var(--border)',
          color: 'var(--text-muted)', fontSize: 12,
          fontFamily: 'var(--font-mono)',
        }}>
          ARA-1 · Autonomous Financial Research Agent v2.0 · Not financial advice
        </footer>
      </div>
    </div>
  );
}

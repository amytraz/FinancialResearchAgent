import { motion, useSpring, useTransform, animate } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';

/* ── Animated counter ─────────────────────────────────────── */
function AnimatedNumber({ value, prefix = '', suffix = '', decimals = 2 }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const ctrl = { val: 0 };
    gsap.to(ctrl, {
      val: value,
      duration: 1.8,
      ease: 'power3.out',
      onUpdate() { setDisplay(ctrl.val); },
    });
  }, [value]);
  if (value === null || value === undefined) return <span>N/A</span>;
  return <span>{prefix}{display.toFixed(decimals)}{suffix}</span>;
}

/* ── MoS Gauge ─────────────────────────────────────────────── */
function MoSGauge({ mos }) {
  const barRef = useRef(null);
  // -100% to +100%, centre = 50%
  const pct = Math.max(0, Math.min(100, ((mos + 100) / 200) * 100));
  const isPositive = mos > 0;
  const color = mos > 20 ? 'var(--green)' : mos < -20 ? 'var(--red)' : 'var(--yellow)';

  useEffect(() => {
    if (barRef.current) {
      gsap.fromTo(barRef.current, { scaleX: 0 }, { scaleX: 1, duration: 1.5, ease: 'power3.out', transformOrigin: '0 50%' });
    }
  }, [mos]);

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Overvalued ← Margin of Safety → Undervalued</span>
        <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color, fontWeight: 700 }}>
          {mos > 0 ? '+' : ''}{mos.toFixed(1)}%
        </span>
      </div>
      <div style={{ position: 'relative', height: 8, background: 'var(--bg-surface)', borderRadius: 4, overflow: 'visible' }}>
        {/* Track gradient */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: 4, overflow: 'hidden',
          background: 'linear-gradient(to right, rgba(255,71,87,0.3) 0%, rgba(255,184,0,0.2) 50%, rgba(0,255,136,0.3) 100%)',
        }} />
        {/* Midline */}
        <div style={{ position: 'absolute', left: '50%', top: -2, bottom: -2, width: 1, background: 'rgba(255,255,255,0.2)' }} />
        {/* Indicator */}
        <motion.div
          initial={{ left: '50%' }}
          animate={{ left: `${pct}%` }}
          transition={{ duration: 1.5, ease: [0.25, 0.46, 0.45, 0.94] }}
          style={{
            position: 'absolute', top: -4, width: 16, height: 16,
            background: color, borderRadius: '50%', marginLeft: -8,
            boxShadow: `0 0 12px ${color}`,
            border: '2px solid var(--bg-base)',
          }}
        />
      </div>
    </div>
  );
}

/* ── Recommendation Block ─────────────────────────────────── */
function RecommendationBlock({ rec, conf, mos }) {
  const config = {
    BULLISH: { color: 'var(--green)', border: 'var(--green-border)', bg: 'var(--green-dim)', badge: '🟢 BULLISH', action: 'LONG' },
    BEARISH: { color: 'var(--red)',   border: 'var(--red-border)',   bg: 'var(--red-dim)',   badge: '🔴 BEARISH', action: 'AVOID / SHORT' },
    NEUTRAL: { color: 'var(--yellow)',border: 'var(--yellow-border)',bg: 'var(--yellow-dim)',badge: '🟡 NEUTRAL', action: 'HOLD / MONITOR' },
  }[rec] || { color: 'var(--accent)', border: 'var(--accent-border)', bg: 'var(--accent-dim)', badge: rec, action: '' };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
      className="recommendation-block"
      style={{ background: config.bg, borderColor: config.border }}
    >
      {/* Glow effect */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: 'inherit',
        background: `radial-gradient(circle at 50% 0%, ${config.color}20 0%, transparent 70%)`,
        pointerEvents: 'none',
      }} />

      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.2em', color: config.color, marginBottom: 12 }}>
        FINAL VERDICT
      </p>
      <motion.div
        style={{ fontSize: 40, fontWeight: 900, fontFamily: 'var(--font-display)', color: config.color, lineHeight: 1, marginBottom: 8 }}
        animate={{ textShadow: [`0 0 20px ${config.color}`, `0 0 40px ${config.color}`, `0 0 20px ${config.color}`] }}
        transition={{ repeat: Infinity, duration: 3 }}
      >
        {config.badge}
      </motion.div>
      <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginBottom: 16, letterSpacing: '0.08em' }}>
        [{config.action}]
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <span className={`badge badge-${rec.toLowerCase()}`}>Confidence: {conf}</span>
      </div>

      <MoSGauge mos={mos} />
    </motion.div>
  );
}

/* ── Metric Row ───────────────────────────────────────────── */
function MetricRow({ label, value, prefix = '', suffix = '', highlight = false, index = 0 }) {
  return (
    <motion.div
      className="metric-row"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
    >
      <span className="metric-label">{label}</span>
      <span className="metric-value" style={{ color: highlight ? 'var(--accent)' : undefined }}>
        {value !== null && value !== undefined
          ? <AnimatedNumber value={value} prefix={prefix} suffix={suffix} />
          : 'N/A'
        }
      </span>
    </motion.div>
  );
}

/* ── Download PDF Button ──────────────────────────────────── */
function DownloadPDFButton({ reportJson }) {
  const [loading, setLoading] = useState(false);
  const btnRef = useRef(null);

  const handleDownload = async () => {
    setLoading(true);
    gsap.to(btnRef.current, { scale: 0.96, duration: 0.1, yoyo: true, repeat: 1 });
    try {
      const res = await fetch('/api/download-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_json: reportJson }),
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ARA1_${reportJson.ticker}_${reportJson.date}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      // Success animation
      gsap.fromTo(btnRef.current,
        { boxShadow: '0 0 0px rgba(0,255,136,0)' },
        { boxShadow: '0 0 30px rgba(0,255,136,0.5)', duration: 0.4, yoyo: true, repeat: 1 }
      );
    } catch (e) {
      alert('PDF download failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      ref={btnRef}
      className="btn btn-success"
      onClick={handleDownload}
      disabled={loading}
      id="download-pdf-btn"
      style={{ width: '100%', padding: '14px', fontSize: 15 }}
    >
      {loading ? (
        <>
          <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
            ⟳
          </motion.span>
          Generating PDF…
        </>
      ) : (
        <>📄 Download Institutional PDF Report</>
      )}
    </button>
  );
}

/* ── Main Report Component ────────────────────────────────── */
export default function ResearchReport({ report }) {
  const rj = report;
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      gsap.fromTo(containerRef.current,
        { opacity: 0, y: 40 },
        { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }
      );
    }
  }, []);

  const rec = (rj.recommendation || 'NEUTRAL').toUpperCase();
  const mos = rj.margin_of_safety_pct ?? 0;

  const metrics = [
    { label: 'Current Price',           value: rj.current_price,           prefix: '$', suffix: '',  highlight: true },
    { label: 'DCF Intrinsic Value',      value: rj.intrinsic_value_per_share,prefix: '$', suffix: ' (DCF)' },
    { label: 'P/E Ratio (TTM)',          value: rj.pe_ratio,                suffix: 'x' },
    { label: 'Forward P/E',             value: rj.forward_pe,              suffix: 'x' },
    { label: 'EPS (TTM)',               value: rj.eps_ttm,                 prefix: '$' },
    { label: 'Revenue (TTM)',           value: rj.revenue_b,               prefix: '$', suffix: 'B' },
    { label: 'Net Income (TTM)',        value: rj.net_income_b,            prefix: '$', suffix: 'B' },
    { label: 'Profit Margin',           value: rj.profit_margin_pct,       suffix: '%' },
    { label: 'Revenue Growth YoY',      value: rj.revenue_growth_pct,      suffix: '%' },
    { label: 'ROE',                     value: rj.roe_pct,                suffix: '%' },
    { label: 'Debt-to-Equity',          value: rj.debt_to_equity,          suffix: 'x' },
    { label: 'Beta',                    value: rj.beta },
    { label: 'Analyst Target',          value: rj.analyst_target_mean,     prefix: '$' },
    { label: 'Upside to Target',        value: rj.upside_pct,              suffix: '%' },
  ];

  return (
    <div ref={containerRef} style={{ maxWidth: 880, margin: '0 auto' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 32, flexWrap: 'wrap', gap: 16,
        }}
      >
        <div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)', letterSpacing: '0.15em', marginBottom: 4 }}>
            RESEARCH COMPLETE · {rj.date}
          </p>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 38, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
            {rj.ticker}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
            ARA-1 Autonomous Research Agent v2.0
          </p>
        </div>
        {rj.enforced_override && (
          <div style={{
            background: 'rgba(255,184,0,0.1)', border: '1px solid rgba(255,184,0,0.3)',
            borderRadius: 8, padding: '8px 14px', fontSize: 12, color: 'var(--yellow)',
          }}>
            ⚠️ Rule Engine Override Applied
          </div>
        )}
      </motion.div>

      {/* Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>

        {/* Recommendation */}
        <div style={{ gridColumn: '1 / -1' }}>
          <RecommendationBlock rec={rec} conf={rj.confidence} mos={mos} />
        </div>

        {/* Executive Summary */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{ gridColumn: '1 / -1' }}
        >
          <div className="section-title">Executive Summary</div>
          <p style={{ fontSize: 15, color: 'var(--text-primary)', lineHeight: 1.8 }}>{rj.executive_summary}</p>
        </motion.div>

        {/* Financial Metrics */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          style={{ gridColumn: '1 / -1' }}
        >
          <div className="section-title">Financial Metrics</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 32px' }}>
            {metrics.map((m, i) => (
              <MetricRow key={m.label} {...m} index={i} />
            ))}
          </div>
        </motion.div>

        {/* Investment Thesis */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{ gridColumn: '1 / -1' }}
        >
          <div className="section-title">Investment Thesis</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {rj.bull_case && (
              <div className="thesis-box thesis-bull">
                <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--green)', marginBottom: 8, letterSpacing: '0.05em' }}>
                  🟢 BULL CASE
                </p>
                <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.7 }}>{rj.bull_case}</p>
              </div>
            )}
            {rj.bear_case && (
              <div className="thesis-box thesis-bear">
                <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--red)', marginBottom: 8, letterSpacing: '0.05em' }}>
                  🔴 BEAR CASE
                </p>
                <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.7 }}>{rj.bear_case}</p>
              </div>
            )}
          </div>
          {rj.rationale && (
            <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--accent-dim)', borderRadius: 8, borderLeft: '3px solid var(--accent)' }}>
              <p style={{ fontSize: 13, color: 'var(--text-primary)', fontStyle: 'italic' }}>
                💡 {rj.rationale}
              </p>
            </div>
          )}
        </motion.div>

        {/* Risks */}
        {rj.risks && rj.risks.length > 0 && (
          <motion.div
            className="card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <div className="section-title">Risk Assessment</div>
            {rj.risks.map((r, i) => (
              <div key={i} className="risk-item">
                <span style={{ fontSize: 12 }}>⚠</span>
                <span>{r}</span>
              </div>
            ))}
          </motion.div>
        )}

        {/* Data Warnings */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="section-title">Data Quality</div>
          {rj.data_warnings && rj.data_warnings.length > 0 ? (
            rj.data_warnings.map((w, i) => (
              <div key={i} className="warning-item">
                <span style={{ fontSize: 12 }}>⚠</span>
                <span style={{ fontSize: 12 }}>{w}</span>
              </div>
            ))
          ) : (
            <p style={{ color: 'var(--green)', fontSize: 14 }}>✅ No data quality anomalies detected</p>
          )}
        </motion.div>

        {/* Data Sources */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          style={{ gridColumn: '1 / -1' }}
        >
          <div className="section-title">Data Sources</div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {(rj.data_sources || []).map((s, i) => (
              <span key={i} style={{
                padding: '4px 12px', background: 'var(--bg-surface)',
                border: '1px solid var(--border)', borderRadius: 20,
                fontSize: 12, color: 'var(--text-secondary)',
              }}>
                {s}
              </span>
            ))}
          </div>
        </motion.div>

        {/* PDF Download */}
        <motion.div
          className="card glow-border"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          style={{ gridColumn: '1 / -1', background: 'var(--bg-elevated)' }}
        >
          <div className="section-title">Export Report</div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Download a professional multi-page institutional PDF report including all sections, metrics tables, and investment thesis.
          </p>
          <DownloadPDFButton reportJson={rj} />
        </motion.div>
      </div>
    </div>
  );
}

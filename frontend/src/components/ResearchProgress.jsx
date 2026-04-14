import { motion, AnimatePresence } from 'framer-motion';
import { gsap } from 'gsap';
import { useEffect, useRef } from 'react';

const PHASES = [
  { id: 'BOOT',    label: 'Initialising',          icon: '⚙️',  step: 0 },
  { id: 'BOOT2',   label: 'Agent Ready',            icon: '🤖',  step: 1 },
  { id: 'OBSERVE', label: 'Collecting Data',        icon: '📡',  step: 2 },
  { id: 'ORIENT',  label: 'Validating Metrics',     icon: '🔬',  step: 3 },
  { id: 'DECIDE',  label: 'Synthesising Report',    icon: '🧠',  step: 4 },
  { id: 'ACT',     label: 'Enforcing Rules',        icon: '⚖️',  step: 5 },
];

function OODAOrb({ phase }) {
  const phases = ['OBSERVE', 'ORIENT', 'DECIDE', 'ACT'];
  const current = phases.indexOf(phase);

  return (
    <div style={{ position: 'relative', width: 120, height: 120, margin: '0 auto 24px' }}>
      <svg width="120" height="120" viewBox="0 0 120 120">
        {phases.map((p, i) => {
          const angle = (i * 90 - 90) * (Math.PI / 180);
          const cx = 60 + 44 * Math.cos(angle);
          const cy = 60 + 44 * Math.sin(angle);
          const isDone = i < current;
          const isActive = i === current;
          return (
            <g key={p}>
              <circle
                cx={cx} cy={cy} r={isActive ? 10 : 7}
                fill={isDone ? '#00FF88' : isActive ? '#00D4FF' : 'rgba(255,255,255,0.1)'}
                style={{ transition: 'all 0.5s' }}
              />
              {isActive && (
                <circle cx={cx} cy={cy} r={14} fill="none" stroke="#00D4FF" strokeWidth="1.5"
                  strokeDasharray="4 4" style={{ animation: 'spin-slow 4s linear infinite', transformOrigin: `${cx}px ${cy}px` }} />
              )}
              <text x={cx} y={cy + 24} textAnchor="middle" fontSize="9" fill={isActive ? '#00D4FF' : '#484F58'}
                fontFamily="'JetBrains Mono', monospace">{p.slice(0,3)}</text>
            </g>
          );
        })}
        {/* Centre */}
        <circle cx="60" cy="60" r="16" fill="rgba(0,212,255,0.08)" stroke="rgba(0,212,255,0.3)" strokeWidth="1" />
        <text x="60" y="56" textAnchor="middle" fontSize="8" fill="#8B949E" fontFamily="'JetBrains Mono',monospace">ARA-1</text>
        <text x="60" y="67" textAnchor="middle" fontSize="7" fill="#00D4FF" fontFamily="'JetBrains Mono',monospace">v2.0</text>
        {/* Connectors */}
        {phases.map((_, i) => {
          const a1 = (i * 90 - 90) * (Math.PI / 180);
          const a2 = ((i + 1) * 90 - 90) * (Math.PI / 180);
          return (
            <line key={`l${i}`}
              x1={60 + 44 * Math.cos(a1)} y1={60 + 44 * Math.sin(a1)}
              x2={60 + 44 * Math.cos(a2)} y2={60 + 44 * Math.sin(a2)}
              stroke="rgba(255,255,255,0.07)" strokeWidth="1"
            />
          );
        })}
      </svg>
    </div>
  );
}

export default function ResearchProgress({ phase, message, currentStep }) {
  const barRef = useRef(null);

  const steps = [
    { label: 'Agent Boot',          phase: 'BOOT' },
    { label: 'Graph Compiled',      phase: 'BOOT2' },
    { label: 'Data Collection',     phase: 'OBSERVE' },
    { label: 'Validation',          phase: 'ORIENT' },
    { label: 'LLM Synthesis',       phase: 'DECIDE' },
    { label: 'Rule Enforcement',    phase: 'ACT' },
  ];

  const progress = ((currentStep + 1) / steps.length) * 100;

  useEffect(() => {
    if (barRef.current) {
      gsap.to(barRef.current, {
        width: `${progress}%`,
        duration: 0.8,
        ease: 'power2.out',
      });
    }
  }, [progress]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -20 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="card"
      style={{ maxWidth: 540, margin: '0 auto', padding: '36px 32px' }}
    >
      <OODAOrb phase={phase} />

      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)', letterSpacing: '0.15em', marginBottom: 8 }}>
          OODA LOOP · ACTIVE
        </p>
        <motion.h3
          key={phase}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}
        >
          {phase === 'OBSERVE' ? 'Observing Markets' :
           phase === 'ORIENT'  ? 'Orienting Data' :
           phase === 'DECIDE'  ? 'Deciding Thesis' :
           phase === 'ACT'     ? 'Acting on Rules' : 'Starting Agent…'}
        </motion.h3>
        <motion.p
          key={message}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}
        >
          {message}
        </motion.p>
      </div>

      {/* Progress bar */}
      <div style={{ marginBottom: 24 }}>
        <div className="mos-bar-track" style={{ height: 4, marginBottom: 8 }}>
          <div
            ref={barRef}
            className="mos-bar-fill"
            style={{ width: '0%', background: 'linear-gradient(90deg, var(--accent), #0096FF)' }}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {Math.round(progress)}%
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Step {currentStep + 1} / {steps.length}
          </span>
        </div>
      </div>

      {/* Step list */}
      <div>
        {steps.map((s, i) => {
          const isDone = i < currentStep;
          const isActive = i === currentStep;
          return (
            <motion.div
              key={s.label}
              className="step-item"
              animate={{ opacity: isDone ? 0.6 : 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className={`step-dot ${isActive ? 'active' : isDone ? 'done' : 'pending'}`} />
              <div>
                <p style={{
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'var(--text-primary)' : isDone ? 'var(--green)' : 'var(--text-muted)',
                  transition: 'color 0.3s',
                }}>
                  {isDone ? '✓ ' : ''}{s.label}
                </p>
              </div>
              {isActive && (
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}
                >
                  RUNNING
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}

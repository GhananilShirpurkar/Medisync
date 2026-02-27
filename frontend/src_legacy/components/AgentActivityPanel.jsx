import { useState, useRef, useEffect } from 'react';
import { useTraceStream } from '../hooks/useTraceStream';

// ─── Agent metadata ────────────────────────────────────────────────────────
const AGENT_META = {
  'API Gateway':      { icon: '⚡', color: '#6366f1' },
  'Identity Agent':   { icon: '🪪', color: '#f59e0b' },
  'Front Desk Agent': { icon: '🎯', color: '#3b82f6' },
  'Medical Agent':    { icon: '⚕️', color: '#10b981' },
  'Inventory Agent':  { icon: '📦', color: '#14b8a6' },
  'Fulfillment Agent':{ icon: '✅', color: '#22c55e' },
  'Notification Agent':{ icon: '📱', color: '#ec4899' },
};

const ACTION_ICON = {
  thinking:  '🧠',
  tool_use:  '🛠️',
  decision:  '🤔',
  response:  '🗣️',
  error:     '❌',
  event:     '⚡',
};

const STATUS_STYLE = {
  started:   { dot: '#60a5fa', label: 'Running',   pulse: true  },
  running:   { dot: '#60a5fa', label: 'Running',   pulse: true  },
  completed: { dot: '#4ade80', label: 'Done',      pulse: false },
  failed:    { dot: '#f87171', label: 'Error',     pulse: false },
};

// ─── Sub-components ────────────────────────────────────────────────────────

function StatusDot({ status }) {
  const s = STATUS_STYLE[status] || STATUS_STYLE.started;
  return (
    <span style={{
      display: 'inline-block',
      width: 8, height: 8,
      borderRadius: '50%',
      background: s.dot,
      boxShadow: s.pulse ? `0 0 0 2px ${s.dot}44` : 'none',
      animation: s.pulse ? 'pulse 1.4s ease-in-out infinite' : 'none',
      flexShrink: 0,
    }} />
  );
}

function TraceCard({ event, index }) {
  const [expanded, setExpanded] = useState(false);
  const meta = AGENT_META[event.agent] || { icon: '🤖', color: '#94a3b8' };
  const time = new Date(event.timestamp).toLocaleTimeString([], { timeStyle: 'medium' });
  const hasDetails = event.details && Object.keys(event.details).length > 0;

  return (
    <div style={{
      display: 'flex',
      gap: 10,
      opacity: event.status === 'completed' ? 0.85 : 1,
      animation: 'fadeSlideIn 0.25s ease',
    }}>
      {/* Timeline spine */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 28, flexShrink: 0 }}>
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: meta.color + '22',
          border: `1.5px solid ${meta.color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, flexShrink: 0,
        }}>
          {meta.icon}
        </div>
        <div style={{ flex: 1, width: 1.5, background: '#1e293b', minHeight: 8 }} />
      </div>

      {/* Card body */}
      <div style={{
        flex: 1, marginBottom: 8,
        background: '#0f172a',
        border: `1px solid ${event.status === 'failed' ? '#ef4444' : '#1e293b'}`,
        borderRadius: 10,
        overflow: 'hidden',
        fontSize: 12,
      }}>
        {/* Header row */}
        <button
          onClick={() => hasDetails && setExpanded(v => !v)}
          style={{
            width: '100%', textAlign: 'left',
            padding: '8px 12px',
            background: 'transparent',
            border: 'none',
            cursor: hasDetails ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          <StatusDot status={event.status} />
          <span style={{ color: meta.color, fontWeight: 600, fontSize: 11 }}>{event.agent}</span>
          <span style={{ color: '#64748b', margin: '0 2px' }}>·</span>
          <span style={{ color: '#cbd5e1', flex: 1 }}>
            {ACTION_ICON[event.type]} {event.step}
          </span>
          <span style={{ color: '#475569', fontSize: 10, whiteSpace: 'nowrap', marginLeft: 4 }}>{time}</span>
          {hasDetails && (
            <span style={{ color: '#475569', fontSize: 10 }}>{expanded ? '▲' : '▼'}</span>
          )}
        </button>

        {/* Expandable payload */}
        {expanded && hasDetails && (
          <div style={{ padding: '0 12px 10px' }}>
            <pre style={{
              margin: 0, padding: '8px 10px',
              background: '#020617',
              borderRadius: 6,
              color: '#7dd3fc',
              fontSize: 10.5,
              lineHeight: 1.6,
              overflowX: 'auto',
              maxHeight: 200,
              overflowY: 'auto',
            }}>
              {JSON.stringify(event.details, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

function ConnectionBadge({ connected }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 99,
      background: connected ? '#052e16' : '#1c0909',
      border: `1px solid ${connected ? '#16a34a' : '#7f1d1d'}`,
      fontSize: 11, fontWeight: 600,
      color: connected ? '#4ade80' : '#f87171',
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: connected ? '#4ade80' : '#f87171',
        display: 'inline-block',
        animation: connected ? 'pulse 1.4s ease-in-out infinite' : 'none',
      }} />
      {connected ? 'LIVE' : 'DISCONNECTED'}
    </div>
  );
}

// ─── Main Panel ────────────────────────────────────────────────────────────

export default function AgentActivityPanel({ sessionId }) {
  const { events, connected, clearEvents } = useTraceStream(sessionId);
  const bottomRef = useRef(null);
  const containerRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll unless user scrolled up
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, autoScroll]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setAutoScroll(atBottom);
  };

  const activeAgent = events.length > 0 ? events[events.length - 1]?.agent : null;

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      width: '100%', height: '100%',
      background: '#020617',
      borderLeft: '1px solid #1e293b',
      fontFamily: '"Inter", "SF Mono", monospace',
      color: '#e2e8f0',
    }} aria-label="Agent Activity Panel">
      {/* ── Header ── */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid #1e293b',
        display: 'flex', alignItems: 'center', gap: 10,
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 18 }}>🖥️</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#f1f5f9' }}>Agent's Computer</div>
          <div style={{ fontSize: 10, color: '#475569', marginTop: 1 }}>
            {activeAgent ? `Active: ${activeAgent}` : 'Idle — waiting for request'}
          </div>
        </div>
        <ConnectionBadge connected={connected} />
        <button
          onClick={clearEvents}
          title="Clear trace log"
          style={{
            background: 'none', border: '1px solid #1e293b',
            color: '#475569', borderRadius: 6,
            padding: '3px 8px', cursor: 'pointer', fontSize: 11,
          }}
        >
          Clear
        </button>
      </div>

      {/* ── TODO / Active Step Banner ── */}
      {events.some(e => e.status === 'started' || e.status === 'running') && (
        <div style={{
          padding: '8px 16px',
          background: '#0c1a3a',
          borderBottom: '1px solid #1e2d5a',
          fontSize: 11.5, color: '#93c5fd',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⚙️</span>
          <span>
            <b>{activeAgent}</b> is working &mdash; {events[events.length - 1]?.step}
          </span>
        </div>
      )}

      {/* ── Trace Timeline ── */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '14px 14px 4px',
        }}
      >
        {events.length === 0 ? (
          <div style={{
            height: '100%', display: 'flex',
            flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            gap: 12, color: '#334155', textAlign: 'center',
          }}>
            <div style={{ fontSize: 40 }}>🕵️</div>
            <p style={{ fontSize: 13, fontWeight: 600 }}>No agent activity yet</p>
            <p style={{ fontSize: 11, maxWidth: 200 }}>
              Send a message in the chat to watch agents work in real-time.
            </p>
          </div>
        ) : (
          events.map((evt, i) => <TraceCard key={evt.id || i} event={evt} index={i} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Footer: Stats Bar ── */}
      <div style={{
        padding: '8px 16px',
        borderTop: '1px solid #1e293b',
        display: 'flex', gap: 16,
        fontSize: 10.5, color: '#475569',
        flexShrink: 0,
      }}>
        <span>📊 {events.length} steps traced</span>
        <span>✅ {events.filter(e => e.status === 'completed').length} done</span>
        <span>❌ {events.filter(e => e.status === 'failed').length} errors</span>
        {!autoScroll && (
          <button
            onClick={() => { setAutoScroll(true); bottomRef.current?.scrollIntoView({behavior:'smooth'}); }}
            style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: 10.5 }}
          >
            ↓ Jump to latest
          </button>
        )}
      </div>

      {/* ── Animation keyframes ── */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

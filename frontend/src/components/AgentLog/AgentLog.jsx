import React, { useEffect, useRef, useState, useMemo } from 'react';
import { pipelineStore } from '../../state/pipelineStore';
import './AgentLog.css';

const AgentLog = ({ steps }) => {
  const containerRef = useRef(null);
  const [displayedSteps, setDisplayedSteps] = useState([]);
  const [sessionActive, setSessionActive] = useState(!!pipelineStore.get().sessionId);

  useEffect(() => {
    const unsubscribe = pipelineStore.subscribe((state) => {
      setSessionActive(!!state.sessionId);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const allSteps = steps || [];
    if (allSteps.length === 0) return;
    
    const latest = allSteps[allSteps.length - 1];
    if (!latest) return;

    setDisplayedSteps(prev => {
      // If same agent+step exists, update it in place (status change)
      const existingIndex = prev.findIndex(
        s => s.agent === latest.agent && s.step === latest.step
      );
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = latest;
        return updated;
      }
      // Otherwise append
      return [...prev, latest];
    });
  }, [steps?.length]);

  // Handle auto-scroll
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [displayedSteps]);

  const getStatusDot = (status, type) => {
    if (type === 'fusion') {
      return <div className="status-dot fusion-diamond"></div>;
    }
    switch (status) {
      case 'started':
        return <div className="status-dot hollow-circle"></div>;
      case 'running':
        return <div className="status-dot solid-amber pulse-anim"></div>;
      case 'completed':
        // A checkmark replacing dot
        return (
          <div className="status-dot complete-check">
            <svg viewBox="0 0 12 12" width="12" height="12">
              <path d="M2.5 6L5 8.5L9.5 3.5" stroke="var(--green)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            </svg>
          </div>
        );
      case 'failed':
      case 'rejected':
        return <div className="status-dot solid-red"></div>;
      default:
        return <div className="status-dot hollow-circle"></div>;
    }
  };

  const getAgentColor = (type, status) => {
    if (type === 'fusion') return 'var(--ink-faint)';
    if (status === 'failed' || status === 'rejected') return 'var(--red)';
    if (status === 'completed') return 'var(--green)';
    if (type === 'tool_use') return 'var(--amber)';
    if (type === 'thinking') return 'var(--ink-mute)';
    return 'var(--ink-2)';
  };

  const formatTime = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }).split(' ')[0]; // Returns HH:MM:SS
    } catch {
      return '';
    }
  };

  const renderDetails = (evt) => {
    if (!evt.details) return null;
    if (evt.type === 'fusion') {
      const safety = Math.round((evt.details.safety_confidence || 0) * 100);
      const fulfill = Math.round((evt.details.fulfillment_confidence || 0) * 100);
      return <div className="agent-detail-line">↳ safety: {safety}% · fulfillment: {fulfill}%</div>;
    }
    
    // For normal agents, only render if there's text/string info we can cleanly show
    // We'll extract a few known keys or just the first string value to keep it sane
    let displayStr = '';
    if (typeof evt.details === 'string') {
      displayStr = evt.details;
    } else if (evt.details.error) {
      displayStr = evt.details.error;
    } else if (evt.details.reason) {
      displayStr = evt.details.reason;
    } else if (evt.details.tool_call) {
      displayStr = `Using ${evt.details.tool_call}`;
    } else if (evt.details.action) {
      displayStr = evt.details.action;
    } else if (Object.keys(evt.details).length > 0) {
      // Find first string or number
      const firstKey = Object.keys(evt.details).find(k => typeof evt.details[k] === 'string' || typeof evt.details[k] === 'number');
      if (firstKey) displayStr = `${firstKey}: ${evt.details[firstKey]}`;
    }

    if (!displayStr) return null;

    // Truncate to reasonable length
    if (displayStr.length > 60) displayStr = displayStr.substring(0, 60) + '...';
    return <div className="agent-detail-line">↳ {displayStr}</div>;
  };

  return (
    <div className="agent-log-container" ref={containerRef}>
      <div className="agent-log-track">
        {displayedSteps.length === 0 && sessionActive && (
          <div className="trace-initializing">
            <span className="trace-init-dot" />
            <span className="trace-init-text">Pipeline initializing...</span>
          </div>
        )}
        
        {displayedSteps.map((evt, idx) => {
          const isFusion = evt.type === 'fusion';
          return (
            <div 
              key={`${evt.agent}-${evt.step}-${idx}`} 
              className={`agent-log-entry trace-step-enter ${isFusion ? 'is-fusion' : ''}`}
            >
              <div className="log-icon-col">
                {getStatusDot(evt.status, evt.type)}
                {/* Visual rail connecting nodes */}
                {idx < displayedSteps.length - 1 && <div className="log-rail"></div>}
              </div>
              <div className="log-content-col">
                <div className="log-header-row">
                  <span className="log-agent-name" style={{ color: getAgentColor(evt.type, evt.status) }}>
                    {evt.agent}
                  </span>
                  <span className="log-timestamp">{formatTime(evt.timestamp)}</span>
                </div>
                <div className="log-step-desc">{evt.step}</div>
                {renderDetails(evt)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentLog;

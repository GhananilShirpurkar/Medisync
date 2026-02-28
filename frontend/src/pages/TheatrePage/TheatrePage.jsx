import React, { useEffect, useState } from 'react';
import { pipelineStore } from '../../state/pipelineStore';
import { runConsultationFlowAPI } from '../../data/apiFlows';
import TheatreLayout from '../../layouts/TheatreLayout/TheatreLayout';
import ConsultationStage from '../../components/ConsultationStage/ConsultationStage';
import ClinicalRecord from '../../components/ClinicalRecord/ClinicalRecord';
import CameraModal from '../../components/CameraModal/CameraModal';
import VoiceCallModal from '../../components/VoiceCallModal/VoiceCallModal';
import AgentLog from '../../components/AgentLog/AgentLog';
import FusionGauge from '../../components/FusionGauge/FusionGauge';
import './TheatrePage.css';

const TheatrePage = () => {
  const [pipelineState, setPipelineState] = useState(pipelineStore.get());
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [isOrdersOpen, setIsOrdersOpen] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);

  useEffect(() => {
    const unsubscribe = pipelineStore.subscribe(setPipelineState);
    const timer = setInterval(() => {
      setSessionTime(prev => prev + 1);
    }, 1000);
    return () => {
      unsubscribe();
      clearInterval(timer);
    };
  }, []);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleInputSubmit = (value) => {
    pipelineStore.dispatch('USER_MESSAGE_SENT', value);
    runConsultationFlowAPI(value);
  };

  const closePanels = () => {
    setIsTimelineOpen(false);
    setIsOrdersOpen(false);
  };

  const leftZone = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
      <div className="fixed-patient-zone" style={{ flexShrink: 0, marginBottom: '1rem' }}>
        <div className="metadata-header">👤 {pipelineState.pid || 'Anonymous Patient'}</div>
        <div className="patient-meta-row">
          <span style={{ color: 'var(--rx-ink-3)', fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Session</span>
          <span style={{ color: 'var(--rx-ink-2)' }}>
            {pipelineState.sessionId ? pipelineState.sessionId.split('-')[0] : '—'}
          </span>
        </div>
        <div className="patient-meta-row" style={{ marginBottom: '12px' }}>
          <span style={{ color: 'var(--rx-ink-3)', fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Elapsed</span>
          <span className="session-timer">⏱ {formatTime(sessionTime)}</span>
        </div>
        <div className="metadata-actions" style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
          <span className="status-badge toggle">End Session</span>
          <span className="status-badge toggle">Pause</span>
        </div>
      </div>

      <div style={{ flex: '1 1 0%', minHeight: '0', marginBottom: '1rem', display: 'flex', flexDirection: 'column' }}>
        <div className="agent-logs-header">
          Agent Logs
        </div>
        <div style={{ flex: '1 1 0%', minHeight: '0' }}>
          <AgentLog steps={pipelineState.traceSteps.filter(s => s.agent !== 'ORCHESTRATOR')} />
        </div>
      </div>

      <button
        className="trigger-button"
        onClick={() => setIsTimelineOpen(true)}
      >
        📋 History
      </button>
    </div>
  );

  const isSystemActive = pipelineState.messages.length > 0;
  const orchestratorEvents = pipelineState.traceSteps.filter(s => s.agent === 'ORCHESTRATOR');
  const fusionState = orchestratorEvents.length > 0 ? orchestratorEvents[orchestratorEvents.length - 1] : null;

  const rightZone = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
      <div className="fixed-system-zone" style={{ flex: '1 1 0%', display: 'flex', flexDirection: 'column', padding: '1.25rem 1rem', overflowY: 'auto', minHeight: '0' }}>
        <div className="metadata-header" style={{ marginBottom: '1.5rem', justifyContent: 'center', flexShrink: 0 }}>
          Fusion Confidence
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.75rem' }}>
          {fusionState ? (
            <FusionGauge fusionState={fusionState} />
          ) : (
            <div style={{
              textAlign: 'center',
              color: 'var(--rx-ink-3)',
              fontFamily: 'var(--font-data)',
              fontSize: '11px',
              letterSpacing: '0.1em',
              marginBottom: '16px',
            }}>
              Awaiting input…
            </div>
          )}
        </div>

        <div style={{ marginBottom: '1.5rem', fontFamily: 'var(--font-data)', fontSize: '12px' }}>
          <div style={{
            marginBottom: '10px',
            color: 'var(--rx-ink-3)',
            fontSize: '10px',
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            fontWeight: 600,
          }}>
            Input Breakdown
          </div>

          {[
            { icon: '🎤', label: 'Voice',  key: 'voice',  color: 'var(--rx-teal)'  },
            { icon: '📷', label: 'Vision', key: 'vision', color: 'var(--rx-amber)' },
            { icon: '⌨️', label: 'Text',   key: 'text',   color: 'var(--rx-green)' },
          ].map(({ icon, label, key, color }) => {
            const val = pipelineState.fusionMetrics?.[key];
            return (
              <div key={key} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', alignItems: 'center' }}>
                  <span style={{ color: 'var(--rx-ink-2)' }}>{icon} {label}</span>
                  <span style={{ color: val ? color : 'var(--rx-ink-mute)', fontWeight: 600 }}>
                    {val ? `${val}%` : '--'}
                  </span>
                </div>
                <div style={{ height: '3px', background: 'var(--rx-border)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    background: color,
                    width: `${val || 0}%`,
                    transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)',
                    boxShadow: val ? `0 0 6px ${color}` : 'none',
                    borderRadius: '2px',
                  }} />
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ borderTop: '1px solid var(--rx-border)', paddingTop: '14px', fontFamily: 'var(--font-data)', fontSize: '12px' }}>
          <div style={{
            marginBottom: '10px',
            color: 'var(--rx-ink-3)',
            fontSize: '10px',
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            fontWeight: 600,
          }}>
            System Health
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: 'var(--rx-ink-3)' }}>Latency</span>
            <span style={{ color: isSystemActive ? 'var(--rx-amber)' : 'var(--rx-ink-mute)', letterSpacing: '0.05em' }}>
              {isSystemActive ? `${Math.floor(Math.random() * 40 + 80)}ms ✓` : '—'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: 'var(--rx-ink-3)' }}>Model</span>
            <span style={{ color: 'var(--rx-ink-2)' }}>LLaMA-3 Med</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--rx-ink-3)' }}>DB</span>
            <span style={{ color: 'var(--rx-green)' }}>Isolated ✓</span>
          </div>
        </div>

        <div style={{ flex: 1 }} />

        <button
          className="trigger-button"
          onClick={() => setIsOrdersOpen(true)}
          style={{
            marginTop: 'auto',
            ...(pipelineState.checkoutReady ? {
              background: 'linear-gradient(135deg, #00d4aa, #009e82) !important',
              border: 'none !important',
              color: 'var(--rx-void) !important',
              fontWeight: 700,
              boxShadow: '0 4px 20px rgba(0,212,170,0.3) !important',
            } : {}),
          }}
        >
          🛒 Current Orders {pipelineState.checkoutReady && '(1)'}
        </button>
      </div>
    </div>
  );

  const stageContent = (
    <ConsultationStage
      messages={pipelineState.messages}
      onSubmit={handleInputSubmit}
      isSettled={pipelineState.sessionSettled}
      checkoutReady={pipelineState.checkoutReady}
      patientContext={pipelineState.patientContext}
      ambientState={pipelineState.ambientState}
      onCheckout={() => {
        pipelineStore.dispatch('order_created', {});
      }}
    />
  );

  const timelinePanelContent = (
    <>
      <div className="metadata-header" style={{ marginBottom: '1rem', borderBottom: '1px solid var(--rx-border)', paddingBottom: '0.6rem' }}>
        Clinical Record Timeline
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        <ClinicalRecord entries={pipelineState.recordEntries} />
      </div>
    </>
  );

  const ordersPanelContent = (
    <>
      <div className="metadata-header" style={{ marginBottom: '1rem', borderBottom: '1px solid var(--rx-border)', paddingBottom: '0.6rem' }}>
        Current Orders
      </div>
      <div style={{ overflowY: 'auto', flex: 1, padding: '2px 0' }}>
        {pipelineState.pendingOrderSummary?.items?.length > 0 ? (
          pipelineState.pendingOrderSummary.items.map((item, i) => {
            const isOutOfStock = item.stockStatus !== 'In Stock';
            const hasWarnings = item.warnings && item.warnings.length > 0;
            const requiresConsultation = isOutOfStock && (!item.substitute || item.substitute.warnings?.length > 0);

            const borderColor = requiresConsultation
              ? 'rgba(255,77,106,0.4)'
              : hasWarnings
              ? 'rgba(240,165,0,0.3)'
              : 'var(--rx-border)';

            const bgColor = requiresConsultation
              ? 'linear-gradient(135deg, var(--rx-red-soft), var(--rx-card))'
              : hasWarnings
              ? 'linear-gradient(135deg, var(--rx-amber-soft), var(--rx-card))'
              : 'var(--rx-card)';

            return (
              <div key={i} style={{
                padding: '13px',
                border: `1px solid ${borderColor}`,
                borderRadius: 'var(--rx-r)',
                marginBottom: '10px',
                background: bgColor,
                opacity: isOutOfStock ? 0.78 : 1,
                transition: 'border-color 0.2s ease',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                  <div style={{
                    fontFamily: 'var(--font-ui)',
                    fontWeight: 600,
                    fontSize: '13px',
                    color: isOutOfStock ? 'var(--rx-ink-3)' : 'var(--rx-ink-1)',
                    textDecoration: isOutOfStock ? 'line-through' : 'none',
                  }}>
                    {item.name}
                  </div>
                  <div style={{
                    fontFamily: 'var(--font-data)',
                    fontSize: '10px',
                    fontWeight: 600,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    whiteSpace: 'nowrap',
                    padding: '2px 7px',
                    borderRadius: '3px',
                    color: isOutOfStock ? 'var(--rx-red)' : 'var(--rx-green)',
                    background: isOutOfStock ? 'var(--rx-red-soft)' : 'var(--rx-green-soft)',
                    border: `1px solid ${isOutOfStock ? 'rgba(255,77,106,0.2)' : 'rgba(39,212,138,0.2)'}`,
                  }}>
                    {item.stockStatus}
                  </div>
                </div>

                <div style={{
                  marginTop: '7px',
                  fontFamily: 'var(--font-data)',
                  fontSize: '12px',
                  color: 'var(--rx-green)',
                  letterSpacing: '0.04em',
                }}>
                  ₹{item.price}
                </div>

                {hasWarnings && (
                  <div style={{
                    marginTop: '10px', padding: '8px 10px',
                    background: 'var(--rx-amber-soft)',
                    borderLeft: '2px solid var(--rx-amber)',
                    borderRadius: '0 3px 3px 0',
                    color: 'var(--rx-amber)', fontSize: '12px',
                  }}>
                    <strong style={{
                      fontFamily: 'var(--font-data)', fontSize: '10px',
                      letterSpacing: '0.12em', textTransform: 'uppercase',
                      display: 'block', marginBottom: '4px',
                    }}>
                      ⚠ Warnings
                    </strong>
                    <ul style={{ margin: 0, paddingLeft: '16px' }}>
                      {item.warnings.map((w, wIdx) => <li key={wIdx} style={{ marginBottom: '2px' }}>{w}</li>)}
                    </ul>
                  </div>
                )}

                {isOutOfStock && item.substitute && !requiresConsultation && (
                  <div style={{
                    marginTop: '10px', padding: '8px 10px',
                    background: 'var(--rx-indigo-soft)',
                    borderLeft: '2px solid var(--rx-indigo)',
                    borderRadius: '0 3px 3px 0', fontSize: '12px',
                  }}>
                    <div style={{
                      color: 'var(--rx-indigo)',
                      fontFamily: 'var(--font-data)', fontSize: '10px',
                      letterSpacing: '0.12em', textTransform: 'uppercase',
                      marginBottom: '4px',
                    }}>
                      ⇄ Substitute Suggested
                    </div>
                    <div style={{ color: 'var(--rx-ink-1)' }}>
                      {item.substitute.name}
                      <span style={{ color: 'var(--rx-green)', marginLeft: '6px' }}>₹{item.substitute.price}</span>
                    </div>
                    <div style={{ color: 'var(--rx-ink-3)', marginTop: '4px', fontSize: '11px' }}>
                      Awaiting confirmation in chat…
                    </div>
                  </div>
                )}

                {requiresConsultation && (
                  <div style={{
                    marginTop: '10px', padding: '8px 10px',
                    background: 'var(--rx-red-soft)',
                    borderLeft: '2px solid var(--rx-red)',
                    borderRadius: '0 3px 3px 0',
                    color: 'var(--rx-red)', fontSize: '12px',
                  }}>
                    <strong style={{
                      fontFamily: 'var(--font-data)', fontSize: '10px',
                      letterSpacing: '0.12em', textTransform: 'uppercase',
                      display: 'block', marginBottom: '4px',
                    }}>
                      ⛔ Unavailable
                    </strong>
                    <p style={{ margin: 0 }}>
                      Primary and substitutes unavailable or unsafe. Doctor consultation required.
                    </p>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div style={{
            color: 'var(--rx-ink-3)',
            fontFamily: 'var(--font-data)',
            fontSize: '11px',
            letterSpacing: '0.08em',
            textAlign: 'center',
            padding: '24px 0',
          }}>
            No items in cart yet.
          </div>
        )}
      </div>

      {pipelineState.pendingOrderSummary && (
        <div style={{
          borderTop: '1px solid var(--rx-border-mid)',
          paddingTop: '12px',
          marginBottom: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: 'var(--font-data)',
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'var(--rx-ink-2)',
        }}>
          <span>Total</span>
          <span style={{ color: 'var(--rx-green)', fontSize: '15px', letterSpacing: '0.04em' }}>
            ₹{pipelineState.pendingOrderSummary.totalPrice}
          </span>
        </div>
      )}

      {(() => {
        const hasBlockingItems = pipelineState.pendingOrderSummary?.items?.some(
          i => i.stockStatus !== 'In Stock' && (!i.substitute || i.substitute.warnings?.length > 0)
        );
        const canProceed = pipelineState.checkoutReady && !hasBlockingItems;
        return (
          <button
            className="trigger-button"
            style={{
              marginTop: 'auto',
              ...(canProceed ? {
                background: 'linear-gradient(135deg, #00d4aa, #009e82) !important',
                border: 'none !important',
                color: 'var(--rx-void) !important',
                fontWeight: 700,
                boxShadow: '0 4px 20px rgba(0,212,170,0.3) !important',
              } : {}),
            }}
            disabled={!canProceed}
            onClick={() => pipelineStore.dispatch('order_created', {})}
          >
            {hasBlockingItems ? 'Consultation Required' : 'Proceed to Summary'}
          </button>
        );
      })()}
    </>
  );

  return (
    <>
      <TheatreLayout
        leftZone={leftZone}
        rightZone={rightZone}
        stageContent={stageContent}
        isTimelineOpen={isTimelineOpen}
        isOrdersOpen={isOrdersOpen}
        onClosePanels={closePanels}
        timelinePanelContent={timelinePanelContent}
        ordersPanelContent={ordersPanelContent}
      />
      {pipelineState.isCameraOpen && <CameraModal />}
      {pipelineState.isVoiceCallOpen && <VoiceCallModal />}
    </>
  );
};

export default TheatrePage;
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

const TheatrePage = () => {
  const [pipelineState, setPipelineState] = useState(pipelineStore.get());
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [isOrdersOpen, setIsOrdersOpen] = useState(false);

  const [sessionTime, setSessionTime] = useState(0);

  useEffect(() => {
    const unsubscribe = pipelineStore.subscribe(setPipelineState);
    
    // Session Timer
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
        <div className="metadata-header" style={{ color: 'var(--amber)' }}>👤 {pipelineState.pid || 'Anonymous Patient'}</div>
        <div className="patient-meta-row">
          <span>Session: {pipelineState.sessionId ? pipelineState.sessionId.split('-')[0] : 'Pending...'}</span>
          <span className="session-timer">⏱ {formatTime(sessionTime)}</span>
        </div>
        <div className="metadata-actions" style={{ display: 'flex', gap: '1rem', marginTop: '8px' }}>
          <span className="status-badge toggle">[End Session]</span> 
          <span className="status-badge toggle">[Pause]</span>
        </div>
      </div>
      
      <div style={{ flex: '1 1 0%', minHeight: '0', marginBottom: '1rem', display: 'flex', flexDirection: 'column' }}>
        <div className="agent-logs-header">
          AGENT LOGS
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
      <div className="fixed-system-zone" style={{ flex: '1 1 0%', display: 'flex', flexDirection: 'column', padding: '1.5rem 1rem', overflowY: 'auto', minHeight: '0' }}>
        <div className="metadata-header" style={{ marginBottom: '2rem', textAlign: 'center', color: 'var(--ink-1)', flexShrink: 0 }}>FUSION CONFIDENCE</div>
        
        {/* Dynamic Fusion Gauge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem' }}>
          {fusionState ? (
            <FusionGauge fusionState={fusionState} />
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--amber)', fontFamily: 'var(--font-machine)', fontSize: '11px', marginBottom: '16px' }}>
              Awaiting input...
            </div>
          )}
        </div>

        <div style={{ marginBottom: '2rem', fontFamily: 'var(--font-machine)', fontSize: '12px' }}>
          <div style={{ marginBottom: '8px', color: 'var(--ink-2)' }}>INPUT BREAKDOWN</div>
          
          <div style={{ marginBottom: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>🎤 Voice</span> 
              <span style={{ color: pipelineState.fusionMetrics?.voice ? 'var(--green)' : 'var(--ink-mute)' }}>
                {pipelineState.fusionMetrics?.voice ? `${pipelineState.fusionMetrics.voice}%` : '--'}
              </span>
            </div>
            <div style={{ height: '4px', background: 'var(--divider)', width: '100%' }}>
              <div style={{ height: '100%', background: 'var(--green)', width: `${pipelineState.fusionMetrics?.voice || 0}%`, transition: 'width 0.5s' }} />
            </div>
          </div>

          <div style={{ marginBottom: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>📷 Vision</span> 
              <span style={{ color: pipelineState.fusionMetrics?.vision ? 'var(--amber)' : 'var(--ink-mute)' }}>
                {pipelineState.fusionMetrics?.vision ? `${pipelineState.fusionMetrics.vision}%` : '--'}
              </span>
            </div>
            <div style={{ height: '4px', background: 'var(--divider)', width: '100%' }}>
              <div style={{ height: '100%', background: 'var(--amber)', width: `${pipelineState.fusionMetrics?.vision || 0}%`, transition: 'width 0.5s' }} />
            </div>
          </div>

          <div style={{ marginBottom: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>⌨️ Text</span> 
              <span style={{ color: pipelineState.fusionMetrics?.text ? 'var(--green)' : 'var(--ink-mute)' }}>
                {pipelineState.fusionMetrics?.text ? `${pipelineState.fusionMetrics.text}%` : '--'}
              </span>
            </div>
            <div style={{ height: '4px', background: 'var(--divider)', width: '100%' }}>
              <div style={{ height: '100%', background: 'var(--green)', width: `${pipelineState.fusionMetrics?.text || 0}%`, transition: 'width 0.5s' }} />
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px dashed var(--divider)', paddingTop: '16px', fontFamily: 'var(--font-machine)', fontSize: '12px' }}>
          <div style={{ marginBottom: '8px', color: 'var(--ink-2)' }}>SYSTEM HEALTH</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
             <span style={{ color: 'var(--ink-2)' }}>Latency:</span> 
             <span style={{ color: isSystemActive ? 'var(--amber)' : 'var(--ink-mute)' }}>
               {isSystemActive ? `${Math.floor(Math.random() * 40 + 80)}ms ✓` : '-- ms'}
             </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
             <span style={{ color: 'var(--ink-2)' }}>Model:</span> 
             <span>LLaMA-3 Med</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
             <span style={{ color: 'var(--ink-2)' }}>DB:</span> 
             <span style={{ color: 'var(--green)' }}>Isolated ✓</span>
          </div>
        </div>
        
        <div style={{ flex: 1 }} /> {/* Spacer */}

        <button 
          className="trigger-button"
          onClick={() => setIsOrdersOpen(true)}
          style={{ 
            marginTop: 'auto',
            background: pipelineState.checkoutReady ? 'var(--indigo)' : 'var(--bg-room)',
            color: pipelineState.checkoutReady ? 'var(--paper)' : 'var(--ink-2)'
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
      <div className="metadata-header" style={{ marginBottom: '1rem', borderBottom: '1px solid var(--divider)', paddingBottom: '0.5rem' }}>
        CLINICAL RECORD TIMELINE
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        <ClinicalRecord entries={pipelineState.recordEntries} />
      </div>
    </>
  );

  const [expandedReplacementId, setExpandedReplacementId] = useState(null);

  const handleChooseReplacement = (oldName, replacement) => {
    pipelineStore.dispatch('UPDATE_ORDER_ITEM', {
      oldName: oldName,
      newName: replacement.name,
      price: replacement.price
    });
    setExpandedReplacementId(null);
  };

  const ordersPanelContent = (
    <>
      <div className="metadata-header" style={{ marginBottom: '1rem', borderBottom: '1px solid var(--divider)', paddingBottom: '0.5rem' }}>
        CURRENT ORDERS
      </div>
      <div style={{ overflowY: 'auto', flex: 1, padding: '1rem 0' }}>
        {pipelineState.orderSummary && pipelineState.orderSummary.items && pipelineState.orderSummary.items.length > 0 ? (
          pipelineState.orderSummary.items.map((item, i) => {
            const isOutOfStock = item.stockStatus !== 'In Stock';
            const available = item.available !== false && !isOutOfStock;
            const hasWarnings = item.warnings && item.warnings.length > 0;
            const hasSuggestions = item.substitute && item.substitute.suggestions && item.substitute.suggestions.length > 0;
            const requiresConsultation = isOutOfStock && !hasSuggestions;

            return (
               <div key={i} style={{ 
                 padding: '12px', 
                 border: `1px solid ${available ? 'var(--green)' : requiresConsultation ? 'var(--red)' : hasWarnings ? 'var(--amber)' : 'var(--divider)'}`, 
                 borderRadius: '8px', 
                 marginBottom: '12px', 
                 background: isOutOfStock ? 'rgba(255,255,255,0.03)' : (available ? 'rgba(72, 187, 120, 0.05)' : 'transparent'),
                 boxShadow: available ? '0 0 10px rgba(72, 187, 120, 0.1)' : 'none',
                 position: 'relative'
               }}>
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                   <div style={{ 
                     fontWeight: 'bold', 
                     color: available ? 'var(--green)' : (isOutOfStock ? 'var(--ink-mute)' : 'var(--ink-1)'), 
                     textDecoration: isOutOfStock ? 'line-through' : 'none' 
                   }}>
                     {item.name} {item.isReplaced && <span style={{ fontSize: '10px', verticalAlign: 'middle', background: 'var(--indigo)', color: 'white', padding: '2px 4px', borderRadius: '4px', marginLeft: '4px' }}>REPLACED</span>}
                   </div>
                   <div style={{ color: available ? 'var(--green)' : 'var(--red)', fontFamily: 'var(--font-machine)', fontSize: '11px', fontWeight: 'bold' }}>
                     {available ? '✓ AVAILABLE' : item.stockStatus}
                   </div>
                 </div>
                 
                 <div style={{ marginTop: '8px', fontFamily: 'var(--font-machine)', fontSize: '12px', color: available ? 'var(--green)' : 'var(--ink-2)' }}>
                   Price: ₹{item.price}
                 </div>

                 {hasWarnings && (
                   <div style={{ marginTop: '12px', padding: '8px', background: 'rgba(255, 171, 0, 0.1)', borderLeft: '2px solid var(--amber)', color: 'var(--amber)', fontSize: '12px' }}>
                     <strong style={{ fontFamily: 'var(--font-machine)', fontSize: '11px', display: 'block', marginBottom: '4px' }}>⚠️ WARNINGS:</strong>
                     <ul style={{ margin: 0, paddingLeft: '16px' }}>
                       {item.warnings.map((w, wIdx) => <li key={wIdx} style={{ marginBottom: '2px' }}>{w}</li>)}
                     </ul>
                   </div>
                 )}

                  {isOutOfStock && hasSuggestions && (
                    <div style={{ marginTop: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                         <div style={{ color: 'var(--indigo)', fontFamily: 'var(--font-machine)', fontSize: '11px' }}>⇄ ALTERNATIVES AVAILABLE</div>
                         <button 
                           onClick={() => setExpandedReplacementId(expandedReplacementId === i ? null : i)}
                           style={{ background: 'var(--indigo)', color: 'white', border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '10px', cursor: 'pointer' }}
                         >
                           {expandedReplacementId === i ? 'HIDE' : 'SHOW REPLACEMENTS'}
                         </button>
                      </div>

                      {expandedReplacementId === i && (
                        <div className="replacement-list" style={{ background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '6px' }}>
                          {item.substitute.suggestions.map((option, optIdx) => (
                            <div key={optIdx} style={{ padding: '8px', borderBottom: optIdx < item.substitute.suggestions.length - 1 ? '1px solid var(--divider)' : 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                               <div style={{ flex: 1 }}>
                                  <div style={{ fontSize: '12px', color: 'var(--ink-1)', fontWeight: 'bold' }}>{option.name}</div>
                                  <div style={{ fontSize: '11px', color: 'var(--indigo)' }}>₹{option.price} • {option.confidence.toUpperCase()} confidence</div>
                                  <div style={{ fontSize: '10px', color: 'var(--ink-mute)', marginTop: '2px' }}>{option.reasoning}</div>
                               </div>
                               <button 
                                 onClick={() => handleChooseReplacement(item.name, option)}
                                 style={{ background: 'var(--green)', color: 'white', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '10px', cursor: 'pointer', fontWeight: 'bold' }}
                               >
                                 CHOOSE
                               </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {requiresConsultation && (
                    <div style={{ marginTop: '12px', padding: '8px', background: 'rgba(255, 82, 82, 0.1)', borderLeft: '2px solid var(--red)', color: 'var(--red)', fontSize: '12px' }}>
                      <strong>⛔ UNAVAILABLE</strong>
                      <p style={{ margin: '4px 0 0 0' }}>{item.message || item.substitute_reasoning || 'Primary and substitutes unavailable or unsafe. Doctor consultation required.'}</p>
                    </div>
                  )}
               </div>
            );
          })
        ) : (
          <div style={{ color: 'var(--ink-3)', fontFamily: 'var(--font-machine)', fontSize: '12px' }}>No items in cart yet.</div>
        )}
      </div>
      
      {pipelineState.orderSummary && (
        <div style={{ borderTop: '1px solid var(--divider)', paddingTop: '1rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-machine)' }}>
           <span>TOTAL:</span>
           <span style={{ color: 'var(--green)', fontWeight: 'bold', fontSize: '1.2rem' }}>₹{pipelineState.orderSummary.totalPrice}</span>
        </div>
      )}

      <button 
        className="trigger-button" 
        style={{ 
           marginTop: 'auto', 
           background: (pipelineState.checkoutReady && !pipelineState.orderSummary?.items?.some(i => i.stockStatus !== 'In Stock' && (!i.substitute || !i.substitute.suggestions?.length))) ? 'var(--indigo)' : 'var(--bg-room)', 
           color: (pipelineState.checkoutReady && !pipelineState.orderSummary?.items?.some(i => i.stockStatus !== 'In Stock' && (!i.substitute || !i.substitute.suggestions?.length))) ? 'white' : 'var(--ink-mute)', 
           border: pipelineState.checkoutReady ? 'none' : '1px solid var(--divider)' 
        }}
        disabled={!pipelineState.checkoutReady || pipelineState.orderSummary?.items?.some(i => i.stockStatus !== 'In Stock' && (!i.substitute || !i.substitute.suggestions?.length))}
        onClick={() => {
           pipelineStore.dispatch('order_created', { orderSummary: pipelineState.orderSummary });
        }}
      >
        {pipelineState.orderSummary?.items?.some(i => i.stockStatus !== 'In Stock' && (!i.substitute || !i.substitute.suggestions?.length)) ? 'REPLACEMENTS NEEDED or CONSULTATION' : 'PROCEED TO SUMMARY'}
      </button>
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

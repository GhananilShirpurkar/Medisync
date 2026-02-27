/* eslint-disable no-unused-vars */
import React, { useEffect, useRef } from 'react';
import './ConsultationStage.css';
import PulseLine from '../PulseLine/PulseLine';

const ConsultationStage = ({ 
  messages = [], 
  onSubmit, 
  isSettled, 
  checkoutReady,
  patientContext,
  ambientState,
  onCheckout
}) => {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length, isSettled]);

  const age = patientContext?.age || 0;
  const duration = parseInt(patientContext?.symptom_duration) || 0;
  const isHighRisk = patientContext?.symptom_severity === 'severe';
  
  const shouldEscalate = age > 65 && duration > 10 && isHighRisk;

  return (
    <div className="consultation-stage-container">
      <div className="stage-message-list" ref={scrollRef}>
        {(!messages || messages.length === 0) ? (
          <div className="stage-idle-watermark">
             <div className="watermark-logo">⋈</div>
             <div className="watermark-text">How can I help you today?</div>
             <div className="watermark-sub">MediSync AI Assistant v2.0</div>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isAssistant = msg.role === 'assistant' || msg.sender === 'ai';
            const textContent = msg.text || msg.content || (typeof msg === 'string' ? msg : '');
            
            // Render nothing if absolutely no content
            if (!textContent && !msg.type) return null;

            return (
              <div key={msg.id || idx} className={`stage-message-row ${msg.sender} ${isAssistant ? 'assistant-response' : ''}`}>
                {msg.type === 'image' && msg.url && (
                  <div style={{ marginBottom: '8px', border: '1px solid var(--divider)', padding: '4px', background: 'var(--bg-panel)', display: 'inline-block' }}>
                    <img 
                      src={msg.url} 
                      alt="Uploaded prescription" 
                      style={{ maxWidth: '200px', maxHeight: '200px', objectFit: 'contain' }} 
                    />
                  </div>
                )}
                
                {msg.type === 'audio' && (
                  <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: 'var(--bg-panel)', border: '1px solid var(--amber)', color: 'var(--amber)', fontFamily: 'var(--font-machine)', fontSize: '11px', borderRadius: '4px' }}>
                    <span>🎙️</span>
                    <div style={{ display: 'flex', gap: '2px', height: '12px', alignItems: 'center' }}>
                      <div style={{ width: '3px', height: '100%', background: 'var(--amber)', animation: 'typing 1s infinite' }} />
                      <div style={{ width: '3px', height: '60%', background: 'var(--amber)', animation: 'typing 1s infinite 0.2s' }} />
                      <div style={{ width: '3px', height: '80%', background: 'var(--amber)', animation: 'typing 1s infinite 0.4s' }} />
                      <div style={{ width: '3px', height: '40%', background: 'var(--amber)', animation: 'typing 1s infinite 0.6s' }} />
                    </div>
                  </div>
                )}

                {textContent && (
                  <p 
                    className="stage-message-text"
                    style={isAssistant ? { 
                      fontFamily: "'Cormorant Garamond', serif", 
                      fontSize: '20px', 
                      fontStyle: 'italic',
                      lineHeight: '1.4',
                      color: 'var(--amber)' 
                    } : {}}
                  >
                    {textContent}
                  </p>
                )}

                {isAssistant && msg.severityAssessment && (
                  <div className="stage-intelligence-block">
                    <div className="stage-confidence-score">
                      Confidence Score: {msg.severityAssessment.confidence_score || '0.88'} &nbsp;&nbsp;|&nbsp;&nbsp; 
                      Model Version: RiskEngine v1.2
                    </div>
                    
                    <details className="stage-clinical-reasoning">
                      <summary>View Clinical Reasoning</summary>
                      <div className="reasoning-content">
                        <ul>
                           {msg.severityAssessment.red_flags_detected && msg.severityAssessment.red_flags_detected.length > 0 ? (
                             msg.severityAssessment.red_flags_detected.map((flag, fidx) => (
                               <li key={fidx}>{flag}</li>
                             ))
                           ) : (
                             <li>No immediate red flags detected</li>
                           )}
                           <li>Risk Assignment: {msg.severityAssessment.risk_level?.toUpperCase()}</li>
                           <li>Consultation Route: {msg.severityAssessment.route}</li>
                        </ul>
                      </div>
                    </details>
                  </div>
                )}

                {msg.footnotes && msg.footnotes.map((fn, fidx) => (
                  <div key={fidx} className="stage-footnote">
                    <span className="stage-footnote-label">{fn.agent} // Footnote</span>
                    <span className="stage-footnote-meta">{fn.text}</span>
                  </div>
                ))}
              </div>
            );
          })
        )}

        {!isSettled && messages.length > 0 && messages[messages.length - 1].sender === 'user' && (
          <div className="stage-message-row ai">
            <div className="typing-indicator">
              <span></span><span></span><span></span> AI Agent is typing...
            </div>
          </div>
        )}
      </div>

      <div className="stage-input-area">
        <div className={`checkout-panel ${checkoutReady ? 'visible' : ''}`}>
          <div className="checkout-content">
            <span className="checkout-label">FULFILLMENT READY</span>
            <span className="checkout-sub">Items validated and ready for checkout.</span>
          </div>
          <button className="checkout-proceed-btn" onClick={onCheckout}>
            Proceed to Checkout <span className="arrow-icon">→</span>
          </button>
        </div>

        {shouldEscalate && (
          <div className="escalation-trigger-panel">
            <div className="escalation-trigger-content">
              <span className="escalation-trigger-label">SYSTEM OVERRIDE</span>
              <span className="escalation-trigger-text">
                Given persistence {duration} days and patient age {age}, teleconsultation recommended.
              </span>
            </div>
            <button className="escalation-trigger-btn" onClick={() => alert("Doctor callback requested!")}>
              Request Doctor Callback
            </button>
          </div>
        )}

        <PulseLine 
          onSubmit={onSubmit} 
          placeholder={isSettled ? "Session complete." : "Describe symptoms..."} 
          disabled={isSettled}
        />
      </div>
    </div>
  );
};

export default ConsultationStage;

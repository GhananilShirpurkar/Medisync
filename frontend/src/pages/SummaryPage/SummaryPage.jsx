import React, { useEffect, useState, useMemo } from 'react';
import { pipelineStore } from '../../state/pipelineStore';
import mlog from '../../services/debugLogger';
import './SummaryPage.css';

const SummaryPage = () => {
    const [pipelineState, setPipelineState] = useState(pipelineStore.get());
    const [paymentConfirmed, setPaymentConfirmed] = useState(false);

    useEffect(() => {
        const unsubscribe = pipelineStore.subscribe(setPipelineState);
        return () => unsubscribe();
    }, []);

    const [paymentId, setPaymentId] = useState(null);
    const [qrData, setQrData] = useState(null);
    const [timeLeft, setTimeLeft] = useState(9);

    // Phase 1: Initiate Payment
    useEffect(() => {
        const order = pipelineState.orderSummary;
        if (order && !paymentId) {
            const initiatePayment = async () => {
                try {
                    const res = await fetch('http://localhost:8000/api/payment/initiate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            order_id: order.orderId,
                            amount: order.totalPrice
                        })
                    });
                    const data = await res.json();
                    if (data.payment_id) {
                        setPaymentId(data.payment_id);
                        setQrData(data.qr_code_data);
                        mlog.info('Payment initiated', { paymentId: data.payment_id });
                    }
                } catch (err) {
                    mlog.error('Payment initiation failed', { error: err.message });
                }
            };
            initiatePayment();
        }
    }, [pipelineState.orderSummary]);

    // Phase 2: Poll for status + countdown UI
    useEffect(() => {
        if (!paymentId || paymentConfirmed) return;

        const countdownInterval = setInterval(() => {
            setTimeLeft(prev => Math.max(0, prev - 1));
        }, 1000);

        const pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/payment/status/${paymentId}`);
                const data = await res.json();
                if (data.status === 'success') {
                    setPaymentConfirmed(true);
                    pipelineStore.dispatch('payment_confirmed', { txn_id: data.transaction_id });
                    mlog.whatsapp('Payment SETTLED', { txn_id: data.transaction_id });
                    clearInterval(pollInterval);
                    clearInterval(countdownInterval);
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 2000);

        return () => {
            clearInterval(pollInterval);
            clearInterval(countdownInterval);
        };
    }, [paymentId, paymentConfirmed]);

    const handleNewConsultation = () => {
        pipelineStore.dispatch('RESET_SESSION', {});
    };

    const handleSavePDF = () => {
        window.print();
    };

    const { 
        pid, 
        messages, 
        traceSteps, 
        shelfCards, 
        orderSummary, 
        notificationSent,
        phone 
    } = pipelineState;

    if (!orderSummary) return null;

    // --- DATA PROCESSING (V3) ---

    const complaint = messages.find(m => m.sender === 'user')?.content || '"paracetamol"';
    const triage = shelfCards.triage || {};
    const validationStatus = triage.details?.decision || 'approved';
    const safetyIssue = triage.details?.safety_issues?.[0] || triage.safety_issues?.[0];

    const processedTraceSteps = useMemo(() => {
        // Step 1 — deduplicate: one entry per unique agent, keep final completed event
        const agentMap = {};
        (pipelineStore.traceSteps || []).forEach(step => {
          if (step.status === 'completed') {
            agentMap[step.agent] = step;
          }
        });
        const uniqueAgents = Object.values(agentMap);
        
        // Return sorted agents matching old format but mapped with new getting logic
        return uniqueAgents.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    }, [traceSteps]);

    // Step 2 — safe duration calculation, never return NaN
    const getDuration = (step) => {
      const started = (pipelineStore.traceSteps || []).find(
        s => s.agent === step.agent && s.status === 'started'
      );
      if (!started || !step.timestamp || !started.timestamp) return '—';
      const diff = (new Date(step.timestamp) - new Date(started.timestamp)) / 1000;
      return isNaN(diff) || diff < 0 ? '—' : `${diff.toFixed(1)}s`;
    };

    const totalPipelineTime = useMemo(() => {
        // Step 3 — total time
        const first = (pipelineStore.traceSteps || [])[0];
        const last = (pipelineStore.traceSteps || []).slice(-1)[0];
        const totalTime = (first && last && first.timestamp && last.timestamp)
          ? `${((new Date(last.timestamp) - new Date(first.timestamp)) / 1000).toFixed(1)}s`
          : '—';
        return totalTime;
    }, [traceSteps]);

    const maskedPhone = useMemo(() => {
        if (!phone) return '+91 XXXXXX0000';
        const last4 = phone.replace(/\D/g, '').slice(-4);
        return `+91 XXXXXX${last4}`;
    }, [phone]);

    const formattedTimestamp = useMemo(() => {
        const date = new Date();
        return `${date.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} · ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase()}`;
    }, []);

    return (
        <div className="summary-v3-container">
            <div className="summary-dashboard">
                
                {/* GLOBAL HEADER BAR */}
                <header className="global-header animate-fade-up-0">
                    <div className="header-brand">
                        <span className="brand-label">MEDI<span className="accent">SYNC</span></span>
                        <span className="brand-sub">CONSULTATION SUMMARY</span>
                    </div>
                    <div className="header-meta">
                        <span className="meta-time">{formattedTimestamp}</span>
                        <button className="save-pdf-btn" onClick={handleSavePDF}>SAVE PDF</button>
                    </div>
                </header>

                <div className="dashboard-grid">
                    
                    {/* LEFT RAIL: CONTEXT */}
                    <aside className="dashboard-left-rail animate-fade-right">
                        <div className="rail-section">
                            <div className="rail-label">PATIENT CONTEXT</div>
                            <div className="patient-id-block">
                                <span className="id-label">ID</span>
                                <span className="id-val">{pid || '9067939108'}</span>
                            </div>
                        </div>

                        <div className="rail-section">
                            <div className="rail-label">ORDER ID</div>
                            <div className="order-ref-val">{orderSummary.orderId || 'ORD-XXXX'}</div>
                        </div>

                        <div className={`rail-section validation-box status-${validationStatus}`}>
                            <div className="rail-label">VALIDATION</div>
                            <div className="validation-main">
                                {validationStatus === 'approved' && "Approved"}
                                {validationStatus === 'needs_review' && "Under Review"}
                                {validationStatus === 'rejected' && "Rejected"}
                            </div>
                            <div className="validation-sub">
                                {validationStatus === 'approved' ? "No contraindications found" : safetyIssue}
                            </div>
                        </div>
                    </aside>

                    {/* CENTER CONSOLE: CLINICAL CORE */}
                    <main className="dashboard-center animate-fade-up-200">
                        <section className="complaint-console">
                            <div className="console-label">PATIENT COMPLAINT</div>
                            <div className="complaint-text">{complaint}</div>
                        </section>

                        <section className="medicines-console">
                            <div className="console-label">MEDICINES DISPENSED</div>
                            <div className="medicines-table">
                                <header className="table-header">
                                    <span className="col-name">MEDICINE</span>
                                    <span className="col-status">STATUS</span>
                                    <span className="col-price">PRICE</span>
                                </header>
                                <div className="table-body">
                                    {orderSummary.items.map((item, idx) => (
                                        <div key={idx} className="medicine-row">
                                            <div className="med-primary">
                                                <div className="name-line">{item.name}</div>
                                                <div className="subnote-line">
                                                    ↳ {item.isSubstitution ? 
                                                        `Substituted for ${item.originalName || 'item'} · Semantic Match` : 
                                                        `${item.indication || 'Standard medication'}`}
                                                </div>
                                            </div>
                                            <span className={`med-status badge-${item.stockStatus.toLowerCase().replace(' ', '-')}`}>
                                                [{item.stockStatus}]
                                            </span>
                                            <span className="med-price">₹{item.price.toFixed(2)}</span>
                                        </div>
                                    ))}
                                </div>
                                <footer className="table-footer">
                                    <div className="total-label">TOTAL AMOUNT</div>
                                    <div className="total-value">₹{orderSummary.totalPrice.toFixed(2)}</div>
                                </footer>
                            </div>
                        </section>
                    </main>

                    {/* RIGHT RAIL: ORCHESTRATION / TECHNICAL */}
                    <aside className="dashboard-right-rail animate-fade-left">
                        <section className="rail-section pipeline-technical">
                            <div className="rail-label">PIPELINE AUDIT</div>
                            <div className="pipeline-trace">
                                {processedTraceSteps.map((step, idx) => {
                                    const agentName = step.agent.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                                    return (
                                        <div key={idx} className="trace-row">
                                            <span className="trace-check">✓</span>
                                            <span className="trace-agent">{agentName}</span>
                                            <span className="trace-time">{getDuration(step)}</span>
                                        </div>
                                    );
                                })}
                                <div className="trace-total">
                                    <span className="label">TOTAL</span>
                                    <span className="val">{totalPipelineTime} · {processedTraceSteps.length} Agents</span>
                                </div>
                            </div>
                        </section>

                        <section className="rail-section payment-technical">
                            <div className="rail-label">PAYMENT SETTLEMENT</div>
                            <div className="payment-mini-block">
                                <div className="qr-box">
                                    <img src={qrData || "/assets/mock_qr.png"} className={`qr-code ${paymentConfirmed ? 'confirmed' : ''}`} alt="QR" />
                                    {!paymentConfirmed && timeLeft > 0 && (
                                        <div className="qr-countdown-overlay" style={{
                                            position: 'absolute',
                                            top: '50%',
                                            left: '50%',
                                            transform: 'translate(-50%, -50%)',
                                            background: 'rgba(0,0,0,0.7)',
                                            color: 'white',
                                            padding: '10px 15px',
                                            borderRadius: '50%',
                                            fontWeight: 'bold',
                                            fontSize: '18px',
                                            pointerEvents: 'none'
                                        }}>
                                            {timeLeft}s
                                        </div>
                                    )}
                                </div>
                                <div className="pay-meta">
                                    <div className="upi">medisync@upi</div>
                                    <div className={`pay-status ${paymentConfirmed ? 'confirmed' : 'waiting'}`}>
                                        {paymentConfirmed ? 'SETTLED ✓' : `WAITING ${timeLeft}s ●`}
                                    </div>
                                    {!paymentConfirmed && (
                                        <div style={{ width: '100%', background: '#eee', height: '4px', marginTop: '8px', borderRadius: '2px', overflow: 'hidden' }}>
                                            <div style={{ width: `${(timeLeft / 9) * 100}%`, background: 'var(--indigo)', height: '100%', transition: 'width 1s linear' }}></div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </section>

                        <section className="rail-section whatsapp-technical">
                            <div className="rail-label">SOCIAL NOTIFICATION</div>
                            {!paymentConfirmed ? (
                                <div className="whatsapp-pending">Waiting for settlement...</div>
                            ) : (
                                <div className="whatsapp-preview animate-fade-in">
                                    <div className="recipient">TO {maskedPhone}</div>
                                    <div className="preview-bubble">
                                        <div className="bubble-content">
                                            MediSync 💊<br/>
                                            Order {orderSummary.orderId} Confirmed<br/>
                                            Total: ₹{orderSummary.totalPrice.toFixed(2)}<br/>
                                            Collect at counter.
                                        </div>
                                    </div>
                                    <div className="preview-label">SENT VIA TWILIO</div>
                                </div>
                            )}
                        </section>
                    </aside>

                </div>

                {/* FOOTER ACTION */}
                <footer className="dashboard-footer">
                    <button className="new-session-btn" onClick={handleNewConsultation}>
                        NEW CONSULTATION
                    </button>
                    <div className="footer-v-tag">MEDISYNC v4.1 · PRODUCTION STAGE</div>
                </footer>

            </div>
        </div>
    );
};

export default SummaryPage;

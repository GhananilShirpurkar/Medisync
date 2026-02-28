import { pipelineStore } from '../state/pipelineStore';

let wsConnection = null;
let retryCount = 0;
const maxRetries = 5;
const baseDelay = 1000;

const reconnect = (sessionId) => {
  if (retryCount >= maxRetries) {
    pipelineStore.dispatch('CONNECTION_LOST', { session_id: sessionId });
    return;
  }
  const delay = baseDelay * Math.pow(2, retryCount);
  retryCount++;
  console.log(`[WS] Reconnecting in ${delay}ms... (Attempt ${retryCount}/${maxRetries})`);
  setTimeout(() => initWebSocket(sessionId), delay);
};

const initWebSocket = (sessionId) => {
  if (wsConnection) {
    wsConnection.close();
  }
  
  wsConnection = new WebSocket(`ws://localhost:8000/ws/trace/${sessionId}`);
  
  wsConnection.onopen = () => {
    console.log(`[WS] Connected to trace stream for session: ${sessionId}`);
    retryCount = 0; // Reset on successful connection
  };

  wsConnection.onmessage = (event) => {
    try {
      const traceEvent = JSON.parse(event.data);
      console.log("[WS TRACE]:", traceEvent);
      
      // We can map these if needed later, but right now we push the raw traceEvent
      // to the store without transforming it to a mapped CSS class locally.

      // Dispatch to pipelineStore
      // The new AgentLog component expects the raw shape of the trace event
      // We push the whole event instead of transforming it to phase/type/text
      pipelineStore.dispatch('TRACE_APPEND', traceEvent);

      // Simple mapping for demonstration of shelf cards, update ambience etc
      if (traceEvent.details && traceEvent.details.severity) {
         pipelineStore.dispatch('UPDATE_AMBIENCE', { 
           severity: traceEvent.details.severity, 
           isConflict: !!traceEvent.details.risk && traceEvent.details.risk.toLowerCase().includes('critical'), 
           isHalted: false 
         });
         
         pipelineStore.dispatch('SHELF_CARD_READY', {
           type: 'triage',
           card: {
             title: 'TRIAGE ASSESSMENT',
             severity: traceEvent.details.severity,
             content: [`Risk: ${traceEvent.details.risk}`]
           }
         });
      }
      
    } catch (e) {
      console.error("[WS] Failed to parse message", e);
    }
  };

  wsConnection.onerror = (error) => {
    console.error("[WS] Error occurred", error);
    reconnect(sessionId);
  };

  wsConnection.onclose = (event) => {
    console.log(`[WS] Disconnected from trace stream`);
    if (!event.wasClean) {
        reconnect(sessionId);
    }
  };
};

export const sendOTPAPI = async (phone) => {
  const res = await fetch('http://localhost:8000/api/conversation/auth/otp/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone })
  });
  if (!res.ok) throw new Error('Failed to send OTP');
  return await res.json();
};

export const verifyOTPAPI = async (phone, code) => {
  const res = await fetch('http://localhost:8000/api/conversation/auth/otp/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, code })
  });
  if (!res.ok) throw new Error('Invalid or expired OTP');
  return await res.json();
};

export const runIdentityFlowAPI = async (phoneNumber) => {

  try {
    pipelineStore.dispatch('TRACE_APPEND', { 
      agent: 'GATEWAY', 
      step: 'Initializing Session', 
      type: 'tool',
      status: 'completed',
      timestamp: new Date().toISOString()
    });
    
    // Create Session
    const res = await fetch('http://localhost:8000/api/conversation/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: phoneNumber || `operator_${Date.now()}` })
    });
    
    const data = await res.json();
    const sessionId = data.session_id;
    
    // Set in store and connect WS
    pipelineStore.dispatch('SET_SESSION_ID', { sessionId });
    initWebSocket(sessionId);
    
    pipelineStore.dispatch('RECORD_APPEND', { text: `Session opened (${sessionId})` });
    pipelineStore.dispatch('IDENTITY_RESOLVED', { pid: phoneNumber || 'PID-API', phone: phoneNumber || '' });
    
  } catch (error) {
    console.error("Failed to init identity flow", error);
    pipelineStore.dispatch('RECORD_APPEND', { text: `Error: Could not connect to backend.` });
    throw error;
  }
};

// Helper for TTS — speaks AI responses aloud when voice output is enabled
let cachedVoice = null;

// Preload voices (browsers load them async)
if ('speechSynthesis' in window) {
  const loadVoices = () => {
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      cachedVoice = voices.find(v => v.lang.includes('en-GB') || v.name.includes('Google UK English Female'))
                 || voices.find(v => v.lang.startsWith('en'))
                 || voices[0];
    }
  };
  loadVoices();
  window.speechSynthesis.onvoiceschanged = loadVoices;
}

const speakResponse = (text) => {
  const storeState = pipelineStore.get();
  
  if (!storeState.isVoiceResponseEnabled) {
    return; // Silent — voice output disabled
  }

  if (!('speechSynthesis' in window)) {
    console.warn('[TTS] speechSynthesis not supported in this browser');
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Clean text by removing emojis, markdown, and special characters
  const cleanText = text
    .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
    .replace(/[#*`_~]/g, '')
    .replace(/\n+/g, '. ')
    .trim();

  if (!cleanText) return;

  const utterance = new SpeechSynthesisUtterance(cleanText);

  if (cachedVoice) {
    utterance.voice = cachedVoice;
  }

  utterance.rate = 1.05;
  utterance.pitch = 1.0;

  utterance.onend = () => console.log('[TTS] Finished speaking');
  utterance.onerror = (e) => console.error('[TTS] Error:', e.error);

  window.speechSynthesis.speak(utterance);
  console.log('[TTS] Speaking response (' + cleanText.length + ' chars)');
};

export const runConsultationFlowAPI = async (userMessage) => {
  const storeState = pipelineStore.get();
  let sessionId = storeState.sessionId;
  
  if (!sessionId) {
    // If no session exists, create a temporary anonymous session to allow the message to flow
    console.warn("No session ID found. Auto-generating anon session.");
    await runIdentityFlowAPI(`anon_${Date.now()}`);
    sessionId = pipelineStore.get().sessionId;
  }
  
  pipelineStore.dispatch('RECORD_APPEND', { text: userMessage });
  pipelineStore.dispatch('INPUT_CONFIDENCE_UPDATED', { type: 'text', score: 100 });
  
  try {
    const res = await fetch('http://localhost:8000/api/conversation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: userMessage })
    });
    
    const data = await res.json();

    if (data.client_action === 'OPEN_CAMERA') {
      pipelineStore.dispatch('OPEN_CAMERA', {});
    }
    
    // Based on the response, trigger the necessary store updates
    if (data.intent) {
      pipelineStore.dispatch('intent_classified', { 
        intent: data.intent, 
        entities: data.patient_context ? Object.keys(data.patient_context) : [],
        patientContext: data.patient_context || null,
        recommendations: data.recommendations || []
      });
    }

    if (data.recommendations && data.recommendations.length > 0) {
      const meds = data.recommendations.map(r => `${r.medicine_name} - ${r.stock > 0 ? 'In Stock' : 'Out of Stock'}`);
      pipelineStore.dispatch('SHELF_CARD_READY', {
        type: 'inventory',
        card: {
          title: 'INVENTORY RECOMMENDATIONS',
          severity: 0,
          content: meds
        }
      });
    }

    pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
      text: data.message,
      footnotes: [],
      severityAssessment: data.severity_assessment
    });
    
    speakResponse(data.message);

    if (!data.needs_clarification && data.recommendations && data.recommendations.length > 0) {
      // Dispatch CHECKOUT_READY instead of automatically transitioning.
      // This will spawn the slide-in proceed panel.
      setTimeout(() => {
        let totalPrice = 0;
        const items = data.recommendations.map(r => {
           totalPrice += r.price;
           return { 
             name: r.medicine_name, 
             stockStatus: r.stock > 0 ? 'In Stock' : 'Out of Stock', 
             price: r.price,
             warnings: r.warnings || [],
             substitute: r.substitute || null
           };
        });

        pipelineStore.dispatch('CHECKOUT_READY', {
          orderSummary: {
            pid: storeState.pid,
            complaint: userMessage, 
            validation: { status: 'Approved', severity: data.severity_assessment?.severity_score || 0 },
            items,
            substitutions: [],
            totalPrice,
            orderId: `ORD-${Date.now().toString().slice(-4)}`
          }
        });
      }, 500);
    }

    // FIX 3: Trigger CHECKOUT_READY after YES confirmation
    if (data.order_id || (data.next_step === 'order_complete' && data.message?.includes('Order'))) {
      const currentState = pipelineStore.get();
      pipelineStore.dispatch('CHECKOUT_READY', {
        orderSummary: {
          pid: currentState.pid,
          orderId: data.order_id || `ORD-${Date.now()}`,
          complaint: currentState.lastUserMessage || '',
          validation: { status: 'Approved', severity: 0 },
          items: (currentState.lastRecommendations || []).map(r => ({
            name: r.medicine_name || r.name,
            stockStatus: (r.in_stock || r.stock > 0 || r.available) ? 'In Stock' : 'Out of Stock',
            price: r.price || 0,
            warnings: [],
            substitute: null
          })),
          substitutions: [],
          totalPrice: (currentState.lastRecommendations || []).reduce((sum, r) => sum + (r.price || 0), 0)
        }
      });
    }


  } catch (error) {
    console.error("Failed consultation flow", error);
    pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
      text: "Sorry, I am having trouble connecting to the system right now.",
      footnotes: []
    });
  }
};

export const runVoiceFlowAPI = async (audioBlob) => {
  const storeState = pipelineStore.get();
  let sessionId = storeState.sessionId;
  
  if (!sessionId) {
    // Attempt auto-generation to prevent block
    console.warn("No session ID found for Voice. Auto-generating anon session.");
    await runIdentityFlowAPI(`anon_${Date.now()}`);
    sessionId = pipelineStore.get().sessionId;
    
    if (!sessionId) {
      console.warn("Please send a 'Hello' first to open a session before using voice dictation.");
      return;
    }
  }
  
  pipelineStore.dispatch('RECORD_APPEND', { text: "🎤 Voice input received", type: 'voice' });
  
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    // We add session_id as a query param per backend design
    const url = new URL('http://localhost:8000/api/conversation/voice');
    url.searchParams.append('session_id', sessionId);

    const res = await fetch(url, {
      method: 'POST',
      body: formData // No Content-Type header needed for FormData
    });
    
    if (!res.ok) {
        pipelineStore.dispatch('TRACE_APPEND', { 
          agent: 'SYSTEM', 
          step: `Voice API returned ${res.status}`, 
          type: 'error',
          status: 'failed',
          timestamp: new Date().toISOString()
        });
        throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    
    // Echo back what the user said (transcription) into the record log explicitly if desired
    pipelineStore.dispatch('RECORD_APPEND', { text: `Transcription: "${data.transcription}"`, type: 'info' });

    if (data.client_action === 'OPEN_CAMERA') {
      pipelineStore.dispatch('OPEN_CAMERA', {});
    }

    if (data.intent) {
      pipelineStore.dispatch('intent_classified', { 
        intent: data.intent, 
        entities: data.patient_context ? Object.keys(data.patient_context) : [],
        patientContext: data.patient_context || null,
        recommendations: data.recommendations || []
      });
    }

    if (data.recommendations && data.recommendations.length > 0) {
      const meds = data.recommendations.map(r => `${r.medicine_name} - ${r.stock > 0 ? 'In Stock' : 'Out of Stock'}`);
      pipelineStore.dispatch('SHELF_CARD_READY', {
        type: 'inventory',
        card: {
          title: 'INVENTORY RECOMMENDATIONS',
          severity: 0,
          content: meds
        }
      });
    }

    pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
      text: data.message,
      footnotes: [{ agent: 'Whisper', text: `Confidence: ${(data.transcription_confidence * 100).toFixed(0)}%` }],
      severityAssessment: data.severity_assessment
    });
    
    pipelineStore.dispatch('INPUT_CONFIDENCE_UPDATED', { 
      type: 'voice', 
      score: Math.round(data.transcription_confidence * 100) 
    });
    
    speakResponse(data.message);

    if (!data.needs_clarification && data.recommendations && data.recommendations.length > 0) {
      setTimeout(() => {
        let totalPrice = 0;
        const items = data.recommendations.map(r => {
           totalPrice += r.price;
           return { 
             name: r.medicine_name, 
             stockStatus: r.stock > 0 ? 'In Stock' : 'Out of Stock', 
             price: r.price,
             warnings: r.warnings || [],
             substitute: r.substitute || null
           };
        });

        pipelineStore.dispatch('CHECKOUT_READY', {
          orderSummary: {
            pid: storeState.pid,
            complaint: data.transcription,
            validation: { status: 'Approved', severity: data.severity_assessment?.severity_score || 0 },
            items,
            substitutions: [],
            totalPrice,
            orderId: `ORD-${Date.now().toString().slice(-4)}`
          }
        });
      }, 500);
    }
  } catch (error) {
    console.error("Failed voice consultation flow", error);
    pipelineStore.dispatch('TRACE_APPEND', { 
      agent: 'SYSTEM', 
      step: `Voice API Error: ${error.message}`, 
      type: 'error',
      status: 'failed',
      timestamp: new Date().toISOString()
    });
    pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
      text: "Sorry, I am having trouble connecting to the system right now.",
      footnotes: []
    });
  }
};

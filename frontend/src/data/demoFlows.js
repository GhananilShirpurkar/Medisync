import { pipelineStore } from '../state/pipelineStore';

/**
 * Simulates backend WebSocket events.
 * Uses exact delays to orchestrate the multi-agent UI transitions.
 */

const executeFlow = (events) => {
  let accumDelay = 0;
  events.forEach(({ delay, event, payload }) => {
    accumDelay += delay;
    setTimeout(() => {
      pipelineStore.dispatch(event, payload);
    }, accumDelay);
  });
};

export const runIdentityFlow = () => {
  executeFlow([
    { delay: 100, event: 'TRACE_APPEND', payload: { phase: 'GATEWAY', type: 'tool', text: 'Receive Message' } },
    { delay: 400, event: 'TRACE_APPEND', payload: { phase: 'IDENTITY', type: 'tool', text: 'Scan for Phone Number' } },
    { delay: 800, event: 'identity_resolved', payload: { pid: 'PID-10928' } },
    { delay: 800, event: 'RECORD_APPEND', payload: { text: "Session opened" } }
  ]);
};

export const runConsultationFlow = (userMessage) => {
  // We use the actual user message for the simulation instead of hardcoding it
  executeFlow([
    { delay: 500, event: 'RECORD_APPEND', payload: { text: userMessage } },
    { delay: 800, event: 'TRACE_APPEND', payload: { phase: 'INTAKE', type: 'think', text: 'Classify Intent' } },
    { delay: 1200, event: 'intent_classified', payload: { intent: 'order', entities: ['symptom', 'condition'] } },
    
    // Triage
    { delay: 800, event: 'TRACE_APPEND', payload: { phase: 'TRIAGE', type: 'think', text: 'Assess Severity' } },
    { delay: 1500, event: 'TRACE_APPEND', payload: { phase: 'TRIAGE', type: 'result', text: 'Severity 8 - Caution' } },
    { delay: 500, event: 'UPDATE_AMBIENCE', payload: { severity: 8, isConflict: false, isHalted: false } },
    { delay: 800, event: 'RECORD_APPEND', payload: { text: 'MEDICAL // Assess Severity: 8 - Caution' } },
    { delay: 1200, event: 'SHELF_CARD_READY', payload: { 
      type: 'triage', 
      card: { title: 'TRIAGE ASSESSMENT', severity: 8, content: ['Symptom: Severe', 'Recommendation: Monitor closely. Discontinue if symptoms worsen.'] } 
    }},

    // Inventory
    { delay: 800, event: 'TRACE_APPEND', payload: { phase: 'INVENTORY', type: 'tool', text: 'Check Stock' } },
    { delay: 1200, event: 'TRACE_APPEND', payload: { phase: 'INVENTORY', type: 'result', text: 'Paracetamol In Stock' } },
    { delay: 1200, event: 'SHELF_CARD_READY', payload: { 
      type: 'inventory', 
      card: { title: 'INVENTORY', severity: 0, content: ['Paracetamol 500mg - ALLOCATED'] } 
    }},

    // Fulfillment
    { delay: 800, event: 'TRACE_APPEND', payload: { phase: 'FULFILLMENT', type: 'tool', text: 'Create Order' } },
    { delay: 1200, event: 'TRACE_APPEND', payload: { phase: 'FULFILLMENT', type: 'done', text: 'Order Complete' } },
    { delay: 500, event: 'SHELF_CARD_READY', payload: { 
      type: 'fulfillment', 
      card: { title: 'ORDER PREPARED', severity: 0, content: ['Order ID: ORD-1992-X4', 'Amount: ₹125.00'] } 
    }},
    { delay: 500, event: 'AI_RESPONSE_RECEIVED', payload: { 
      text: "I've assessed your symptoms. This is a severity 8 condition. I've placed an order for pain relief, but please seek immediate medical attention if symptoms progress.",
      footnotes: [{ agent: 'Medical', text: 'High risk symptom presented.' }]
    }},

    // Settle & Summary
    { delay: 2000, event: 'ROOM_SETTLES', payload: {} },
    { delay: 500, event: 'RECORD_APPEND', payload: { text: 'Consultation closed · 4 agents resolved' } },
    { delay: 2000, event: 'order_created', payload: { 
      orderSummary: {
        pid: 'PID-10928',
        complaint: userMessage,
        validation: { status: 'Approved', severity: 8 },
        items: [{name: 'Paracetamol 500mg', stockStatus: 'In Stock', price: 125.00}],
        substitutions: [],
        totalPrice: 125.00,
        orderId: 'ORD-1992-X4'
      },
      telegramSent: true
    }}
  ]);
};

export const runFlow2 = () => {
  // Vision Agent Pipeline - Drug Conflict
  executeFlow([
    { delay: 300, event: 'prescription_uploaded', payload: {} },
    { delay: 600, event: 'TRACE_APPEND', payload: { phase: 'VISION', type: 'tool', text: 'OCR Extract' } },
    { delay: 1800, event: 'TRACE_APPEND', payload: { phase: 'VISION', type: 'result', text: 'Amoxicillin 500mg detected' } },
    { delay: 100, event: 'identity_resolved', payload: { pid: 'PID-54611' } },
    { delay: 200, event: 'intent_classified', payload: { intent: 'order', entities: ['Amoxicillin'] } },
    { delay: 500, event: 'RECORD_APPEND', payload: { text: "Session opened via Document Scan" } },
    
    // Triage -> Conflict
    { delay: 1200, event: 'TRACE_APPEND', payload: { phase: 'TRIAGE', type: 'think', text: 'Cross-check Allergies' } },
    { delay: 2000, event: 'TRACE_APPEND', payload: { phase: 'TRIAGE', type: 'critical result', text: 'CONFLICT: Penicillin Allergy' } },
    { delay: 100, event: 'UPDATE_AMBIENCE', payload: { severity: 9, isConflict: true, isHalted: true } },
    { delay: 800, event: 'RECORD_APPEND', payload: { text: 'MEDICAL // CRITICAL: Patient history indicates severe anaphylaxis risk with Penicillins.' } },
    
    { delay: 1000, event: 'SHELF_CARD_READY', payload: { 
      type: 'triage', 
      card: { title: 'TRIAGE ASSESSMENT', severity: 9, content: ['Rx: Amoxicillin 500mg', 'Risk: FATAL ANAPHYLAXIS', 'Action: REJECTED'] } 
    }},

    { delay: 1500, event: 'AI_RESPONSE_RECEIVED', payload: { 
      text: "I cannot process this prescription. Your medical record indicates a severe allergy to Penicillin, and Amoxicillin belongs to that class. Dispensing this medication could lead to fatal anaphylaxis. Please consult your doctor immediately for an alternative antibiotic.",
      footnotes: [{ agent: 'Medical', text: 'Prescription halted due to absolute contraindication.' }]
    }}
    // Flow halts here. Ambient remains critical. Input line stays active.
  ]);
};

export const runFlow3 = () => {
  // Semantic Substitute 
  executeFlow([
    { delay: 800, event: 'identity_resolved', payload: { pid: 'PID-7731' } },
    { delay: 800, event: 'RECORD_APPEND', payload: { text: "Session opened" } },
    
    // Intake
    { delay: 2000, event: 'USER_MESSAGE_SENT', payload: 'I have a mild fever. I need Dolo 650.' },
    { delay: 500, event: 'RECORD_APPEND', payload: { text: 'I have a mild fever. I need Dolo 650.' } },
    { delay: 1000, event: 'intent_classified', payload: { intent: 'order', entities: ['fever', 'Dolo 650'] } },
    
    // Triage
    { delay: 800, event: 'TRACE_APPEND', payload: { phase: 'TRIAGE', type: 'think', text: 'Assess Severity' } },
    { delay: 1200, event: 'TRACE_APPEND', payload: { phase: 'TRIAGE', type: 'result', text: 'Severity 2 - Mild' } },
    { delay: 500, event: 'UPDATE_AMBIENCE', payload: { severity: 2, isConflict: false, isHalted: false } },
    { delay: 1200, event: 'SHELF_CARD_READY', payload: { 
      type: 'triage', 
      card: { title: 'TRIAGE ASSESSMENT', severity: 2, content: ['Fever: Mild', 'Recommendation: Standard antipyretic clear.'] } 
    }},

    // Inventory -> Substitute
    { delay: 1200, event: 'TRACE_APPEND', payload: { phase: 'INVENTORY', type: 'tool', text: 'Check Stock: Dolo 650' } },
    { delay: 1800, event: 'TRACE_APPEND', payload: { phase: 'INVENTORY', type: 'result', text: 'Dolo 650 Out of Stock' } },
    { delay: 2200, event: 'TRACE_APPEND', payload: { phase: 'INVENTORY', type: 'result', text: 'Semantic Search: Paracetamol 650' } },
    
    { delay: 800, event: 'SHELF_CARD_READY', payload: { 
      type: 'inventory', 
      card: { title: 'INVENTORY ASSIGNMENT', severity: 5, content: ['~~Dolo 650~~ (OOS)', 'Generic Paracetamol 650mg - ALLOCATED'] } 
    }},

    // Fulfillment
    { delay: 1000, event: 'TRACE_APPEND', payload: { phase: 'FULFILLMENT', type: 'tool', text: 'Create Order' } },
    { delay: 800, event: 'TRACE_APPEND', payload: { phase: 'FULFILLMENT', type: 'done', text: 'Order Complete' } },
    { delay: 500, event: 'SHELF_CARD_READY', payload: { 
      type: 'fulfillment', 
      card: { title: 'ORDER PREPARED', severity: 0, content: ['Order ID: ORD-2211-ZZ', 'Amount: ₹45.00'] } 
    }},
    { delay: 500, event: 'AI_RESPONSE_RECEIVED', payload: { 
      text: "Dolo 650 is currently out of stock, but I have found an exact generic equivalent (Paracetamol 650mg) and prepared it for you. Your order is confirmed.",
      footnotes: [{ agent: 'Inventory', text: 'Semantic substitute applied successfully.' }]
    }},

    // Settle & Summary
    { delay: 2000, event: 'ROOM_SETTLES', payload: {} },
    { delay: 500, event: 'RECORD_APPEND', payload: { text: 'Consultation closed · 4 agents resolved' } },
    { delay: 2000, event: 'order_created', payload: { 
      orderSummary: {
        pid: 'PID-7731',
        complaint: 'I have a mild fever. I need Dolo 650.',
        validation: { status: 'Approved', severity: 2 },
        items: [{name: 'Paracetamol 650mg', stockStatus: 'Substituted', price: 45.00}],
        substitutions: ['Dolo 650 → Paracetamol 650mg'],
        totalPrice: 45.00,
        orderId: 'ORD-2211-ZZ'
      },
      telegramSent: false
    }}
  ]);
};

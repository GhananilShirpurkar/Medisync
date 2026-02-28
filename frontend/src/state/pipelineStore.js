// A simple pub/sub central state system. No Redux, no Zustand.
// Single source of truth for the entire application.

let state = {
  sessionId: null,
  currentPage: 'IDENTITY',        // IDENTITY | INTAKE | THEATRE | SUMMARY
  pid: null,
  intent: null,                   // greeting | inquiry | order
  entities: [],
  ambientState: 'base',           // base | warn | critical
  messages: [],
  recordEntries: [],
  traceSteps: [],
  shelfCards: { triage: null, medical: null, inventory: null },
  orderSummary: null,
  sessionSettled: false,
  telegramSent: false,
  isVoiceCallOpen: false,
  isVoiceResponseEnabled: false,
  lastUserMessage: null,      // Added for SummaryPage persistence
  lastRecommendations: [],    // Added for SummaryPage persistence
};


const listeners = new Set();

const calculateAmbientState = (severity, isConflict, isHalted) => {
  if (isHalted) return 'critical';
  if (severity >= 9 || isConflict) return 'critical';
  if (severity >= 7 && severity < 9) return 'warn';
  return 'base';
};

export const pipelineStore = {
  get: () => ({ ...state }),
  
  subscribe: (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  dispatch: (event, payload) => {
    let nextState = { ...state };

    switch(event) {
      case 'RESET_SESSION':
        nextState = {
          sessionId: null,
          currentPage: 'IDENTITY',
          pid: null,
          intent: null,
          entities: [],
          ambientState: 'base',
          messages: [],
          recordEntries: [],
          traceSteps: [],
          shelfCards: { triage: null, medical: null, inventory: null },
          orderSummary: null,
          sessionSettled: false,
          checkoutReady: false,
          pendingOrderSummary: null,
          telegramSent: false,
          patientContext: null,
          isCameraOpen: false,
          isVoiceCallOpen: false,
          // Preserve voice preference across sessions
          isVoiceResponseEnabled: state.isVoiceResponseEnabled,
          lastUserMessage: null,
          lastRecommendations: [],
        };

        break;

      case 'SET_SESSION_ID':
        nextState.sessionId = payload.sessionId;
        break;

      case 'IDENTITY_RESOLVED':
        nextState.pid = payload.pid;
        nextState.phone = payload.phone;
        nextState.currentPage = 'THEATRE';
        if (payload.isDemo) {
          nextState.messages = [{ 
            sender: 'ai', 
            text: `Welcome back, ${payload.patientName}. Last visit you ordered ${payload.previousOrder}. What brings you in today?` 
          }];
        }
        break;

      case 'identity_resolved':
        nextState.pid = payload.pid;
        nextState.currentPage = 'THEATRE';
        break;

      case 'prescription_uploaded':
        // Specifically for direct-to-theatre skipping Intake
        nextState.currentPage = 'THEATRE';
        break;

      case 'intent_classified':
        nextState.intent = payload.intent;
        nextState.entities = payload.entities || [];
        if (payload.patientContext) {
          nextState.patientContext = {
            ...(nextState.patientContext || {}),
            ...payload.patientContext
          };
        }
        if (payload.recommendations && payload.recommendations.length > 0) {
          nextState.lastRecommendations = payload.recommendations;
        }
        nextState.currentPage = 'THEATRE';
        break;



      case 'CHECKOUT_READY':
        nextState.checkoutReady = true;
        // Optionally store the pending order summary so we have it ready
        if (payload.orderSummary) {
          nextState.pendingOrderSummary = payload.orderSummary;
        }
        break;

      case 'order_created':
        // Usually handled when the user actually clicks proceed
        if (payload.orderSummary) {
            nextState.orderSummary = payload.orderSummary;
        } else if (nextState.pendingOrderSummary) {
            nextState.orderSummary = nextState.pendingOrderSummary;
        }
        nextState.telegramSent = payload.telegramSent || false;
        nextState.currentPage = 'SUMMARY';
        break;

      case 'UPDATE_ORDER_ITEM':
        if (nextState.orderSummary && nextState.orderSummary.items) {
            const index = nextState.orderSummary.items.findIndex(i => i.name === payload.oldName);
            if (index !== -1) {
                const updatedItems = [...nextState.orderSummary.items];
                updatedItems[index] = {
                    ...updatedItems[index],
                    name: payload.newName,
                    price: payload.price,
                    stockStatus: 'In Stock',
                    available: true,
                    substitute: null, // Clear substitute info once replaced
                    isReplaced: true,
                    originalName: payload.oldName
                };
                nextState.orderSummary = {
                    ...nextState.orderSummary,
                    items: updatedItems,
                    totalPrice: updatedItems.reduce((sum, i) => sum + (i.price || 0), 0)
                };
            }
        }
        break;

      case 'USER_MESSAGE_SENT':
        if (typeof payload === 'object' && payload !== null) {
          nextState.messages = [...nextState.messages, { sender: 'user', ...payload }];
          nextState.lastUserMessage = payload.text || payload.message || '';
        } else {
          nextState.messages = [...nextState.messages, { sender: 'user', text: payload }];
          nextState.lastUserMessage = payload;
        }
        break;


      case 'AI_RESPONSE_RECEIVED':
        nextState.messages = [...nextState.messages, { 
          sender: 'ai', 
          text: payload.text, 
          footnotes: payload.footnotes,
          severityAssessment: payload.severityAssessment 
        }];
        break;

      case 'RECORD_APPEND':
        nextState.recordEntries = [...nextState.recordEntries, { ...payload, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }];
        break;

      case 'MESSAGE_APPEND':
        if (typeof payload === 'object' && payload !== null) {
          nextState.messages = [...nextState.messages, { ...payload }];
        } else {
          nextState.messages = [...nextState.messages, { sender: 'ai', text: payload }];
        }
        break;

      case 'TRACE_APPEND': {
        if (!payload) break;
        nextState.traceSteps = [...nextState.traceSteps, payload];
        
        // INTERCEPTOR: If this is an agent response message (opening message or follow-up), 
        // also add it to messages array so ConsultationStage can render it.
        const isResponse = payload.type === 'response' || payload.step === 'opening_message';
        const messageText = payload.details?.message || payload.details?.text;
        
        if (isResponse && messageText) {
          // Check if this message is already in the messages array to avoid duplicates
          const isDuplicate = nextState.messages.some(m => m.text === messageText && m.agent === payload.agent);
          
          if (!isDuplicate) {
            nextState.messages = [...nextState.messages, {
              id: payload.id || `msg_${Date.now()}`,
              sender: 'ai',
              role: 'assistant',
              text: messageText,
              agent: payload.agent || 'SYSTEM',
              timestamp: payload.timestamp || new Date().toISOString()
            }];
          }
        }
        break;
      }

      case 'SHELF_CARD_READY':
        nextState.shelfCards = { ...nextState.shelfCards, [payload.type]: payload.card };
        break;

      case 'UPDATE_AMBIENCE':
        nextState.ambientState = calculateAmbientState(payload.severity, payload.isConflict, payload.isHalted);
        break;

      case 'INPUT_CONFIDENCE_UPDATED':
        nextState.fusionMetrics = {
          ...(nextState.fusionMetrics || {}),
          [payload.type]: payload.score
        };
        break;

      case 'ROOM_SETTLES':
        nextState.sessionSettled = true;
        break;

      case 'OPEN_CAMERA':
        nextState.isCameraOpen = true;
        break;

      case 'CLOSE_CAMERA':
        nextState.isCameraOpen = false;
        break;

      case 'OPEN_VOICE_CALL':
        nextState.isVoiceCallOpen = true;
        break;

      case 'CLOSE_VOICE_CALL':
        nextState.isVoiceCallOpen = false;
        break;

      case 'TOGGLE_VOICE_RESPONSE':
        nextState.isVoiceResponseEnabled = !state.isVoiceResponseEnabled;
        break;

      case 'SET_VOICE_RESPONSE':
        nextState.isVoiceResponseEnabled = !!payload.enabled;
        break;

      default:
        console.warn(`[PipelineStore] Unhandled event: ${event}`);
    }

    state = nextState;
    listeners.forEach(listener => listener(state));
  }
};

import { useState, useEffect } from 'react';
import VoiceInputButton from './VoiceInputButton';
import CameraModal from './CameraModal';

const OrderPanel = ({ onSessionCreated, onAgentActivity, onOrderUpdate }) => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);

  useEffect(() => {
    createSession();
  }, []);

  const createSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/conversation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: `operator_${Date.now()}` }),
      });

      const data = await response.json();
      setSessionId(data.session_id);

      // Lift sessionId up to Kiosk so AgentActivityPanel can connect via WebSocket
      if (onSessionCreated) onSessionCreated(data.session_id);

      setMessages([
        {
          role: 'system',
          content: 'Session created successfully',
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    setIsLoading(true);
    let currentSessionId = sessionId;

    if (!currentSessionId) {
      try {
        const response = await fetch('http://localhost:8000/api/conversation/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: `operator_${Date.now()}` }),
        });

        const data = await response.json();
        currentSessionId = data.session_id;
        setSessionId(currentSessionId);
        if (onSessionCreated) onSessionCreated(currentSessionId);
      } catch (error) {
        console.error('Failed to create session on send:', error);
        setMessages((prev) => [...prev, {
          role: 'system',
          content: 'Failed to connect to server. Please verify backend is running and try again.',
          timestamp: new Date().toISOString(),
        }]);
        setIsLoading(false);
        return;
      }
    }

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputText('');

    try {
      const response = await fetch('http://localhost:8000/api/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          message: text,
        }),
      });

      const data = await response.json();

      // Notify parent about agent activity
      if (onAgentActivity) {
        onAgentActivity(data);
      }

      const assistantMessage = {
        role: 'assistant',
        content: data.message,
        intent: data.intent,
        recommendations: data.recommendations,
        severity: data.severity,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (voiceEnabled && isSupported) {
        speak(data.message);
      }

      // Extract order data from recommendations
      if (data.recommendations && data.recommendations.length > 0) {
        if (onOrderUpdate) {
          onOrderUpdate({
            patientName: 'Patient',
            prescriptionId: sessionId.substring(0, 8),
            medications: data.recommendations,
            interactionStatus: data.intent || 'pending',
            severity: data.severity,
          });
        }
      }

      // Handle client actions (e.g., open camera for prescription upload)
      if (data.client_action === 'OPEN_CAMERA') {
        setIsCameraOpen(true);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((prev) => [...prev, {
        role: 'system',
        content: `Error: ${error.message}. Check console for details.`,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputText);
  };

  const handleApprove = () => {
    alert('Order approved');
  };

  const handleEdit = () => {
    alert('Edit details');
  };

  const handleVoiceTranscription = (data) => {
    console.log("Voice transcription data:", data);
    // Determine user message content from transcription
    const transcription = data.transcription || data.message || "Voice input processed";

    // Extract order data from recommendations if present
    if (data.recommendations && data.recommendations.length > 0) {
        if (onOrderUpdate) {
            onOrderUpdate({
                patientName: 'Patient',
                prescriptionId: sessionId.substring(0, 8),
                medications: data.recommendations,
                interactionStatus: data.intent || 'pending',
                severity: data.severity,
            });
        }
    }

    // Handle client actions
    if (data.client_action === 'OPEN_CAMERA') {
      setIsCameraOpen(true);
    }

    // Add user message (transcription)
    const userMessage = {
      role: 'user',
      content: transcription,
      timestamp: new Date().toISOString(),
      isVoice: true,
      confidence: data.confidence,
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add assistant response
    const assistantMessage = {
      role: 'assistant',
      content: data.message,
      intent: data.intent,
      recommendations: data.recommendations,
      severity: data.severity,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    // Notify parent about agent activity
    if (onAgentActivity) {
      onAgentActivity(data);
    }
  };

  const handleCapture = async (blob) => {
    console.log("Captured prescription:", blob);

    // Show loading state
    setIsLoading(true);

    // Add user message
    const userMessage = {
      role: 'user',
      content: '📸 Prescription image captured',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('image', blob, 'prescription.jpg');

      // Upload to backend
      const response = await fetch(`http://localhost:8000/api/prescription/upload?session_id=${sessionId}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      console.log("Prescription processing result:", data);

      const mappedMedicines = data.medicines ? data.medicines.map(med => {
        const inStock = data.inventory_check?.in_stock?.find(
          item => item.name.toLowerCase() === med.name.toLowerCase()
        );
        const outStock = data.inventory_check?.out_of_stock?.find(
          item => item.name.toLowerCase() === med.name.toLowerCase()
        );

        return {
          medicine_name: med.name,
          dosage: med.dosage || 'N/A',
          frequency: med.frequency || 'N/A',
          duration: med.duration || 'N/A',
          price: inStock ? inStock.price : 0,
          stock: inStock ? inStock.stock : (outStock ? 'Out of Stock' : 'Unknown'),
          requires_prescription: true
        };
      }) : [];

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: data.message,
        intent: 'prescription_upload',
        recommendations: mappedMedicines,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update current order if medicines found
      if (mappedMedicines.length > 0) {
        if (onOrderUpdate) {
          onOrderUpdate({
            patientName: data.patient_info?.patient_name || 'Patient',
            prescriptionId: sessionId.substring(0, 8),
            medications: mappedMedicines,
            interactionStatus: 'prescription_processed',
          });
        }
      }

    } catch (error) {
      console.error('Failed to process prescription:', error);

      const errorMessage = {
        role: 'assistant',
        content: '❌ Failed to process prescription. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex px-4 pt-12 pb-[120px] flex-col h-full bg-[#F7F7F5] overflow-y-auto w-full max-w-4xl mx-auto relative font-sans">
      <CameraModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCapture}
      />
      
      {/* Interaction Log (Minimalist Zen) */}
      <div className="flex-1 space-y-6 w-full px-2 md:px-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50 mt-32">
            <span className="text-4xl text-[#6b8e23]">🌿</span>
            <h1 className="text-2xl font-light text-gray-800 tracking-tight">How can I help you today?</h1>
            <p className="text-sm font-medium text-gray-400">Describe your symptoms or upload a prescription.</p>
          </div>
        ) : (
          messages.map((message, index) => {
            const isUser = message.role === 'user';
            const isSystem = message.role === 'system';
            
            if (isSystem) {
              return (
                <div key={index} className="flex justify-center my-6">
                  <span className="text-xs font-medium uppercase tracking-widest text-[#a8a89a] px-4 py-1.5 rounded-full bg-[#f0f0eb]">
                    {message.content}
                  </span>
                </div>
              );
            }

            return (
              <div key={index} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-8 animate-[fadeSlideIn_0.3s_ease-out]`}>
                {!isUser && (
                  <div className="w-8 h-8 rounded-full bg-[#f0f0eb] flex-shrink-0 flex items-center justify-center mr-4 text-sm border border-[#e4e4dd]">
                    🤖
                  </div>
                )}
                
                <div className={`max-w-[85%] md:max-w-[75%] px-5 py-4 rounded-2xl shadow-sm text-base leading-relaxed ${
                  isUser 
                    ? 'bg-[#white] border border-[#e8e8e3] text-gray-800 rounded-br-sm' 
                    : 'bg-[#eef2e6] border border-[#dce5c7] text-[#3d4d1d] rounded-bl-sm'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Floating Input Capsule */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-[calc(100%-2rem)] md:max-w-2xl">
        <div className="bg-white p-2 rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-[#e4e4dd] flex items-center gap-2 group focus-within:ring-2 focus-within:ring-[#6b8e23]/20 focus-within:border-[#6b8e23] transition-all duration-300">
          
          <button 
            type="button"
            onClick={() => setIsCameraOpen(true)}
            className="p-3 text-gray-400 hover:text-[#6b8e23] hover:bg-[#F7F7F5] rounded-full transition-colors shrink-0"
            title="Upload Prescription"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
          </button>

          <form onSubmit={handleSubmit} className="flex-1 flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask me anything..."
              className="flex-1 bg-transparent px-2 py-3 focus:outline-none text-gray-800 placeholder-gray-400 font-medium"
              disabled={isLoading}
            />
            
            {/* The existing VoiceToggle is technically a complex separate component, rendering its own button. 
                We can wrap it or just use VoiceInputButton here seamlessly. */}
            <div className="shrink-0 flex items-center pr-1">
              <VoiceInputButton
                sessionId={sessionId}
                onTranscription={handleVoiceTranscription}
                disabled={isLoading || !sessionId}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="p-3 bg-[#6b8e23] text-white rounded-full hover:bg-[#556b2f] disabled:opacity-50 disabled:bg-[#a8a89a] transition-all shrink-0 shadow-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default OrderPanel;

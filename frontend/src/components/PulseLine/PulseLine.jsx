import React, { useState, useRef, useEffect } from 'react';
import { runVoiceFlowAPI, runIdentityFlowAPI } from '../../data/apiFlows';
import { pipelineStore } from '../../state/pipelineStore';
import './PulseLine.css';

const PulseLine = ({ onSubmit, placeholder, type = 'text', disabled = false }) => {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isVoiceOutputOn, setIsVoiceOutputOn] = useState(false);
  
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Subscribe to voice output state from the store
  useEffect(() => {
    const unsub = pipelineStore.subscribe((s) => {
      setIsVoiceOutputOn(s.isVoiceResponseEnabled);
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Allow Space to trigger voice recording ONLY if we aren't typing in an input text field
      if (e.code === 'Space' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        toggleRecording();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isRecording, disabled]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && !disabled && !isRecording) {
      onSubmit(value);
      setValue('');
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      
      let sessionId = pipelineStore.get().sessionId;
      if (!sessionId) {
        console.warn("No session ID found for Upload. Auto-generating anon session.");
        await runIdentityFlowAPI(`anon_${Date.now()}`);
        sessionId = pipelineStore.get().sessionId;
        
        if (!sessionId) {
          alert("Could not start session for upload. Please send a 'Hello' first.");
          if (fileInputRef.current) fileInputRef.current.value = '';
          return;
        }
      }
      
      pipelineStore.dispatch('RECORD_APPEND', { text: '📎 Prescription file uploaded...' });

      pipelineStore.dispatch('TRACE_APPEND', {
        agent: 'Vision Agent',
        step: 'file_upload_started',
        type: 'event',
        status: 'started',
        details: { message: `Uploading prescription file: ${file.name}` },
        timestamp: new Date().toISOString()
      });

      // Also show it in the chat UI
      pipelineStore.dispatch('USER_MESSAGE_SENT', {
         type: 'image',
         text: `Uploaded file: ${file.name}`,
         url: URL.createObjectURL(file) // Create a local preview URL
      });

      try {
        const formData = new FormData();
        formData.append('image', file);
        
        const url = new URL('http://localhost:8000/api/prescription/upload');
        url.searchParams.append('session_id', sessionId);
        
        const res = await fetch(url, { method: 'POST', body: formData });
        if (!res.ok) throw new Error("Upload failed");
        
        const data = await res.json();
        
        if (data.medicines && data.medicines.length > 0) {
           const meds = data.medicines.map(m => m.name);
           pipelineStore.dispatch('SHELF_CARD_READY', {
             type: 'medical',
             card: { title: 'EXTRACTED MEDICINES', severity: 0, content: meds }
           });

           // Trigger CHECKOUT_READY with the extracted medicines
           let totalPrice = 0;
           const items = data.medicines.map(m => {
              totalPrice += m.price || 0;
              return { 
                name: m.name, 
                stockStatus: m.available ? 'In Stock' : 'Out of Stock', 
                price: m.price || 0,
                warnings: m.warnings || [],
                substitute: m.substitute || null
              };
           });

           pipelineStore.dispatch('CHECKOUT_READY', {
             orderSummary: {
               pid: sessionId, // Use session ID as fallback PID for uploads
               complaint: "Prescription Upload",
               validation: { status: 'Pending Review', severity: 0 },
               items,
               substitutions: [],
               totalPrice,
               orderId: `ORD-${Date.now().toString().slice(-4)}`
             }
           });
        }
        
        pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
           text: data.message,
           footnotes: [{ agent: 'Vision', text: `Status: ${data.extraction_status}` }]
        });

        pipelineStore.dispatch('INPUT_CONFIDENCE_UPDATED', {
          type: 'vision',
          score: data.extraction_status === 'success' ? Math.floor(Math.random() * 15 + 85) : 0
        });

        pipelineStore.dispatch('TRACE_APPEND', {
          agent: 'Vision Agent',
          step: 'file_upload_completed',
          type: 'event',
          status: 'completed',
          details: { message: `Prescription file processed: ${data.extraction_status}`, medicines_found: data.medicines?.length || 0 },
          timestamp: new Date().toISOString()
        });
      } catch (err) {
        console.error("File upload error:", err);
        pipelineStore.dispatch('TRACE_APPEND', { 
          agent: 'SYSTEM', 
          step: `Upload Error: ${err.message}`, 
          type: 'error',
          status: 'failed',
          timestamp: new Date().toISOString()
        });
      }
      
      // Reset input so they can upload the exact same file again if it failed
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleTriggerCamera = () => {
    pipelineStore.dispatch('OPEN_CAMERA', {});
    pipelineStore.dispatch('RECORD_APPEND', { text: '📷 Opening camera for prescription scan...' });
  };

  const toggleRecording = async () => {
    if (disabled) return;
    
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunksRef.current = [];

        // Auto-enable voice output when user starts talking
        if (!pipelineStore.get().isVoiceResponseEnabled) {
          pipelineStore.dispatch('SET_VOICE_RESPONSE', { enabled: true });
        }

        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

          mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current.mimeType || 'audio/webm' });
          console.log("Audio Blob created, size:", audioBlob.size, "type:", audioBlob.type);
          if (audioBlob.size === 0) {
            alert("Recording was empty. Please check your microphone.");
            return;
          }
          
          // Show voice visualizer in the chat UI
          pipelineStore.dispatch('USER_MESSAGE_SENT', {
             type: 'audio',
             text: `Voice recording (${(audioBlob.size / 1024).toFixed(1)} KB)`
          });

          runVoiceFlowAPI(audioBlob);
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorderRef.current.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Microphone access denied or error:", err);
        alert(`Microphone error: ${err.message}`);
      }
    }
  };

  return (
    <div className={`pulse-line-container ${isFocused ? 'focused' : ''} ${disabled ? 'disabled' : ''} ${isRecording ? 'recording' : ''}`}>
      <form onSubmit={handleSubmit} className="pulse-line-form">
        <button 
          type="button" 
          className="pulse-action-btn"
          onClick={() => fileInputRef.current.click()}
          disabled={disabled}
          title="Upload Prescription (PDF/IMG)"
        >
          📎
        </button>
        <input 
          type="file" 
          ref={fileInputRef}
          className="hidden-file-input"
          onChange={handleFileChange}
          accept="image/*,application/pdf"
          disabled={disabled}
        />
        
        <button 
          type="button" 
          className="pulse-action-btn"
          onClick={handleTriggerCamera}
          disabled={disabled}
          title="Scan Prescription via Camera"
        >
          📷
        </button>

        <input
          type="text"
          className="pulse-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={isRecording ? "Listening... (Press Space to stop)" : placeholder}
          disabled={disabled || isRecording}
          autoComplete="off"
        />
        
        {isRecording && (
          <div className="voice-waveform-indicator">
            <span className="waveform-bar"></span>
            <span className="waveform-bar"></span>
            <span className="waveform-bar"></span>
            <span className="waveform-bar"></span>
            <span className="waveform-bar"></span>
          </div>
        )}

        <button 
          type="button" 
          className={`pulse-mic-btn ${isRecording ? 'active' : ''}`}
          onClick={toggleRecording}
          disabled={disabled}
          title="Toggle Voice Input (Space)"
        >
          {isRecording ? '⏹️' : '🎙️'}
        </button>

        <button
          type="button"
          className={`pulse-action-btn voice-output-toggle ${isVoiceOutputOn ? 'active' : ''}`}
          onClick={() => pipelineStore.dispatch('TOGGLE_VOICE_RESPONSE', {})}
          disabled={disabled}
          title={isVoiceOutputOn ? 'Voice Output ON (click to mute)' : 'Voice Output OFF (click to enable)'}
        >
          {isVoiceOutputOn ? '🔊' : '🔇'}
        </button>
      </form>
    </div>
  );
};

export default PulseLine;

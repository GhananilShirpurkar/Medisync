import { useState, useRef, useEffect } from 'react';

/**
 * VoiceInputButton Component
 * 
 * Push-to-talk voice input with audio recording.
 * Records audio and sends to backend for transcription.
 */
const VoiceInputButton = ({ sessionId, onTranscription, disabled }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [isSupported, setIsSupported] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  useEffect(() => {
    // Check if browser supports MediaRecorder
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      setIsSupported(true);
    }

    // Cleanup on unmount
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    if (!isSupported) {
      setError('Voice input not supported in your browser');
      return;
    }

    if (!sessionId) {
      setError('No active session');
      return;
    }

    try {
      setError(null);
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000, // Whisper's native sample rate
        } 
      });
      
      streamRef.current = stream;

      // Create MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : 'audio/mp4';
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        await sendAudioToBackend(audioBlob);
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (err) {
      console.error('Error starting recording:', err);
      
      if (err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone access.');
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone.');
      } else {
        setError('Failed to start recording. Please try again.');
      }
      
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendAudioToBackend = async (audioBlob) => {
    try {
      // Create form data
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      // Send to backend
      const response = await fetch(
        `http://localhost:8000/api/conversation/voice?session_id=${sessionId}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Call callback with transcription and response
      if (onTranscription) {
        onTranscription({
          transcription: data.transcription,
          confidence: data.transcription_confidence,
          language: data.language,
          message: data.message,
          recommendations: data.recommendations,
        });
      }

      setIsProcessing(false);
      
    } catch (err) {
      console.error('Error sending audio:', err);
      setError('Failed to process audio. Please try again.');
      setIsProcessing(false);
    }
  };

  const handleMouseDown = () => {
    if (!disabled && !isProcessing) {
      startRecording();
    }
  };

  const handleMouseUp = () => {
    if (isRecording) {
      stopRecording();
    }
  };

  const handleTouchStart = (e) => {
    e.preventDefault();
    if (!disabled && !isProcessing) {
      startRecording();
    }
  };

  const handleTouchEnd = (e) => {
    e.preventDefault();
    if (isRecording) {
      stopRecording();
    }
  };

  if (!isSupported) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-500">
        <span>🎤</span>
        <span>Voice input not supported</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp} // Stop if mouse leaves while holding
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        disabled={disabled || isProcessing}
        className={`relative w-16 h-16 rounded-full font-bold transition-all duration-200 transform active:scale-95 touch-target ${
          isRecording
            ? 'bg-red-600 text-white shadow-xl shadow-red-500/50 animate-pulse scale-110'
            : isProcessing
            ? 'bg-blue-400 text-white cursor-wait'
            : disabled
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl hover:scale-105'
        }`}
        title={
          isRecording
            ? 'Release to send'
            : isProcessing
            ? 'Processing...'
            : 'Hold to speak'
        }
        aria-label={
          isRecording
            ? 'Recording voice input, release to send'
            : isProcessing
            ? 'Processing voice input'
            : 'Hold to record voice input'
        }
      >
        {isProcessing ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-7 w-7 border-3 border-white border-t-transparent"></div>
          </div>
        ) : (
          <span className="text-3xl">
            {isRecording ? '🔴' : '🎤'}
          </span>
        )}
        
        {/* Recording pulse ring */}
        {isRecording && (
          <span className="absolute inset-0 rounded-full bg-red-600 animate-ping opacity-75"></span>
        )}
      </button>

      {/* Status Text */}
      <div className="text-center min-h-[2.5rem]">
        {isRecording && (
          <p className="text-sm font-semibold text-red-600 animate-pulse">
            🎙️ Recording... Release to send
          </p>
        )}
        {isProcessing && (
          <p className="text-sm font-semibold text-blue-600">
            ⏳ Processing audio...
          </p>
        )}
        {!isRecording && !isProcessing && !error && (
          <p className="text-xs text-gray-500 font-medium">
            Hold to speak
          </p>
        )}
        {error && (
          <p className="text-xs text-red-600 max-w-xs font-medium">
            ⚠️ {error}
          </p>
        )}
      </div>

      {/* Recording Indicator Dots */}
      {isRecording && (
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 bg-red-600 rounded-full animate-pulse"></div>
          <div className="w-2.5 h-2.5 bg-red-600 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2.5 h-2.5 bg-red-600 rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
        </div>
      )}
    </div>
  );
};

export default VoiceInputButton;

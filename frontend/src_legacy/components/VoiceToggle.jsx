import { useState, useEffect } from 'react';

/**
 * VoiceToggle Component
 * 
 * Provides text-to-speech functionality using Browser SpeechSynthesis API.
 * Allows users to toggle voice output on/off.
 */
const VoiceToggle = ({ enabled, onToggle }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    // Check if browser supports SpeechSynthesis
    if ('speechSynthesis' in window) {
      setIsSupported(true);
    }
  }, []);

  const handleToggle = () => {
    if (!isSupported) {
      alert('Voice output is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    // Stop any ongoing speech when toggling off
    if (enabled && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    onToggle(!enabled);
  };

  // Listen for speech events
  useEffect(() => {
    if (!isSupported) return;

    const handleStart = () => setIsSpeaking(true);
    const handleEnd = () => setIsSpeaking(false);

    // Note: These events are on utterances, not the global speechSynthesis
    // We'll track speaking state through the speak function instead

    return () => {
      // Cleanup
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isSupported]);

  if (!isSupported) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-500">
        <span>🔇</span>
        <span>Voice not supported</span>
      </div>
    );
  }

  return (
    <button
      onClick={handleToggle}
      className={`flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-soft hover:shadow-medium touch-target ${
        enabled
          ? 'bg-white text-blue-600 hover:bg-blue-50'
          : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm'
      }`}
      title={enabled ? 'Voice output enabled - Click to disable' : 'Voice output disabled - Click to enable'}
      aria-label={enabled ? 'Disable voice output' : 'Enable voice output'}
      aria-pressed={enabled}
    >
      <span className="text-xl">
        {isSpeaking ? '🔊' : enabled ? '🔉' : '🔇'}
      </span>
      <span className="text-sm font-semibold">
        {isSpeaking ? 'Speaking...' : enabled ? 'Voice On' : 'Voice Off'}
      </span>
    </button>
  );
};

/**
 * useSpeechSynthesis Hook
 * 
 * Custom hook for text-to-speech functionality.
 */
export const useSpeechSynthesis = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState([]);

  useEffect(() => {
    if ('speechSynthesis' in window) {
      setIsSupported(true);

      // Load voices
      const loadVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices();
        setVoices(availableVoices);
      };

      loadVoices();

      // Voices may load asynchronously
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }
    }
  }, []);

  const speak = (text, options = {}) => {
    if (!isSupported) {
      console.warn('SpeechSynthesis not supported');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(text);

    // Set options
    utterance.rate = options.rate || 1.0; // 0.1 to 10
    utterance.pitch = options.pitch || 1.0; // 0 to 2
    utterance.volume = options.volume || 1.0; // 0 to 1

    // Select voice (prefer English voices)
    if (options.voice) {
      utterance.voice = options.voice;
    } else if (voices.length > 0) {
      // Try to find an English voice
      const englishVoice = voices.find(
        (voice) => voice.lang.startsWith('en-')
      );
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
    }

    // Event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
      if (options.onStart) options.onStart();
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      if (options.onEnd) options.onEnd();
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      if (options.onError) options.onError(event);
    };

    // Speak
    window.speechSynthesis.speak(utterance);
  };

  const stop = () => {
    if (isSupported && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const pause = () => {
    if (isSupported && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
    }
  };

  const resume = () => {
    if (isSupported && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  };

  return {
    isSupported,
    isSpeaking,
    voices,
    speak,
    stop,
    pause,
    resume,
  };
};

export default VoiceToggle;

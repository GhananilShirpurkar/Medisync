import { useState, useEffect, useRef } from 'react';
import VoiceToggle, { useSpeechSynthesis } from './VoiceToggle';
import VoiceInputButton from './VoiceInputButton';
import AgentTimeline from './AgentTimeline';

const ConversationalInterface = () => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [lastResponse, setLastResponse] = useState(null);
  const [showTimeline, setShowTimeline] = useState(false);
  const [severity, setSeverity] = useState(null);
  const messagesEndRef = useRef(null);

  const { isSupported, isSpeaking, speak, stop } = useSpeechSynthesis();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    createSession();
  }, []);

  const createSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/conversation/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: `user_${Date.now()}`,
        }),
      });

      const data = await response.json();
      setSessionId(data.session_id);

      const welcomeMessage = data.message || "Hello! I'm your MediSync pharmacy assistant. How can I help you today?";

      setMessages([
        {
          role: 'assistant',
          content: welcomeMessage,
          timestamp: new Date().toISOString(),
        },
      ]);

      // Don't auto-speak welcome message - let user enable voice first
      // This respects user preference and accessibility guidelines
    } catch (error) {
      console.error('Failed to create session:', error);
      setMessages([
        {
          role: 'system',
          content: 'Failed to connect to server. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ]);
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
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: `user_${Date.now()}`,
          }),
        });

        const data = await response.json();
        currentSessionId = data.session_id;
        setSessionId(currentSessionId);
      } catch (error) {
        console.error('Failed to create session on send:', error);
        setMessages((prev) => [
          ...prev,
          {
            role: 'system',
            content: 'Failed to connect to server. Please verify backend is running and try again.',
            timestamp: new Date().toISOString(),
          },
        ]);
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
    setShowTimeline(true);

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
      setLastResponse(data);

      // Extract severity if available
      if (data.severity_assessment) {
        setSeverity(data.severity_assessment);
      }

      const assistantMessage = {
        role: 'assistant',
        content: data.message,
        intent: data.intent,
        recommendations: data.recommendations,
        severity: data.severity_assessment,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (voiceEnabled && isSupported) {
        speak(data.message);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputText);
  };

  const handleVoiceToggle = (enabled) => {
    setVoiceEnabled(enabled);

    if (!enabled && isSpeaking) {
      stop();
    }
  };

  const handleVoiceTranscription = (data) => {
    setLastResponse(data);
    setShowTimeline(true);

    if (data.severity_assessment) {
      setSeverity(data.severity_assessment);
    }

    const userMessage = {
      role: 'user',
      content: data.transcription,
      timestamp: new Date().toISOString(),
      isVoice: true,
      confidence: data.confidence,
    };
    setMessages((prev) => [...prev, userMessage]);

    const assistantMessage = {
      role: 'assistant',
      content: data.message,
      recommendations: data.recommendations,
      severity: data.severity_assessment,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    if (voiceEnabled && isSupported) {
      speak(data.message);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-4 h-full">
      {/* Main Chat Interface */}
      <div className={`flex flex-col bg-white rounded-2xl shadow-xl ${showTimeline ? 'lg:w-2/3' : 'w-full'}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-2xl">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span>💬</span>
              <span>AI Assistant</span>
            </h2>
            <p className="text-sm text-blue-100 mt-1 flex items-center gap-2">
              {sessionId ? (
                <>
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                  <span>Active</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></span>
                  <span>Connecting...</span>
                </>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end">
              <VoiceToggle enabled={voiceEnabled} onToggle={handleVoiceToggle} />
              {!voiceEnabled && (
                <p className="text-xs text-blue-100 mt-1">Click to enable voice output</p>
              )}
            </div>
            {showTimeline && (
              <button
                onClick={() => setShowTimeline(!showTimeline)}
                className="lg:hidden px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-all"
              >
                {showTimeline ? 'Hide' : 'Show'} Timeline
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
          {isLoading && (
            <div className="flex items-center gap-3 text-gray-500">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-gray-300 border-t-blue-600"></div>
              <span className="text-sm font-medium">Processing...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t bg-white rounded-b-2xl">
          <div className="flex gap-2 items-end">
            <div className="flex-shrink-0">
              <VoiceInputButton
                sessionId={sessionId}
                onTranscription={handleVoiceTranscription}
                disabled={isLoading || !sessionId}
              />
            </div>

            <div className="flex-1 flex gap-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your message or use voice..."
                className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !inputText.trim()}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
              >
                Send
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Agent Timeline Sidebar */}
      {showTimeline && lastResponse && (
        <div className="lg:w-1/3 max-h-[600px] overflow-y-auto">
          <AgentTimeline
            conversationData={lastResponse}
            isProcessing={isLoading}
            mode="conversation"
          />
        </div>
      )}
    </div>
  );
};

const getSeverityBadge = (severity) => {
  if (!severity) return null;

  const score = severity.severity_score || severity.score || 0;

  if (score >= 9) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-100 border-2 border-red-500 rounded-lg animate-pulse">
        <span className="text-red-600 font-bold">🚨 EMERGENCY</span>
        <span className="text-red-900 font-bold">{score}/10</span>
      </div>
    );
  } else if (score >= 7) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-50 border-2 border-red-400 rounded-lg">
        <span className="text-red-600 font-bold">⚠️ High Risk</span>
        <span className="text-red-900 font-bold">{score}/10</span>
      </div>
    );
  } else if (score >= 4) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-orange-50 border-2 border-orange-400 rounded-lg">
        <span className="text-orange-600 font-bold">⚡ Moderate</span>
        <span className="text-orange-900 font-bold">{score}/10</span>
      </div>
    );
  } else {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-green-50 border-2 border-green-400 rounded-lg">
        <span className="text-green-600 font-bold">✓ Low Risk</span>
        <span className="text-green-900 font-bold">{score}/10</span>
      </div>
    );
  }
};

const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="px-4 py-2 bg-yellow-50 text-yellow-800 text-sm rounded-xl border border-yellow-200">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl ${isUser
          ? 'bg-blue-600 text-white rounded-br-sm'
          : 'bg-white text-gray-900 rounded-bl-sm border border-gray-200'
          }`}
      >
        {isUser && message.isVoice && (
          <div className="flex items-center gap-2 mb-2 text-xs opacity-90 bg-white/10 rounded-lg px-2 py-1">
            <span>🎤</span>
            <span>Voice message</span>
          </div>
        )}

        <p className="text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>

        {/* Severity Badge */}
        {message.severity && !isUser && (
          <div className="mt-3">
            {getSeverityBadge(message.severity)}
          </div>
        )}

        {/* Recommendations */}
        {message.recommendations && message.recommendations.length > 0 && (
          <div className="mt-4 space-y-2">
            {message.recommendations.map((rec, index) => (
              <div
                key={index}
                className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-gray-900"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="font-bold text-base mb-1">{rec.medicine_name}</p>
                    <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                      <span className="font-semibold text-green-600">₹{rec.price}</span>
                      <span>•</span>
                      <span>Stock: <span className="font-semibold">{rec.stock}</span></span>
                    </div>
                    {rec.requires_prescription && (
                      <p className="text-xs text-orange-600 font-medium flex items-center gap-1 bg-orange-50 px-2 py-1 rounded-lg inline-flex">
                        <span>⚠️</span>
                        <span>Requires prescription</span>
                      </p>
                    )}
                  </div>
                  <button
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-all"
                    onClick={() => alert('Add to cart functionality coming soon!')}
                  >
                    Add
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="text-xs mt-2 opacity-70">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

export default ConversationalInterface;

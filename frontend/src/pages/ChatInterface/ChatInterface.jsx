import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Paperclip, Settings, MessageSquare, Plus, Activity, Dna, Pill } from 'lucide-react';
import { pipelineStore } from '../../state/pipelineStore';
import { runIdentityFlowAPI } from '../../data/apiFlows';
import { toast } from 'react-hot-toast';
import logoImage from '../../assets/logo.jpeg';
import './ChatInterface.css';

const ChatInterface = () => {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);

  const handlePhoneSubmit = async (e) => {
    if (e) e.preventDefault();
    if (isLoading || !inputValue) return;

    if (inputValue.trim() === '0000000000') {
      pipelineStore.dispatch('IDENTITY_RESOLVED', {
        pid: 'DEMO-001',
        phone: '0000000000',
        patientName: 'Demo Patient',
        isDemo: true,
        previousOrder: 'Paracetamol 500mg'
      });
      navigate('/app');
      return;
    }

    const digits = inputValue.replace(/\D/g, '');
    
    if (digits.length >= 10) {
      const cleanPhone = digits.slice(-10);
      setIsLoading(true);
      try {
        await runIdentityFlowAPI(cleanPhone);
        navigate('/app');
      } catch (err) {
        toast.error("Network Error: Backend unreachable");
        setIsLoading(false);
        setIsError(true);
        setTimeout(() => setIsError(false), 400);
      }
    } else {
      setIsError(true);
      setTimeout(() => setIsError(false), 400);
    }
  };

  return (
    <div className="chat-interface">
      {/* ANIMATED BACKGROUND */}
      <div className="chat-bg-mesh">
        <div className="mesh-blob mesh-blob-1" />
        <div className="mesh-blob mesh-blob-2" />
        <div className="mesh-blob mesh-blob-3" />
        <div className="mesh-blob mesh-blob-4" />
        <div className="mesh-blob mesh-blob-5" />
        {/* Floating 3D Medical Elements */}
        <div className="floating-emoji emoji-1">💊</div>
        <div className="floating-emoji emoji-2">💊</div>
        <div className="floating-emoji emoji-3">💊</div>
        <div className="floating-emoji emoji-4">🩺</div>
        <div className="floating-emoji emoji-5">🧪</div>
        <div className="floating-emoji emoji-6">💉</div>
        <div className="floating-emoji emoji-7">🔬</div>
        <div className="floating-emoji emoji-8">💓</div>
        <div className="floating-emoji emoji-9">🩹</div>
        {/* Additional Injection and Stethoscope icons */}
        <div className="floating-emoji emoji-10">💉</div>
        <div className="floating-emoji emoji-11">💉</div>
        <div className="floating-emoji emoji-12">🩺</div>
        {/* Lucide 3D Icons */}
        <div className="chat-decor chat-decor--steth">
          <Activity size={48} strokeWidth={1} />
        </div>
        <div className="chat-decor chat-decor--pulse">
          <Activity size={64} strokeWidth={0.5} />
        </div>
        {/* CSS 3D Medical Cross */}
        <div className="chat-decor chat-decor--3d-cross">
          <div className="cross-3d">
            <div className="cross-bar horizontal" />
            <div className="cross-bar vertical" />
          </div>
        </div>
      </div>

      {/* HEADER */}
      <header className="chat-header">
        <div className="chat-logo-group" onClick={() => navigate('/')}>
          <div className="chat-logo-image-container">
            <img src={logoImage} alt="MediSync Logo" className="chat-logo-image" />
          </div>
          <span className="chat-logo-text">MEDISYNC</span>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="chat-main">
        <div className="chat-content-wrapper">
          <h1 className="chat-question">What brings you in today?</h1>
          
          <form onSubmit={handlePhoneSubmit} className={`chat-input-container ${isFocused ? 'is-focused' : ''} ${isError ? 'error-flash' : ''}`}>
            {isLoading ? (
              <div className="chat-input" style={{display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0066FF', fontWeight: 'bold'}}>
                Initializing secure session...
              </div>
            ) : (
              <>
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Enter Your Mobile Number..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  autoComplete="off"
                />
                <button type="submit" style={{ display: 'none' }} />
                <div className="chat-input-underline" />
              </>
            )}
          </form>

        </div>
      </main>

      {/* 3D CHARACTER ELEMENTS */}
      <div className="chat-bot-container chat-bot-container--left">
        <div className="chat-bot chat-bot--green">
          {/* Typing Indicator Animation */}
          <div className="bot-typing-indicator bot-typing-indicator--green">
            <div className="dot" />
            <div className="dot" />
            <div className="dot" />
          </div>
          <div className="bot-antenna">
            <div className="bot-antenna-tip" />
          </div>
          <div className="bot-head">
            <div className="bot-face">
              <div className="bot-eye left" />
              <div className="bot-eye right" />
            </div>
            <div className="bot-headset">
              <div className="bot-mic" />
            </div>
          </div>
          <div className="bot-body" />
          <div className="bot-shadow" />
        </div>
      </div>

      <div className="chat-bot-container chat-bot-container--right">
        <div className="chat-bot">
          <div className="bot-antenna">
            <div className="bot-antenna-tip" />
          </div>
          <div className="bot-head">
            <div className="bot-face">
              <div className="bot-eye left" />
              <div className="bot-eye right" />
            </div>
            <div className="bot-headset">
              <div className="bot-mic" />
            </div>
          </div>
          <div className="bot-body" />
          <div className="bot-shadow" />
          
          {/* Floating Speech Bubble for typing indicator */}
          <div className="bot-typing-indicator">
            <div className="dot" />
            <div className="dot" />
            <div className="dot" />
          </div>
        </div>
      </div>

      {/* FLOATING DECORATIVE ELEMENTS */}
      <div className="chat-decor chat-decor--settings">
        <Settings size={24} />
      </div>
      
      <div className="chat-decor chat-decor--cross">
        <Plus size={32} strokeWidth={3} />
      </div>

      <div className="chat-decor chat-decor--dna">
        <Dna size={40} />
      </div>
    </div>
  );
};

export default ChatInterface;
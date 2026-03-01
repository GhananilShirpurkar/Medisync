import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Paperclip, Settings, MessageSquare, Plus, Activity, Dna, Pill } from 'lucide-react';
import { pipelineStore } from '../../state/pipelineStore';
import { runIdentityFlowAPI, sendOTPAPI, verifyOTPAPI } from '../../data/apiFlows';

import { toast } from 'react-hot-toast';
import logoImage from '../../assets/logo.jpeg';
import './ChatInterface.css';

const ChatInterface = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState('phone'); // 'phone' or 'otp'
  const [inputValue, setInputValue] = useState('');
  const [otpValue, setOtpValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);


  const cleanPhone = (val) => val.replace(/\D/g, '');

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
      const phone = cleanPhone(digits);
      setIsLoading(true);
      try {
        await sendOTPAPI(phone);
        toast.success("Verification code sent to WhatsApp!");
        setStep('otp');
        setIsLoading(false);
      } catch (err) {
        console.error("[IdentityFlow] OTP Send Error:", err);
        toast.error("Failed to send verification code. Check WhatsApp Sandbox session.");
        setIsLoading(false);
        triggerError();
      }
    } else {
      triggerError();
    }
  };

  const handleOTPSubmit = async (e) => {
    if (e) e.preventDefault();
    if (isLoading) return;

    if (otpValue.length === 4) {
      setIsLoading(true);
      const phone = cleanPhone(inputValue);
      try {
        await verifyOTPAPI(phone, otpValue);
        toast.success("Identity verified!");
        
        // Final resolution
        await runIdentityFlowAPI(phone);
        navigate('/app');
      } catch (err) {
        console.error("[IdentityFlow] OTP Verify Error:", err);
        toast.error(err.message || "Invalid or expired code.");
        setIsLoading(false);
        setOtpValue('');
        triggerError();
      }
    } else {
      triggerError();
    }
  };

  const triggerError = () => {
    setIsError(true);
    setTimeout(() => setIsError(false), 400);
  };

  return (
    <div className={`chat-interface ${step === 'otp' ? 'modal-open' : ''}`}>
      {/* ANIMATED BACKGROUND */}
      <div className={`chat-bg-mesh ${step === 'otp' ? 'blurred-bg-mesh' : ''}`}>
        <div className="mesh-blob mesh-blob-1" />
        <div className="mesh-blob mesh-blob-2" />
        <div className="mesh-blob mesh-blob-3" />
        <div className="mesh-blob mesh-blob-4" />
        <div className="mesh-blob mesh-blob-5" />
        {/* Floating 3D Medical Elements */}
        {/* ... (rest of background remains same) */}
      </div>

      {/* HEADER */}
      <header className={`chat-header ${step === 'otp' ? 'blurred-bg-header' : ''}`}>
        <div className="chat-logo-group" onClick={() => navigate('/')}>
          <div className="chat-logo-image-container">
            <img src={logoImage} alt="MediSync Logo" className="chat-logo-image" />
          </div>
          <span className="chat-logo-text">MEDISYNC</span>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className={`chat-main ${step === 'otp' ? 'blurred-bg' : ''}`}>
        <div className="chat-content-wrapper">
          <h1 className="chat-question">What brings you in today?</h1>
          
          <form onSubmit={handlePhoneSubmit} className={`chat-input-container ${isFocused ? 'is-focused' : ''} ${isError ? 'error-flash' : ''}`}>
            {isLoading && step === 'phone' ? (
              <div className="chat-input" style={{display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0066FF', fontWeight: 'bold'}}>
                Sending code...
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
                  disabled={step === 'otp'}
                />
                <button type="submit" style={{ display: 'none' }} />
                <div className="chat-input-underline" />
              </>
            )}
          </form>
        </div>
      </main>

      {/* OTP MODAL */}
      {step === 'otp' && (
        <div className="otp-modal-overlay">
          <div className="otp-modal-content">
            <h2 className="otp-modal-title">Verification</h2>
            <p className="otp-modal-desc">
              We've sent a 4-digit code to <br/>
              <strong>{inputValue}</strong> via WhatsApp.
            </p>
            
            <form onSubmit={handleOTPSubmit} className="chat-form-otp">
              <div className={`chat-input-container is-focused ${isError ? 'error-flash' : ''}`}>
                <input 
                  type="text"
                  className="chat-input"
                  value={otpValue}
                  onChange={(e) => setOtpValue(e.target.value)}
                  placeholder="Code"
                  autoComplete="off"
                  maxLength={4}
                  autoFocus
                />
                <button type="submit" style={{ display: 'none' }} />
                <div className="chat-input-underline" />
              </div>
              
              <div className="otp-modal-actions">
                {isLoading ? (
                  <div className="identity-status">Verifying...</div>
                ) : (
                  <>
                    <button type="submit" className="otp-confirm-btn">Confirm</button>
                    <div className="otp-hint" onClick={() => setStep('phone')}>
                      ← Back
                    </div>
                  </>
                )}
              </div>
            </form>
          </div>
        </div>
      )}


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
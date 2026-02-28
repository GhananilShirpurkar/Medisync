import React, { useState, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { pipelineStore } from '../../state/pipelineStore';
import { runIdentityFlowAPI, sendOTPAPI, verifyOTPAPI } from '../../data/apiFlows';
import './IdentityPage.css';

const IdentityPage = () => {
  const [step, setStep] = useState('phone'); // 'phone' or 'otp'
  const [phoneValue, setPhoneValue] = useState('');
  const [otpValue, setOtpValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef(null);

  const cleanPhone = (val) => val.replace(/\D/g, '').slice(-10);

  const handlePhoneSubmit = async (e) => {
    if (e) e.preventDefault();
    if (isLoading) return;

    if (phoneValue.trim() === '0000000000') {
      pipelineStore.dispatch('IDENTITY_RESOLVED', {
        pid: 'DEMO-001',
        phone: '0000000000',
        patientName: 'Demo Patient',
        isDemo: true,
        previousOrder: 'Paracetamol 500mg'
      });
      return;
    }

    const digits = phoneValue.replace(/\D/g, '');
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
      const phone = cleanPhone(phoneValue);
      try {
        await verifyOTPAPI(phone, otpValue);
        toast.success("Identity verified!");
        
        // Final resolution
        await runIdentityFlowAPI(phone);
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

  const handleFileUpload = (e) => {
    if (e.target.files?.length > 0) {
      pipelineStore.dispatch('prescription_uploaded', {});
    }
  };

  return (
    <div className={`identity-container ${step === 'otp' ? 'modal-open' : ''}`}>
      <div className="identity-wordmark">MEDISYNC</div>

      <div className={`identity-content ${step === 'otp' ? 'blurred-bg' : ''}`}>
        <h1 className="identity-prompt">
          What brings you in today?
        </h1>
        
        <div className="identity-input-area">
          {isLoading && step === 'phone' ? (
            <div className="identity-status">Sending code...</div>
          ) : (
            <form onSubmit={handlePhoneSubmit} className="identity-form">
              <div className={`input-line-wrapper ${isFocused ? 'focused' : ''} ${isError ? 'error-flash' : ''}`}>
                <input 
                  type="text"
                  className="identity-input-line"
                  value={phoneValue}
                  onChange={(e) => setPhoneValue(e.target.value)}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  placeholder="Enter your phone number..."
                  autoComplete="off"
                  disabled={step === 'otp'}
                />
                <button type="submit" style={{ display: 'none' }} />
              </div>
            </form>
          )}
        </div>

        <div className="identity-labels">
          <span className="identity-label">ENTER PHONE NUMBER</span>
          <span className="identity-label upload-trigger" onClick={() => fileInputRef.current.click()}>
            UPLOAD PRESCRIPTION
          </span>
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden-file-input" 
            accept="image/*"
            onChange={handleFileUpload}
          />
        </div>
      </div>

      {step === 'otp' && (
        <div className="otp-modal-overlay">
          <div className="otp-modal-content">
            <h2 className="otp-modal-title">Verification</h2>
            <p className="otp-modal-desc">
              We've sent a 4-digit code to <br/>
              <strong>{phoneValue}</strong> via WhatsApp.
            </p>
            
            <form onSubmit={handleOTPSubmit} className="identity-form">
              <div className={`input-line-wrapper focused ${isError ? 'error-flash' : ''}`}>
                <input 
                  type="text"
                  className="identity-input-line"
                  value={otpValue}
                  onChange={(e) => setOtpValue(e.target.value)}
                  placeholder="Code"
                  autoComplete="off"
                  maxLength={4}
                  autoFocus
                />
                <button type="submit" style={{ display: 'none' }} />
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
    </div>
  );
};


export default IdentityPage;


import React, { useState, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { pipelineStore } from '../../state/pipelineStore';
import { runIdentityFlowAPI } from '../../data/apiFlows';
import './IdentityPage.css';

const IdentityPage = () => {
  const [phoneValue, setPhoneValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef(null);

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

    // Clean input: remove all non-digits
    const digits = phoneValue.replace(/\D/g, '');
    
    // Support 10+ digits (handle country code such as +91)
    if (digits.length >= 10) {
      const cleanPhone = digits.slice(-10); // Take last 10 digits
      setIsLoading(true);
      console.log(`[IdentityFlow] Attempting resolution for: ${cleanPhone}`);
      try {
        await runIdentityFlowAPI(cleanPhone);
        // Successful API call will dispatch identity_resolved
        // which triggers navigation in the central store.
      } catch (err) {
        console.error("[IdentityFlow] API Error:", err);
        toast.error("Network Error: Backend unreachable (localhost:8000)");
        setIsLoading(false);
        triggerError();
      }
    } else {
      console.warn(`[IdentityFlow] Invalid length: ${digits.length}`);
      triggerError();
    }
  };

  const triggerError = () => {
    setIsError(true);
    setTimeout(() => setIsError(false), 400);
  };

  const handleFileUpload = (e) => {
    if (e.target.files?.length > 0) {
      // Direct transition to Theatre as per spec
      pipelineStore.dispatch('prescription_uploaded', {});
      // In a real app, we'd upload here. 
      // demoFlows.js or similar would be triggered by this state change.
    }
  };

  return (
    <div className="identity-container">
      {/* Fix 3: MediSync Wordmark */}
      <div className="identity-wordmark">MEDISYNC</div>

      <div className="identity-content">
        <h1 className="identity-prompt">
          What brings you in today?
        </h1>
        
        <div className="identity-input-area">
          {isLoading ? (
            <div className="identity-status">Initializing secure session...</div>
          ) : (
            <form onSubmit={handlePhoneSubmit} className="identity-form">
              {/* Fix 1: Minimal Line Input */}
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
                />
                {/* Hidden submit to ensure Enter always triggers onSubmit */}
                <button type="submit" style={{ display: 'none' }} />
              </div>
            </form>
          )}
        </div>

        {/* Fix 2: Static Mode Labels */}
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
    </div>
  );
};

export default IdentityPage;

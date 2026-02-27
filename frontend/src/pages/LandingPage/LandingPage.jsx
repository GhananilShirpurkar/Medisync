import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [showButtons, setShowButtons] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowButtons(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="landing-page">
      <div className="landing-brand">MEDISYNC</div>
      
      <div className="landing-center">
        <h1 className="landing-title">MEDISYNC</h1>
        <div className="landing-tagline">
          <p className="landing-tagline-primary">Intelligent Pharmacy Management</p>
          <p className="landing-tagline-secondary">Powered by a multi-agent AI pipeline</p>
        </div>
        
        <div className="landing-buttons">
          <button 
            className={`landing-btn landing-btn-customer ${showButtons ? 'visible' : ''}`}
            onClick={() => navigate('/app')}
          >
            [ PATIENT CONSULTATION ]
          </button>
          <button 
            className={`landing-btn landing-btn-admin ${showButtons ? 'visible delay' : ''}`}
            onClick={() => navigate('/admin')}
          >
            [ ADMIN OPERATIONS ]
          </button>
        </div>
        
        <div className="landing-footer">
          v1.0 &middot; Hackathon Build &middot; 2026
        </div>
      </div>
    </div>
  );
};

export default LandingPage;

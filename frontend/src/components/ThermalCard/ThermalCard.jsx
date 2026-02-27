import React, { useEffect, useState } from 'react';
import './ThermalCard.css';

const ThermalCard = ({ title, severity, content = [] }) => {
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    // Thermal wipe animation on mount
    const timer = setTimeout(() => setIsRevealed(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // Determine border color based on severity rules
  const getBorderColor = () => {
    if (severity >= 9) return 'critical';
    if (severity >= 5 && severity <= 8) return 'warn';
    if (severity >= 1 && severity <= 4) return 'safe';
    return 'neutral';
  };

  const isTriage = title.toLowerCase().includes('triage');
  const isInventory = title.toLowerCase().includes('inventory');

  const renderTriageScore = () => {
    if (!isTriage) return null;
    const percentage = Math.min(((severity || 0) / 10) * 100, 100);
    return (
      <div className="triage-progress-ring">
        <svg viewBox="0 0 36 36" className={`ring-svg color-${getBorderColor()}`}>
          <path className="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
          <path className="ring-fill" strokeDasharray={`${percentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
        </svg>
        <div className="ring-text">{severity || 0}/10</div>
      </div>
    );
  };

  return (
    <div className={`thermal-card-container ${isRevealed ? 'revealed' : ''} border-${getBorderColor()}`}>
      <div className={`thermal-card-header color-${getBorderColor()}`}>
        <span>{title}</span>
        {renderTriageScore()}
      </div>
      
      {severity >= 9 && (
        <div className="escalation-banner">
          ⚠️ ESCALATION RECOMMENDED
        </div>
      )}

      <div className={`thermal-card-body ${isInventory ? 'inventory-layout' : ''}`}>
        {content.map((line, idx) => {
          // Handle strikethrough logic specifically requested
          const hasStrikethrough = line.includes('~~');
          const cleanLine = line.replace(/~~/g, '');
          
          if (isInventory) {
            return (
              <div key={idx} className={`inventory-chip ${hasStrikethrough ? 'out-of-stock' : 'in-stock'}`}>
                {cleanLine}
              </div>
            );
          }
          
          return (
            <p key={idx} className={`thermal-card-line ${hasStrikethrough ? 'strikethrough' : ''}`}>
              {cleanLine}
            </p>
          );
        })}
      </div>
    </div>
  );
};

export default ThermalCard;

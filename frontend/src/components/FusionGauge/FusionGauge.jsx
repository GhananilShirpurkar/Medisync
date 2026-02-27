import React from 'react';
import './FusionGauge.css';

const FusionGauge = ({ fusionState }) => {
  if (!fusionState) return null;

  const {
    safety_confidence = 0,
    fulfillment_confidence = 0,
    dominant_mode = 'safety',
    status,
    alert_level = 'nominal',
    halt_reason,
    session_duration_ms
  } = fusionState.details || fusionState; 
  // Allow passing raw details obj or the full event

  // Convert to 0-1 range just in case it's passed as percentage, 
  // but backend sends 0.0 - 1.0 based on orchestrator_models.py
  const clamp = (val) => Math.min(Math.max(val, 0), 1);
  const safetyVal = clamp(safety_confidence);
  const fulfillmentVal = clamp(fulfillment_confidence);

  const dominantValue = dominant_mode === 'safety' ? safetyVal : fulfillmentVal;
  const secondaryValue = dominant_mode === 'safety' ? fulfillmentVal : safetyVal;

  const getColor = (value) => {
    if (value >= 0.70) return 'var(--green)';
    if (value >= 0.40 && value < 0.70) return 'var(--amber)';
    return 'var(--red)';
  };

  const dominantColor = getColor(dominantValue);
  const secondaryColor = alert_level === 'critical' ? 'rgba(204, 51, 0, 0.4)' : 'var(--ink-ghost)';
  
  // Outer arc: radius 60, inner arc: radius 52
  const outerRadius = 60;
  const innerRadius = 52;
  const outerCircumference = 2 * Math.PI * outerRadius;
  const innerCircumference = 2 * Math.PI * innerRadius;
  
  // 270 degrees sweep
  const sweepFraction = 0.75;
  const outerDasharray = `${outerCircumference * sweepFraction} ${outerCircumference}`;
  const innerDasharray = `${innerCircumference * sweepFraction} ${innerCircumference}`;
  
  const outerDashoffset = outerCircumference * sweepFraction * (1 - dominantValue);
  const innerDashoffset = innerCircumference * sweepFraction * (1 - secondaryValue);

  const formatPercentage = (val) => Math.round(val * 100) + '%';
  const displayLabel = status === 'complete' || status === 'completed' ? 'RESOLVED' : dominant_mode.toUpperCase();

  return (
    <div className={`fusion-gauge-container ${alert_level === 'critical' ? 'critical-alert' : ''}`}>
      <div className={`gauge-svg-wrapper ${alert_level === 'critical' ? 'pulse-once' : ''}`}>
        <svg viewBox="0 0 140 140" className="fusion-svg">
          {/* Background tracks */}
          <circle cx="70" cy="70" r={outerRadius} className="gauge-track outer-track" 
            strokeWidth="8" fill="none" transform="rotate(135 70 70)"
            strokeDasharray={outerDasharray} strokeDashoffset="0" />
            
          <circle cx="70" cy="70" r={innerRadius} className="gauge-track inner-track" 
            strokeWidth="3" fill="none" transform="rotate(135 70 70)"
            strokeDasharray={innerDasharray} strokeDashoffset="0" />

          {/* Active arcs */}
          <circle cx="70" cy="70" r={outerRadius} className="gauge-arc outer-arc" 
            stroke={dominantColor} strokeWidth="8" fill="none" transform="rotate(135 70 70)"
            strokeDasharray={outerDasharray} strokeDashoffset={outerDashoffset} />
            
          <circle cx="70" cy="70" r={innerRadius} className="gauge-arc inner-arc" 
            stroke={secondaryColor} strokeWidth="3" fill="none" transform="rotate(135 70 70)"
            strokeDasharray={innerDasharray} strokeDashoffset={innerDashoffset} />
        </svg>
        
        <div className="gauge-center-content">
          <div className="gauge-percentage" style={{ color: 'var(--ink)' }}>{formatPercentage(dominantValue)}</div>
          <div className="gauge-label" style={{ color: (status === 'complete' || status === 'completed') ? 'var(--green)' : 'var(--ink-faint)' }}>{displayLabel}</div>
          {(status === 'complete' || status === 'completed') && session_duration_ms && (
            <div className="gauge-duration">{(session_duration_ms / 1000).toFixed(1)}s</div>
          )}
        </div>
      </div>

      <div className="gauge-metrics">
        <div className="metric-row">
          <span className="metric-name">Safety Conf.</span>
          <span className="metric-val">{formatPercentage(safetyVal)}</span>
          <div className="metric-bar-bg">
            <div className="metric-bar-fill" style={{ width: formatPercentage(safetyVal), backgroundColor: getColor(safetyVal) }}></div>
          </div>
        </div>
        <div className="metric-row">
          <span className="metric-name">Fulfillment Conf.</span>
          <span className="metric-val">{formatPercentage(fulfillmentVal)}</span>
          <div className="metric-bar-bg">
            <div className="metric-bar-fill" style={{ width: formatPercentage(fulfillmentVal), backgroundColor: getColor(fulfillmentVal) }}></div>
          </div>
        </div>
        {status === 'halted' && halt_reason && (
          <div className="halt-reason">{halt_reason}</div>
        )}
      </div>
    </div>
  );
};

export default FusionGauge;

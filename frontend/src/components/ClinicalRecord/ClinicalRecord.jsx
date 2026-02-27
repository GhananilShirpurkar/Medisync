import React from 'react';
import './ClinicalRecord.css';

const ClinicalRecord = ({ entries }) => {
  return (
    <div className="clinical-record-container">
      <div className="clinical-record-header">
        <span>Clinical Record Timeline</span>
      </div>
      
      <div className="clinical-record-log">
        <div className="timeline-rail" />
        {entries.length === 0 && (
          <div className="clinical-record-entry">
            <div className="timeline-node" />
            <div className="timeline-content">
              Session opened {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}...
            </div>
          </div>
        )}
        
        {entries.map((entry, idx) => (
          <div key={idx} className={`clinical-record-entry ${entry.isSubnote ? 'subnote' : 'solidified'}`}>
            <div className="timeline-node" />
            <div className="timeline-content">
              {entry.text}
            </div>
          </div>
        ))}

        {/* Blinking cursor for live mirror simulation */}
        <div className="clinical-record-entry live">
          <div className="timeline-node active" />
          <div className="timeline-content">
            <span className="blinking-cursor">_</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClinicalRecord;

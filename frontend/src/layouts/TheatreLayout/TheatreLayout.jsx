import React from 'react';
import './TheatreLayout.css';

const TheatreLayout = ({ 
  leftZone, 
  rightZone, 
  stageContent,
  isTimelineOpen,
  isOrdersOpen,
  onClosePanels,
  timelinePanelContent,
  ordersPanelContent
}) => {
  return (
    <div className="theatre-layout-container">
      
      {/* Backdrop for sliding panels */}
      <div 
        className={`panel-backdrop ${(isTimelineOpen || isOrdersOpen) ? 'active' : ''}`}
        onClick={onClosePanels}
      />

      {/* COLUMN 1: Left Zone (Metadata + Record + Traces) */}
      <div className="left-zone">
        {leftZone}
      </div>
      
      {/* COLUMN 2: Center Stage (Chat) */}
      <div className="theatre-stage-layer">
        <div className="theatre-stage-panel">
          {stageContent}
        </div>
      </div>
      
      {/* COLUMN 3: Right Zone (Intel Shelf + System Status) */}
      <div className="right-zone">
        {rightZone}
      </div>

      {/* Sliding Panels Overlay */}
      <div className="sliding-panel-overlay">
        {/* Timeline Panel (Slides from left) */}
        <div className={`timeline-sliding-panel ${isTimelineOpen ? 'open' : ''}`}>
           {timelinePanelContent}
        </div>

        {/* Orders Panel (Slides from bottom) */}
        <div className={`orders-sliding-panel ${isOrdersOpen ? 'open' : ''}`}>
           {ordersPanelContent}
        </div>
      </div>

    </div>
  );
};

export default TheatreLayout;

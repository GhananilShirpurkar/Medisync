import React from 'react';
import ThermalCard from '../ThermalCard/ThermalCard';
import './IntelShelf.css';

const IntelShelf = ({ cards }) => {
  return (
    <div className="intel-shelf-container">
      <div className="intel-shelf-header">
        <span>Intel Shelf // Artifact Storage</span>
      </div>

      <div className="intel-shelf-content">
        {/* Triage Slot */}
        <div className="shelf-slot">
          {cards.triage ? (
             <ThermalCard {...cards.triage} />
          ) : (
            <div className="shelf-ghost-outline">
              <span className="ghost-title">TRIAGE</span>
              <span className="ghost-waiting">WAITING</span>
            </div>
          )}
        </div>

        {/* Medical / Identity Slot */}
        <div className="shelf-slot">
          {cards.medical ? (
             <ThermalCard {...cards.medical} />
          ) : (
            <div className="shelf-ghost-outline">
              <span className="ghost-title">MEDICAL</span>
              <span className="ghost-waiting">WAITING</span>
            </div>
          )}
        </div>

        {/* Inventory Slot */}
        <div className="shelf-slot">
          {cards.inventory ? (
             <ThermalCard {...cards.inventory} />
          ) : (
            <div className="shelf-ghost-outline">
              <span className="ghost-title">INVENTORY</span>
              <span className="ghost-waiting">WAITING</span>
            </div>
          )}
        </div>
        
        {/* Fulfillment Slot */}
        <div className="shelf-slot">
          {cards.fulfillment ? (
             <ThermalCard {...cards.fulfillment} />
          ) : (
            null // Fulfillment only appears, doesn't wait visibly.
          )}
        </div>
      </div>
      
      <div className="intel-shelf-footer">
        <span>SHELF-Z-ALPHA</span>
      </div>
    </div>
  );
};

export default IntelShelf;

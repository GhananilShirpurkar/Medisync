import React, { useMemo } from 'react';
import ShelfCard from './ShelfCard';

const IntelShelf = ({ currentOrder }) => {
  // Determine which cards are "ready"
  const triageData = currentOrder?.severity ? {
    SCORE: `${currentOrder.severity.score}/10`,
    RISK: currentOrder.severity.critical ? 'HIGH' : 'STABLE',
    ZONE: 'RED-1'
  } : null;

  const medicalData = currentOrder?.interactionStatus ? {
     INTENT: currentOrder.interactionStatus.toUpperCase(),
     PATH: 'ACUTE-02',
     PROTO: 'SAFE'
  } : null;

  const inventoryData = currentOrder?.medications?.length > 0 ? {
     ITEMS: currentOrder.medications.length,
     AVAIL: 'YES',
     DISP: 'AUTO'
  } : null;

  // Animation Orbit Selection (Highest severity first)
  // Since we only have one trigger in this mock logic, we'll just stagger them in order for now
  // In a real system, we'd sort these keys based on update timestamps or severity scores.

  return (
    <div className="h-full flex flex-col bg-transparent overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 font-mono" style={{ fontFamily: '"B612 Mono", monospace' }}>
          Intel Shelf // Artifact Storage
        </span>
      </div>

      {/* Shelf Contents */}
      <div className="flex-1 overflow-y-auto px-8 py-10 space-y-8">
        <ShelfCard 
          label="Triage" 
          data={triageData} 
          isWaiting={!triageData} 
          delay={0}
        />
        
        <ShelfCard 
          label="Medical" 
          data={medicalData} 
          isWaiting={!medicalData} 
          delay={0.3}
        />

        <ShelfCard 
          label="Inventory" 
          data={inventoryData} 
          isWaiting={!inventoryData} 
          delay={0.6}
        />
      </div>

      {/* Footer Info */}
      <div className="p-6 text-[10px] text-slate-600 font-mono opacity-50 border-t border-white/5">
        SHELF-Z-ALPHA
      </div>
    </div>
  );
};

export default IntelShelf;

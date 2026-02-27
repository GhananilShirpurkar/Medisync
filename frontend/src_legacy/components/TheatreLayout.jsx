import React from 'react';

const TheatreLayout = ({ children, leftZone, rightZone }) => {
  return (
    <div className="relative z-10 flex h-full w-full overflow-hidden bg-transparent">
      {/* BACKGROUND LAYER: Z-index 0 */}
      <div className="absolute inset-0 flex pointer-events-auto z-0">
        {/* Left Background Zone (Process & Record) */}
        <div className="flex-1 h-full border-r border-white/5 bg-black/20 pointer-events-auto">
          {leftZone}
        </div>
        
        {/* Center Gap (for Stage visibility) */}
        <div className="w-[560px] h-full" />
        
        {/* Right Background Zone (Artifacts) */}
        <div className="flex-1 h-full border-l border-white/5 bg-black/20 pointer-events-auto">
          {rightZone}
        </div>
      </div>

      {/* STAGE LAYER: Z-index 20 */}
      <div className="absolute inset-0 z-20 flex pointer-events-none items-stretch">
        {/* Left Spacer */}
        <div className="flex-1 h-full" />
        
        {/* Stage Area - The Focal Point */}
        <div className="w-[560px] h-full flex flex-col items-stretch pointer-events-auto bg-[#F8F9F7] relative shadow-[0_0_100px_rgba(0,0,0,0.5)] border-x border-black/5">
          {children}
        </div>

        {/* Right Spacer */}
        <div className="flex-1 h-full" />
      </div>
    </div>
  );
};

export default TheatreLayout;

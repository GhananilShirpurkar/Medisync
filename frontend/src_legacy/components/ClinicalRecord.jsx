import React from 'react';

const ClinicalRecord = ({ entries = [] }) => {
  return (
    <div className="h-full flex flex-col bg-transparent font-serif overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 font-mono" style={{ fontFamily: '"B612 Mono", monospace' }}>
          Clinical Record // Live Mirror
        </span>
        <span className="text-[10px] text-slate-500 font-mono" style={{ fontFamily: '"B612 Mono", monospace' }}>
          [REDACTED-PHI]
        </span>
      </div>

      {/* Ruled Notebook Content */}
      <div className="flex-1 overflow-y-auto px-8 py-6 relative">
        {/* Ruled Notebook Content Lines */}
        <div className="absolute inset-0 pointer-events-none opacity-10 px-8">
           <div className="h-full w-full bg-[repeating-linear-gradient(transparent,transparent_31px,rgba(255,255,255,0.05)_31px,rgba(255,255,255,0.05)_32px)]" />
        </div>

        <div className="relative z-10 space-y-8">
          {entries.length === 0 ? (
             <div className="text-[13px] text-slate-600 italic py-2">
               Session opened {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}...
             </div>
          ) : (
            entries.map((entry, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center gap-2">
                   <div className="w-1 h-1 bg-slate-600 rounded-full" />
                   <span className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider">
                     {entry.timestamp}
                   </span>
                </div>
                <p className="text-[15px] leading-[32px] text-slate-400 pl-3 italic">
                  {entry.text}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ClinicalRecord;

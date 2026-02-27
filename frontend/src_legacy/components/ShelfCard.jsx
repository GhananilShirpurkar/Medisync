import React from 'react';
import { motion } from 'framer-motion';

const ShelfCard = ({ label, data, delay = 0, isWaiting = true }) => {
  return (
    <div className="relative w-full aspect-[3/4] rounded-xl overflow-hidden group">
      {/* Background Frame */}
      <div className={`
        absolute inset-0 border border-dashed transition-all duration-700
        ${isWaiting ? 'border-white/10 bg-transparent' : 'border-white/20 bg-white/5 backdrop-blur-md shadow-sm'}
      `} />

      {/* Label (Always visible) */}
      <div className="absolute top-4 left-4 z-20">
        <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-500 font-mono" style={{ fontFamily: '"B612 Mono", monospace' }}>
          {label}
        </span>
      </div>

      {/* Content Layer (Thermal Reveal) */}
      {!isWaiting && (
        <motion.div 
          initial={{ clipPath: 'inset(100% 0 0 0)', opacity: 0 }}
          animate={{ clipPath: 'inset(0% 0 0 0)', opacity: 1 }}
          transition={{ 
            duration: 0.8, 
            delay: delay,
            ease: "easeInOut"
          }}
          className="absolute inset-0 p-4 pt-10 flex flex-col justify-between"
        >
          {/* Thermal Reveal Glow / Burn Effect */}
          <motion.div 
            initial={{ top: '100%' }}
            animate={{ top: '-10%' }}
            transition={{ duration: 0.8, delay: delay, ease: "easeInOut" }}
            className="absolute left-0 right-0 h-4 bg-white/10 blur-md z-10 pointer-events-none"
          />

          <div className="space-y-3 relative z-0">
            {data ? (
              typeof data === 'string' ? (
                <p className="text-[13px] text-slate-300 font-serif italic leading-relaxed" style={{ fontFamily: '"Cormorant Garamond", serif' }}>
                   {data}
                </p>
              ) : (
                <div className="space-y-2">
                   {Object.entries(data).map(([key, val], i) => (
                      <div key={i} className="flex justify-between items-end border-b border-white/5 pb-1">
                         <span className="text-[10px] text-slate-500 font-mono uppercase">{key}</span>
                         <span className="text-[11px] text-slate-300 font-bold">{val}</span>
                      </div>
                   ))}
                </div>
              )
            ) : (
              <p className="text-[11px] text-slate-600 italic">No data captured.</p>
            )}
          </div>

          <div className="flex justify-between items-center text-[9px] text-slate-600 font-mono">
             <span>REF-892</span>
             <span>VERIFIED</span>
          </div>
        </motion.div>
      )}

      {/* Waiting Indicator */}
      {isWaiting && (
        <div className="absolute inset-0 flex items-center justify-center">
           <span className="text-[9px] font-bold text-slate-700 tracking-[0.3em] font-mono animate-pulse">
             WAITING
           </span>
        </div>
      )}
    </div>
  );
};

export default ShelfCard;

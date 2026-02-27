import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTraceStream } from '../hooks/useTraceStream';

const IntelligenceTrace = ({ sessionId }) => {
  const { events } = useTraceStream(sessionId);

  return (
    <div className="h-full flex flex-col bg-transparent overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 font-mono" style={{ fontFamily: '"B612 Mono", monospace' }}>
          Intelligence Trace // Agent Timeline
        </span>
      </div>

      {/* Timeline Rail */}
      <div className="flex-1 overflow-y-auto px-8 py-10 relative">
        {/* Vertical Rail Line */}
        <div className="absolute left-[39px] top-0 bottom-0 w-[1px] bg-white/10" />

        <div className="space-y-10 relative z-10">
          <AnimatePresence initial={false}>
            {events.map((event, idx) => {
              const isCritical = event.details?.severity >= 9 || event.details?.interaction === 'critical';
              
              return (
                <motion.div 
                  key={event.id || idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-start gap-6 group"
                >
                  {/* Timeline Node */}
                  <div className="relative mt-1">
                    <div className={`
                      transition-all duration-500 rounded-full
                      ${isCritical ? 'w-2 h-2 bg-[#DC2626] -ml-[0.5px]' : 'w-1.5 h-1.5 bg-slate-600'}
                    `} />
                    {event.status === 'running' && (
                      <motion.div 
                        animate={{ scale: [1, 2, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="absolute inset-0 bg-blue-400/30 rounded-full"
                      />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-widest">
                        {event.agent}
                      </span>
                      <span className="text-[9px] text-slate-600 font-mono">
                        {new Date(event.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                    <p className={`
                      text-[12px] leading-relaxed transition-colors duration-500
                      ${isCritical ? 'text-red-500 font-medium' : 'text-slate-400 group-hover:text-slate-200'}
                    `}>
                      {event.step}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {/* Terminal COMPLETE Node */}
          {events.length > 0 && !events.some(e => e.status === 'started' || e.status === 'running') && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-6 pt-4"
            >
              <div className="w-4 h-4 rounded-full border border-emerald-500/50 flex items-center justify-center -ml-[5.5px] bg-emerald-950/20">
                <span className="text-[8px] text-emerald-500 font-bold">✓</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-500/70 font-mono uppercase tracking-[0.2em]">
                Complete
              </span>
            </motion.div>
          )}

          {/* Empty State / Ready Hook */}
          {events.length === 0 && (
            <div className="flex items-start gap-6 opacity-30">
               <div className="w-1.5 h-1.5 bg-slate-700 rounded-full mt-1" />
               <div className="space-y-1">
                 <span className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-widest">System</span>
                 <p className="text-[12px] text-slate-600 italic">Listener active...</p>
               </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceTrace;

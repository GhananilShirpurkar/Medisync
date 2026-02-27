import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTraceStream } from '../hooks/useTraceStream';

const StatusAmbience = ({ sessionId, severity = 0 }) => {
  const { events } = useTraceStream(sessionId);
  
  const activeEvent = events.find(e => e.status === 'started' || e.status === 'running');

  // Severity Logic: 
  // 0-6: Base (Zen Neutral)
  // 7-8: Warn (Amber)
  // 9-10: Critical (Red)
  const ambientStyle = useMemo(() => {
    if (severity >= 9) return 'bg-[#FEF2F2]'; // Very light red
    if (severity >= 7) return 'bg-[#FFFBEB]'; // Very light amber
    return 'bg-[#E8EAE6]'; // Base Sage Grey
  }, [severity]);
  
  return (
    <>
      {/* FULL SCREEN AMBIENT OVERLAY */}
      <motion.div 
        initial={false}
        animate={{ backgroundColor: severity >= 9 ? '#450a0a' : severity >= 7 ? '#422006' : '#0a0a0a' }}
        className="fixed inset-0 z-0 transition-colors duration-1000 ease-in-out opacity-100"
      />

      {/* QUIET AMBIENCE INDICATOR (Bottom Right) */}
      <div className="fixed bottom-6 right-8 z-[60] pointer-events-none">
        <AnimatePresence mode="wait">
          {activeEvent && (
            <motion.div
              key={activeEvent.agent}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-3"
            >
              <div className="flex gap-1">
                <motion.div 
                  animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0.6, 0.3] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-1.5 h-1.5 bg-[#6b8e23] rounded-full"
                />
              </div>
              <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">
                {activeEvent.agent} is reviewing
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
};

export default StatusAmbience;

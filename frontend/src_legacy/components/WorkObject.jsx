import React from 'react';
import { motion } from 'framer-motion';

const WorkObject = ({ objectData, isProximal }) => {
  const { type, payload, annotations, status } = objectData;

  const isProcessing = status === 'processing';

  // Base card styles: Glassmorphism refined
  const cardBaseStyle = `
    relative w-full bg-white/70 backdrop-blur-xl rounded-[24px] 
    border border-white/40 shadow-[0_8px_32px_0_rgba(31,38,135,0.03)]
    p-6 transition-all duration-700 ease-in-out
    ${isProximal ? 'backdrop-blur-[40px] bg-white/50' : ''}
  `;

  const renderFootnotes = () => {
    if (!annotations || annotations.length === 0) return null;

    return (
      <div className="mt-6 pt-5 border-t border-gray-100/50 space-y-3">
        {annotations.map((ann, idx) => (
          <div key={idx} className="flex items-start gap-3">
            <div className="flex flex-col">
              <span className={`text-[9px] font-bold uppercase tracking-[0.15em] mb-1 font-mono ${
                ann.agent === 'Triage' ? 'text-amber-600/70' :
                ann.agent === 'Medical' ? 'text-slate-500/70' :
                ann.agent === 'Inventory' ? 'text-emerald-600/70' :
                'text-gray-400'
              }`} style={{ fontFamily: '"B612 Mono", monospace' }}>
                {ann.agent} // Footnote
              </span>
              <p className="text-[13px] leading-relaxed text-slate-600 font-normal">
                {ann.text}
              </p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <motion.div 
      initial={false}
      animate={isProcessing ? {
        scale: [1, 1.02, 1],
        boxShadow: [
          '0 8px 32px 0 rgba(31,38,135,0.03)',
          '0 12px 48px 0 rgba(31,38,135,0.06)',
          '0 8px 32px 0 rgba(31,38,135,0.03)'
        ]
      } : {
        scale: 1,
        y: status === 'resolved' ? 2 : 0,
        boxShadow: '0 4px 20px 0 rgba(31,38,135,0.02)'
      }}
      transition={isProcessing ? {
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut"
      } : {
        duration: 0.5
      }}
      className={cardBaseStyle}
    >
      {/* State Indicator: Subtle Dot */}
      <div className="absolute top-6 right-6">
        <div className={`w-1.5 h-1.5 rounded-full ${
          isProcessing ? 'bg-blue-400/50 animate-pulse' : 'bg-slate-200'
        }`} />
      </div>

      {type === 'transcript' ? (
        <div className="space-y-4">
          <p className="text-[17px] text-slate-800 font-medium leading-[1.6] tracking-tight" style={{ fontFamily: '"Plus Jakarta Sans", sans-serif' }}>
            "{payload.text}"
          </p>
          
          {payload.response && (
            <div className="mt-2 text-[18px] text-slate-500 leading-relaxed italic border-l-2 border-slate-100 pl-4 py-1 whitespace-pre-wrap flex flex-col gap-2" style={{ fontFamily: '"Cormorant Garamond", serif' }}>
              {payload.response}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="aspect-[4/3] w-full bg-slate-50 rounded-2xl overflow-hidden border border-slate-100 group relative">
            {payload.imageUrl ? (
              <img src={payload.imageUrl} alt="Document" className="w-full h-full object-cover opacity-90 transition-opacity duration-700 group-hover:opacity-100" />
            ) : (
               <div className="w-full h-full flex items-center justify-center text-4xl opacity-20">📄</div>
            )}
            
            {isProcessing && (
              <div className="absolute inset-0 bg-white/40 backdrop-blur-[2px] flex items-center justify-center">
                <div className="text-[11px] font-bold tracking-widest text-slate-400 uppercase">Scanning...</div>
              </div>
            )}
          </div>
        </div>
      )}

      {renderFootnotes()}
      
      {/* Resolved Subtle Underline for Triage (Amber) */}
      {status === 'resolved' && annotations?.some(a => a.agent === 'Triage') && (
        <div className="absolute bottom-0 left-6 right-6 h-[2px] bg-amber-400/20 rounded-full" />
      )}
    </motion.div>
  );
};

export default WorkObject;

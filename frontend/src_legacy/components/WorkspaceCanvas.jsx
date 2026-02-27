import React, { useRef, useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import WorkObject from './WorkObject';

const GrainOverlay = () => (
  <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-0" 
       style={{ 
         backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
         mixBlendMode: 'multiply'
       }}>
  </div>
);

const WorkspaceCanvas = ({ objects = [] }) => {
  const containerRef = useRef(null);
  const [positions, setPositions] = useState({});

  useEffect(() => {
    let changed = false;
    const next = { ...positions };
    
    objects.forEach((obj) => {
      if (!next[obj.id]) {
        next[obj.id] = {
          x: 280 - 200 + (Math.random() * 40 - 20), // 560/2 - 200
          y: window.innerHeight / 2 - 200 + (Math.random() * 40 - 20)
        };
        changed = true;
      }
    });

    if (changed) {
      setTimeout(() => setPositions(next), 0);
    }
  }, [objects, positions]);

  const proximities = useMemo(() => {
    const threshold = 450;
    const items = [];
    const ids = Object.keys(positions);

    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const idA = ids[i];
        const idB = ids[j];
        const posA = positions[idA];
        const posB = positions[idB];

        const dist = Math.sqrt(
          Math.pow(posA.x - posB.x, 2) + Math.pow(posA.y - posB.y, 2)
        );

        if (dist < threshold) {
          items.push({
            id: `${idA}-${idB}`,
            midX: (posA.x + posB.x) / 2 + 200,
            midY: (posA.y + posB.y) / 2 + 200,
            status: 'Related' 
          });
        }
      }
    }
    return items;
  }, [positions]);

  const handleDragEnd = (id, info) => {
    setPositions(prev => ({
      ...prev,
      [id]: {
        x: (prev[id]?.x || 0) + info.offset.x,
        y: (prev[id]?.y || 0) + info.offset.y
      }
    }));
  };

  return (
    <div className="flex-1 w-full h-full relative overflow-hidden bg-transparent cursor-crosshair" ref={containerRef}>
      <GrainOverlay />
      
      <AnimatePresence>
        {proximities.map((prox) => (
          <motion.div
            key={prox.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1, x: prox.midX, y: prox.midY }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute z-10 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
          >
            <div className="bg-white/80 border border-slate-100 px-3 py-1 rounded-full shadow-sm">
              <span className="text-[10px] font-bold tracking-tighter text-slate-400 uppercase">
                {prox.status}
              </span>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      <AnimatePresence>
        {objects.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex flex-col items-center justify-center text-center px-4"
          >
            <span className="text-4xl mb-4 grayscale opacity-100">⚕️</span>
            <h1 className="text-2xl font-light text-slate-950 tracking-tight">Your Workspace is empty.</h1>
            <p className="text-sm font-medium text-slate-600 mt-2 max-w-xs">Record symptoms, upload medical papers, or type to begin your consultation.</p>
          </motion.div>
        ) : (
          objects.map((obj) => (
            <motion.div
              key={obj.id}
              id={obj.id}
              drag
              dragMomentum={false}
              onDragEnd={(e, info) => handleDragEnd(obj.id, info)}
              initial={{ scale: 0.8, opacity: 0, x: 80, y: window.innerHeight / 2 - 200 }}
              animate={{ 
                scale: 1, 
                opacity: 1,
                x: positions[obj.id]?.x !== undefined ? positions[obj.id].x : 80,
                y: positions[obj.id]?.y !== undefined ? positions[obj.id].y : window.innerHeight / 2 - 200
              }}
              className="absolute z-20 cursor-grab active:cursor-grabbing w-[400px]"
            >
              <WorkObject 
                objectData={obj} 
                isProximal={proximities.some(p => p.id.includes(obj.id))} 
              />
            </motion.div>
          ))
        )}
      </AnimatePresence>

      <div className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none opacity-20 flex flex-col items-center gap-2">
        <div className="w-1 h-32 bg-gray-400 rounded-full" />
        <span className="text-[10px] uppercase tracking-widest font-bold">Past Consults</span>
      </div>
      <div className="absolute right-8 top-1/2 -translate-y-1/2 pointer-events-none opacity-20 flex flex-col items-center gap-2">
        <span className="text-[10px] uppercase tracking-widest font-bold">Fulfillment</span>
        <div className="w-1 h-32 bg-gray-400 rounded-full" />
      </div>
    </div>
  );
};

export default WorkspaceCanvas;

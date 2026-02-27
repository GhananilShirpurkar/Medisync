import { useState, useRef } from 'react';
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';

const OmniInputBar = ({ onInputSubmit, onImageSubmit, sessionId, isLoading, isSettled }) => {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLevel, setVoiceLevel] = useState(0);
  const [isFocused, setIsFocused] = useState(false);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);
  
  // MediaRecorder Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Gesture Controls
  const dragY = useMotionValue(0);
  const barY = useTransform(dragY, [-100, 0], [-20, 0]);
  const barOpacity = useTransform(dragY, [-100, -50, 0], [0, 0.5, 1]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onInputSubmit(inputText);
    setInputText('');
  };

  const startVoice = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      analyserRef.current = analyser;
      audioContextRef.current = audioContext;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateLevel = () => {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        setVoiceLevel(average);
        animationFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        sendVoice(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Voice init failed", err);
    }
  };

  const stopVoice = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setVoiceLevel(0);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close();
    }
  };

  const sendVoice = async (blob) => {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');
    try {
      const response = await fetch(`http://localhost:8000/api/conversation/voice?session_id=${sessionId}`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      onInputSubmit(data.transcription, data);
    } catch (err) {
      console.error("Voice process failed", err);
    }
  };

  const handleDragEnd = (_, info) => {
    if (info.offset.y < -60) {
      fileInputRef.current?.click();
    }
  };

  const displayPlaceholder = isSettled && !isFocused && !inputText 
    ? "New consultation..." 
    : isRecording ? "Listening..." : "Describe symptoms or drag up for camera...";

  return (
    <div className={`absolute bottom-12 left-0 right-0 z-50 px-6 transition-opacity duration-1000 ${isSettled && !isFocused ? 'opacity-50' : 'opacity-100'}`}>
      <motion.div 
        style={{ y: barY, opacity: barOpacity }}
        drag="y"
        dragConstraints={{ top: -100, bottom: 0 }}
        dragElastic={0.2}
        onDragEnd={handleDragEnd}
        className="relative group w-full min-w-[320px] md:min-w-[500px] shadow-2xl"
      >
        <AnimatePresence>
          {isRecording && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 60 + (voiceLevel * 0.5), opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="absolute -top-16 left-0 right-0 flex items-end justify-center gap-1 px-8 pointer-events-none"
            >
              {[...Array(24)].map((_, i) => (
                <motion.div 
                  key={i}
                  animate={{ scaleY: Math.max(0.1, voiceLevel * (0.05 + 0.01 * Math.sin(i))) }}
                  className="w-1 h-20 bg-[#6b8e23]/40 rounded-full origin-bottom"
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="bg-white/80 backdrop-blur-2xl p-1.5 rounded-[32px] border border-white/40 shadow-[0_20px_50px_rgba(0,0,0,0.1)] flex items-center gap-2">
          <input 
            type="file" accept="image/*" ref={fileInputRef} className="hidden" 
            onChange={(e) => e.target.files[0] && onImageSubmit(e.target.files[0])} 
          />
          <form onSubmit={handleSubmit} className="flex-1 flex items-center relative">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={displayPlaceholder}
              className="flex-1 bg-transparent px-6 py-4 focus:outline-none text-slate-800 placeholder-slate-400 font-medium selection:bg-[#6b8e23]/20"
              disabled={isLoading || isRecording}
            />
            <div className="flex items-center gap-1.5 pr-2">
              <motion.button
                type="button"
                onPointerDown={(e) => { e.preventDefault(); startVoice(); }}
                onPointerUp={stopVoice}
                onContextMenu={(e) => e.preventDefault()}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                  isRecording ? 'bg-red-500 text-white' : 'bg-slate-50 text-slate-400 hover:text-[#6b8e23]'
                }`}
              >
                {isRecording ? (
                  <div className="w-3 h-3 bg-white rounded-sm animate-pulse" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                  </svg>
                )}
              </motion.button>
              {inputText.trim() && (
                <motion.button
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  type="submit"
                  className="w-12 h-12 bg-[#6b8e23] text-white rounded-full flex items-center justify-center shadow-lg shadow-[#6b8e23]/20"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </motion.button>
              )}
            </div>
          </form>
        </div>
        <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-8 h-1 bg-slate-200/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.div>
    </div>
  );
};

export default OmniInputBar;

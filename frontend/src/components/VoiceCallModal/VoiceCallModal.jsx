import React, { useState, useRef, useEffect, useCallback } from 'react';
import { pipelineStore } from '../../state/pipelineStore';
import mlog from '../../services/debugLogger';
import './VoiceCallModal.css';

// ── Tuning constants ────────────────────────────────────────────
const SILENCE_THRESHOLD = 1800;   // ms — after speech stops, how long to wait
const RINGING_DURATION = 1200;    // ms — quick connect
const MAX_RECORD_MS = 12000;      // max recording per turn (safety net)
const CALIBRATION_MS = 500;       // ms to calibrate ambient noise
const VOICE_MARGIN = 15;          // amplitude above ambient to count as speech
const BARGE_IN_THRESHOLD = 35;    // amplitude — raised to avoid TTS-to-mic feedback
const BARGE_IN_CONFIRM_MS = 600;  // ms of sustained voice to confirm real interruption
const BARGE_IN_DELAY_MS = 1200;   // ms to wait after TTS starts before monitoring (anti-feedback)
const TTS_RATE = 1.15;            // slightly faster TTS for conversational feel

const VoiceCallModal = () => {
  const [callPhase, setCallPhase] = useState('ringing');
  const [elapsed, setElapsed] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [turnCount, setTurnCount] = useState(0);

  const mountedRef = useRef(true);
  const callPhaseRef = useRef('ringing'); // mirror of callPhase for use in callbacks
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const elapsedTimerRef = useRef(null);
  const callStartRef = useRef(null);
  const bargeInStartRef = useRef(null);
  const ambientNoiseRef = useRef(10);    // calibrated ambient noise level

  // Imperatively sync callPhaseRef whenever we change phase
  const setPhase = useCallback((phase) => {
    callPhaseRef.current = phase;
    setCallPhase(phase);
  }, []);

  // ── CORE AUDIO: Persistent mic stream ─────────────────────────
  // Keep one mic stream alive for the entire call to avoid repeated getUserMedia delays
  const ensureMicStream = useCallback(async () => {
    if (streamRef.current) return streamRef.current;

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 16000,       // Whisper's native rate
        channelCount: 1          // Mono
      }
    });
    if (!mountedRef.current) {
      stream.getTracks().forEach(t => t.stop());
      return null;
    }
    streamRef.current = stream;

    // Set up analyser once
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);
    audioCtxRef.current = ctx;
    analyserRef.current = analyser;

    return stream;
  }, []);

  // ── Read current mic amplitude ────────────────────────────────
  const getMicAmplitude = useCallback(() => {
    if (!analyserRef.current) return 0;
    const data = new Uint8Array(analyserRef.current.fftSize);
    analyserRef.current.getByteTimeDomainData(data);
    let max = 0;
    for (let i = 0; i < data.length; i++) {
      const v = Math.abs(data[i] - 128);
      if (v > max) max = v;
    }
    return max;
  }, []);

  // ── CLEANUP ───────────────────────────────────────────────────
  const stopMonitor = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
  }, []);

  const stopRecording = useCallback(() => {
    stopMonitor();
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, [stopMonitor]);

  const killStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    analyserRef.current = null;
  }, []);

  const cancelSpeech = useCallback(() => {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }, []);

  const endCall = useCallback(() => {
    mlog.info('VoiceCall', 'Call ended');
    cancelSpeech();
    stopRecording();
    stopMonitor();
    killStream();
    if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    setPhase('ended');
    setTimeout(() => pipelineStore.dispatch('CLOSE_VOICE_CALL', {}), 600);
  }, [cancelSpeech, stopRecording, stopMonitor, killStream]);

  // ── Forward ref for startListening (used in callbacks) ────────
  const startListeningRef = useRef(null);

  // ── SPEAK + BARGE-IN MONITOR ──────────────────────────────────
  const speakAndContinue = useCallback((text) => {
    if (!mountedRef.current) return;
    setPhase('speaking');
    setAiResponse(text);
    mlog.info('VoiceCall', `Speaking: ${text.slice(0, 60)}...`);

    const doAfterSpeech = () => {
      if (mountedRef.current && callPhaseRef.current !== 'ended') {
        startListeningRef.current?.();
      }
    };

    if (!('speechSynthesis' in window)) {
      setTimeout(doAfterSpeech, 1500);
      return;
    }

    cancelSpeech();

    const clean = text
      .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
      .replace(/[#*`_~]/g, '')
      .replace(/\n+/g, '. ')
      .trim();

    if (!clean) { doAfterSpeech(); return; }

    const utterance = new SpeechSynthesisUtterance(clean);
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.lang.includes('en-GB') || v.name.includes('Google UK English Female'))
                   || voices.find(v => v.lang.startsWith('en'))
                   || voices[0];
    if (preferred) utterance.voice = preferred;

    utterance.rate = TTS_RATE;
    utterance.pitch = 1.0;

    let interrupted = false;

    utterance.onend = () => {
      if (!interrupted) {
        mlog.info('VoiceCall', 'TTS finished naturally');
        doAfterSpeech();
      }
    };
    utterance.onerror = (e) => {
      if (e.error !== 'interrupted') mlog.error('VoiceCall TTS', e);
      if (!interrupted) doAfterSpeech();
    };

    window.speechSynthesis.speak(utterance);

    // ── BARGE-IN: Monitor mic while AI speaks ───────────────────
    // Wait for TTS audio to settle in the mic before monitoring
    bargeInStartRef.current = null;

    const checkBargeIn = () => {
      if (!mountedRef.current || callPhaseRef.current !== 'speaking') return;

      const amp = getMicAmplitude();

      if (amp > BARGE_IN_THRESHOLD) {
        if (!bargeInStartRef.current) {
          bargeInStartRef.current = Date.now();
        } else if (Date.now() - bargeInStartRef.current > BARGE_IN_CONFIRM_MS) {
          // Confirmed real barge-in!
          mlog.info('VoiceCall', `BARGE-IN detected (amp=${amp}), interrupting AI`);
          interrupted = true;
          cancelSpeech();
          bargeInStartRef.current = null;
          startListeningRef.current?.();
          return;
        }
      } else {
        // Reset if amplitude drops — must be sustained voice
        bargeInStartRef.current = null;
      }

      animFrameRef.current = requestAnimationFrame(checkBargeIn);
    };

    // Long delay before monitoring to let TTS audio bleed settle in the mic
    setTimeout(() => {
      if (mountedRef.current && callPhaseRef.current === 'speaking') {
        checkBargeIn();
      }
    }, BARGE_IN_DELAY_MS);

  }, [cancelSpeech, getMicAmplitude]);

  // ── SEND TO BACKEND ───────────────────────────────────────────
  const processVoiceTurn = useCallback(async (audioBlob) => {
    if (!mountedRef.current) return;
    setPhase('processing');
    setTranscript('...');
    mlog.info('VoiceCall', `Processing blob: ${audioBlob.size}b`);

    const storeState = pipelineStore.get();
    const sessionId = storeState.sessionId;

    if (!sessionId) {
      mlog.error('VoiceCall', 'No session');
      endCall();
      return;
    }

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'call_recording.webm');

      const BASE_URL = window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : window.location.origin;
      const url = new URL(`${BASE_URL}/api/conversation/voice`);
      url.searchParams.append('session_id', sessionId);

      const res = await fetch(url, { method: 'POST', body: formData });
      
      // FIX BUG 5: Properly handle HTTP errors
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }
      
      const data = await res.json();

      if (!mountedRef.current) return;

      // FIX BUG 5: Validate transcription data gracefully
      if (!data.transcription || data.transcription.trim() === '') {
        setPhase('listening');
        speakAndContinue("I didn't catch that. Please try again.");
        return;
      }

      setTranscript(data.transcription || '...');
      setTurnCount(c => c + 1);

      // Update chat
      pipelineStore.dispatch('USER_MESSAGE_SENT', data.transcription);
      pipelineStore.dispatch('RECORD_APPEND', { text: `🎤 "${data.transcription}"`, type: 'voice' });
      
      // FIX BUG 5: Log successful transcription with actual confidence
      pipelineStore.dispatch('TRACE_APPEND', {
        agent: 'Whisper Agent',
        step: 'transcription_completed',
        type: 'tool_use',
        status: 'completed',
        details: { 
          transcription: data.transcription,
          confidence: data.transcription_confidence || 0,
          language: data.language || 'en'
        },
        timestamp: new Date().toISOString()
      });

      if (data.intent) {
        pipelineStore.dispatch('intent_classified', {
          intent: data.intent,
          entities: data.patient_context ? Object.keys(data.patient_context) : [],
          patientContext: data.patient_context || null
        });
      }

      if (data.recommendations?.length > 0) {
        const meds = data.recommendations.map(r => `${r.medicine_name} - ${r.stock > 0 ? 'In Stock' : 'Out of Stock'}`);
        pipelineStore.dispatch('SHELF_CARD_READY', {
          type: 'inventory',
          card: { title: 'INVENTORY RECOMMENDATIONS', severity: 0, content: meds }
        });
      }

      pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
        text: data.message,
        footnotes: [{ agent: 'Whisper', text: `Confidence: ${((data.transcription_confidence || 0) * 100).toFixed(0)}%` }],
        severityAssessment: data.severity_assessment
      });

      if (!data.needs_clarification && data.recommendations?.length > 0) {
        let totalPrice = 0;
        const items = data.recommendations.map(r => {
          totalPrice += r.price;
          return { name: r.medicine_name, stockStatus: r.stock > 0 ? 'In Stock' : 'Out of Stock', price: r.price, warnings: [], substitute: null };
        });
        pipelineStore.dispatch('CHECKOUT_READY', {
          orderSummary: { pid: storeState.pid, complaint: data.transcription, validation: { status: 'Approved', severity: 0 }, items, substitutions: [], totalPrice, orderId: `ORD-${Math.floor(Math.random() * 9999)}` }
        });
      }

      speakAndContinue(data.message);

    } catch (err) {
      mlog.error('VoiceCall processVoiceTurn', err);
      
      // FIX BUG 5: Log as error, not completed
      pipelineStore.dispatch('TRACE_APPEND', {
        agent: 'Whisper Agent',
        step: 'transcription_failed',
        type: 'error',
        status: 'failed',
        details: { error: err.message },
        timestamp: new Date().toISOString()
      });
      
      if (mountedRef.current) {
        // FIX BUG 5: Set empty transcription with confidence 0
        setTranscript('');
        setAiResponse('Sorry, I couldn\'t understand that. Please try speaking again.');
        
        // Speak error message and retry
        setTimeout(() => {
          if (mountedRef.current && callPhaseRef.current !== 'ended') {
            speakAndContinue('Sorry, I couldn\'t understand that. Please try speaking again.');
          }
        }, 500);
      }
    }
  }, [endCall, speakAndContinue]);

  // ── SILENCE MONITOR (with ambient calibration) ────────────────
  const monitorSilence = useCallback(() => {
    if (!analyserRef.current || !mountedRef.current) return;

    const startTime = Date.now();
    let calibrationSamples = [];
    let calibrated = false;
    let speechDetected = false;
    let lastSpeechTime = Date.now();

    const check = () => {
      if (!mountedRef.current || callPhaseRef.current !== 'active') return;

      const amp = getMicAmplitude();
      const now = Date.now();

      // Max recording safety net
      if (now - startTime > MAX_RECORD_MS) {
        mlog.info('VoiceCall', `Max recording time (${MAX_RECORD_MS}ms), stopping`);
        stopRecording();
        return;
      }

      // Phase 1: Calibrate ambient noise (first CALIBRATION_MS)
      if (!calibrated) {
        calibrationSamples.push(amp);
        if (now - startTime >= CALIBRATION_MS) {
          const avg = calibrationSamples.reduce((a, b) => a + b, 0) / calibrationSamples.length;
          ambientNoiseRef.current = Math.max(avg, 5); // minimum floor of 5
          calibrated = true;
          mlog.info('VoiceCall', `Ambient calibrated: ${ambientNoiseRef.current.toFixed(1)}, speech threshold: ${(ambientNoiseRef.current + VOICE_MARGIN).toFixed(1)}`);
        }
        animFrameRef.current = requestAnimationFrame(check);
        return;
      }

      // Phase 2: Detect speech vs silence using calibrated threshold
      const speechThreshold = ambientNoiseRef.current + VOICE_MARGIN;

      if (amp > speechThreshold) {
        speechDetected = true;
        lastSpeechTime = now;
      }

      // Only trigger silence AFTER we've heard speech at least once
      if (speechDetected && (now - lastSpeechTime > SILENCE_THRESHOLD)) {
        mlog.info('VoiceCall', `Silence detected (${SILENCE_THRESHOLD}ms after speech), stopping`);
        stopRecording();
        return;
      }

      animFrameRef.current = requestAnimationFrame(check);
    };

    check();
  }, [getMicAmplitude, stopRecording]);

  // ── START LISTENING ───────────────────────────────────────────
  const startListening = useCallback(async () => {
    if (!mountedRef.current || isMuted) return;
    setPhase('active');
    setTranscript('');
    mlog.info('VoiceCall', 'Listening...');

    try {
      const stream = await ensureMicStream();
      if (!stream || !mountedRef.current) return;

      // Prefer opus for speech (better quality at low bitrate)
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus' : undefined;
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      audioChunksRef.current = [];
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        mlog.info('VoiceCall', `Recorded ${blob.size}b`);
        // Skip tiny recordings (< 5KB = likely just noise/silence, causes hallucination)
        if (blob.size < 5000) {
          mlog.info('VoiceCall', `Skipping tiny recording (${blob.size}b < 5KB)`);
          if (mountedRef.current) startListeningRef.current?.();
          return;
        }
        if (mountedRef.current) {
          processVoiceTurn(blob);
        }
      };

      recorder.start();
      monitorSilence();

    } catch (err) {
      mlog.error('VoiceCall startListening', err);
      endCall();
    }
  }, [isMuted, ensureMicStream, processVoiceTurn, monitorSilence, endCall]);

  // Keep ref in sync
  useEffect(() => { startListeningRef.current = startListening; }, [startListening]);

  // ── MOUNT ─────────────────────────────────────────────────────
  useEffect(() => {
    mountedRef.current = true;
    callStartRef.current = Date.now();

    pipelineStore.dispatch('TRACE_APPEND', {
      agent: 'Voice Agent', step: 'voice_call_started', type: 'event', status: 'started',
      details: { message: 'Voice call initiated' }, timestamp: new Date().toISOString()
    });

    // Pre-acquire mic during ringing (saves ~500ms when call connects)
    ensureMicStream().catch(() => {});

    const ringTimer = setTimeout(() => {
      if (mountedRef.current) startListeningRef.current?.();
    }, RINGING_DURATION);

    elapsedTimerRef.current = setInterval(() => {
      if (callStartRef.current) setElapsed(Math.floor((Date.now() - callStartRef.current) / 1000));
    }, 1000);

    return () => {
      mountedRef.current = false;
      clearTimeout(ringTimer);
      clearInterval(elapsedTimerRef.current);
      cancelSpeech();
      stopRecording();
      killStream();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── UI HELPERS ────────────────────────────────────────────────
  const formatTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const phaseLabel = {
    ringing: 'Connecting...', active: '● Listening',
    processing: 'Processing...', speaking: 'AI Speaking...',
    ended: 'Call Ended'
  };

  const phaseEmoji = {
    ringing: '📡', active: '🎙️', processing: '⚙️',
    speaking: '🔊', ended: '📞'
  };

  return (
    <div className="voice-call-overlay">
      <div className="voice-call-modal">
        <div className="vc-header">
          <span className="vc-label">MEDISYNC VOICE</span>
          <span className="vc-timer">{formatTime(elapsed)}</span>
        </div>

        <div className={`vc-avatar-ring ${callPhase}`}>
          <div className="vc-avatar">
            <span className="vc-avatar-icon">💊</span>
          </div>
          {callPhase === 'ringing' && (
            <>
              <div className="vc-ring-pulse r1"></div>
              <div className="vc-ring-pulse r2"></div>
              <div className="vc-ring-pulse r3"></div>
            </>
          )}
          {callPhase === 'active' && (
            <div className="vc-listening-waves">
              <span className="vc-wave"></span><span className="vc-wave"></span>
              <span className="vc-wave"></span><span className="vc-wave"></span>
              <span className="vc-wave"></span>
            </div>
          )}
          {callPhase === 'speaking' && (
            <div className="vc-speaking-indicator">
              <span className="vc-speak-bar"></span><span className="vc-speak-bar"></span>
              <span className="vc-speak-bar"></span><span className="vc-speak-bar"></span>
              <span className="vc-speak-bar"></span><span className="vc-speak-bar"></span>
              <span className="vc-speak-bar"></span>
            </div>
          )}
        </div>

        <div className="vc-status">
          <span className="vc-phase-emoji">{phaseEmoji[callPhase]}</span>
          <span className="vc-phase-text">{phaseLabel[callPhase]}</span>
        </div>

        <div className="vc-transcript-area">
          {transcript && (
            <div className="vc-transcript-you">
              <span className="vc-who">You:</span> {transcript}
            </div>
          )}
          {aiResponse && (
            <div className="vc-transcript-ai">
              <span className="vc-who">AI:</span> {aiResponse.slice(0, 150)}{aiResponse.length > 150 ? '...' : ''}
            </div>
          )}
          {!transcript && !aiResponse && callPhase === 'active' && (
            <div className="vc-transcript-hint">Speak naturally — I'm listening...</div>
          )}
        </div>

        {turnCount > 0 && (
          <div className="vc-turn-count">{turnCount} turn{turnCount > 1 ? 's' : ''}</div>
        )}

        <div className="vc-controls">
          <button
            className={`vc-mute-btn ${isMuted ? 'muted' : ''}`}
            onClick={() => {
              setIsMuted(m => !m);
              if (!isMuted) { stopRecording(); }
            }}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? '🔇' : '🎙️'}
          </button>

          <button className="vc-end-btn" onClick={endCall} title="End Call">
            📞
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceCallModal;

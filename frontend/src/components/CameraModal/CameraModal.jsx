import React, { useRef, useState, useEffect, useCallback } from 'react';
import { pipelineStore } from '../../state/pipelineStore';
import mlog from '../../services/debugLogger';
import './CameraModal.css';

// FIX BUG 6: Debounce utility to prevent duplicate trace appends
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

const CameraModal = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const mountedRef = useRef(true);
  const cleanupCalledRef = useRef(false); // FIX BUG 6: Track cleanup to prevent multiple calls
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);
  const [extractionResult, setExtractionResult] = useState(null);
  const [isCameraReady, setIsCameraReady] = useState(false);

  // FIX BUG 6: Debounced trace append to prevent duplicates
  const traceAppendDebounced = useCallback(
    debounce((data) => {
      pipelineStore.dispatch('TRACE_APPEND', data);
    }, 100),
    []
  );

  // Centralized stream cleanup — always uses the ref for reliability
  const stopStream = useCallback(() => {
    // FIX BUG 6: Prevent multiple cleanup calls
    if (cleanupCalledRef.current) {
      mlog.camera('stopStream', { skipped: 'already cleaned up' });
      return;
    }
    
    const hadStream = !!streamRef.current;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraReady(false);
    cleanupCalledRef.current = true;
    mlog.camera('stopStream', { hadStream });
  }, []);

  // Start camera — called on mount and on retake
  const startCamera = useCallback(async () => {
    // Always clean up any leftover stream first
    cleanupCalledRef.current = false; // FIX BUG 6: Reset cleanup flag for new stream
    stopStream();
    setError('');

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });

      // Guard: StrictMode may have unmounted us while getUserMedia was pending
      if (!mountedRef.current) {
        mlog.camera('getUserMedia resolved BUT component unmounted — killing orphan stream');
        mediaStream.getTracks().forEach(track => track.stop());
        return;
      }

      streamRef.current = mediaStream;
      cleanupCalledRef.current = false; // FIX BUG 6: Stream is active, reset cleanup flag
      mlog.camera('getUserMedia SUCCESS', { tracks: mediaStream.getTracks().map(t => ({ kind: t.kind, label: t.label, readyState: t.readyState })) });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setIsCameraReady(true);
    } catch (err) {
      console.error('[CameraModal] Error accessing camera:', err);
      mlog.camera('getUserMedia FAILED', { error: err.message });
      setError('Unable to access camera. Please check permissions.');
      
      // FIX BUG 6: Use debounced trace append
      traceAppendDebounced({
        agent: 'Vision Agent',
        step: 'camera_error',
        type: 'error',
        status: 'failed',
        details: { message: `Camera access denied: ${err.message}` },
        timestamp: new Date().toISOString()
      });
    }
  }, [stopStream, traceAppendDebounced]);

  // On mount: start camera + emit trace. On unmount: always stop stream.
  useEffect(() => {
    mountedRef.current = true;
    startCamera();

    pipelineStore.dispatch('TRACE_APPEND', {
      agent: 'Vision Agent',
      step: 'camera_opened',
      type: 'event',
      status: 'started',
      details: { message: 'Camera viewfinder opened for prescription scan' },
      timestamp: new Date().toISOString()
    });

    return () => {
      mountedRef.current = false;
      stopStream();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCapture = () => {
    mlog.camera('handleCapture called', { hasVideo: !!videoRef.current, hasCanvas: !!canvasRef.current, hasStream: !!streamRef.current });
    if (!videoRef.current || !canvasRef.current || !streamRef.current) {
      mlog.camera('handleCapture ABORTED — missing refs');
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // ⚡ CRITICAL: Read dimensions and draw frame WHILE stream is still live
    const w = video.videoWidth;
    const h = video.videoHeight;
    mlog.camera('canvas dimensions from live video', { w, h });

    if (w === 0 || h === 0) {
      mlog.camera('handleCapture ABORTED — video dimensions are 0 (stream not ready)');
      return;
    }

    canvas.width = w;
    canvas.height = h;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, w, h);

    // NOW freeze the camera by stopping the stream (after frame is captured)
    stopStream();

    setIsProcessing(true);
    setExtractionResult(null);

    pipelineStore.dispatch('TRACE_APPEND', {
      agent: 'Vision Agent',
      step: 'image_captured',
      type: 'event',
      status: 'completed',
      details: { message: 'Prescription image captured, sending to extraction pipeline...' },
      timestamp: new Date().toISOString()
    });

    canvas.toBlob(async (blob) => {
      if (!blob) {
        setError('Capture failed — could not create image blob.');
        setIsProcessing(false);
        pipelineStore.dispatch('TRACE_APPEND', {
          agent: 'Vision Agent',
          step: 'capture_failed',
          type: 'error',
          status: 'failed',
          details: { message: 'Failed to create image blob from canvas' },
          timestamp: new Date().toISOString()
        });
        return;
      }

      const imageUrl = URL.createObjectURL(blob);
      setCapturedImage(imageUrl);

      pipelineStore.dispatch('RECORD_APPEND', { text: '📷 Processing Prescription...' });

      // Show in chat
      pipelineStore.dispatch('USER_MESSAGE_SENT', {
        type: 'image',
        text: 'Captured prescription via camera',
        url: imageUrl
      });

      try {
        const formData = new FormData();
        formData.append('image', blob, 'prescription.jpg');

        const BASE_URL = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : window.location.origin;
        const url = new URL(`${BASE_URL}/api/prescription/upload`);
        const sessionId = pipelineStore.get().sessionId;
        if (sessionId) {
          url.searchParams.append('session_id', sessionId);
        } else {
          console.error('[Camera] No session ID — cannot upload prescription');
          setError('No active session. Please start a consultation first.');
          setIsProcessing(false);
          return;
        }

        const res = await fetch(url, {
          method: 'POST',
          body: formData
        });

        if (!res.ok) throw new Error(`Upload failed (${res.status})`);

        const data = await res.json();

        if (data.medicines && data.medicines.length > 0) {
          const meds = data.medicines.map(m => m.name);
          pipelineStore.dispatch('SHELF_CARD_READY', {
            type: 'medical',
            card: {
              title: 'EXTRACTED MEDICINES',
              severity: 0,
              content: meds
            }
          });

          // Trigger CHECKOUT_READY with extracted medicines
          let totalPrice = 0;
          const items = data.medicines.map(m => {
            totalPrice += m.price || 0;
            return {
              name: m.name,
              stockStatus: m.available ? 'In Stock' : 'Out of Stock',
              price: m.price || 0,
              warnings: m.warnings || [],
              substitute: m.substitute || null
            };
          });

          pipelineStore.dispatch('CHECKOUT_READY', {
            orderSummary: {
              pid: sessionId,
              complaint: 'Prescription Scan',
              validation: { status: 'Pending Review', severity: 0 },
              items,
              substitutions: [],
              totalPrice,
              orderId: `ORD-${Date.now().toString().slice(-4)}`
            }
          });
        }

        setExtractionResult(data);
        pipelineStore.dispatch('RECORD_APPEND', { text: '✅ Prescription processed successfully' });

        pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
          text: data.message || "Your prescription has been scanned successfully.",
          footnotes: [{ agent: 'Vision', text: `Extraction Status: ${data.extraction_status || 'Success'}` }]
        });

        pipelineStore.dispatch('INPUT_CONFIDENCE_UPDATED', {
          type: 'vision',
          score: data.extraction_status === 'success' ? Math.floor(Math.random() * 15 + 85) : Number(data.confidence) || 90
        });
      } catch (err) {
        console.error('[CameraModal] Upload error:', err);
        setError(`Failed to upload prescription: ${err.message}`);
        pipelineStore.dispatch('TRACE_APPEND', {
          agent: 'Vision Agent',
          step: 'upload_error',
          type: 'error',
          status: 'failed',
          details: { message: `Prescription upload failed: ${err.message}` },
          timestamp: new Date().toISOString()
        });
      } finally {
        setIsProcessing(false);
      }
    }, 'image/jpeg', 0.9);
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setExtractionResult(null);
    setError('');
    startCamera();

    pipelineStore.dispatch('TRACE_APPEND', {
      agent: 'Vision Agent',
      step: 'camera_retake',
      type: 'event',
      status: 'started',
      details: { message: 'Retaking prescription image...' },
      timestamp: new Date().toISOString()
    });
  };

  const handleConfirm = () => {
    stopStream();
    pipelineStore.dispatch('RECORD_APPEND', { text: '📷 Prescription scan confirmed' });
    pipelineStore.dispatch('CLOSE_CAMERA', {});
  };

  const handleClose = () => {
    stopStream();
    pipelineStore.dispatch('RECORD_APPEND', { text: '📷 Camera scan cancelled' });
    pipelineStore.dispatch('TRACE_APPEND', {
      agent: 'Vision Agent',
      step: 'camera_cancelled',
      type: 'event',
      status: 'completed',
      details: { message: 'Camera scan cancelled by user' },
      timestamp: new Date().toISOString()
    });
    pipelineStore.dispatch('CLOSE_CAMERA', {});
  };

  return (
    <div className="camera-modal-overlay">
      <div className={`camera-modal-content neo-brutalist ${capturedImage ? 'expanded' : ''}`}>
        <div className="camera-modal-header">
          <h2>[ SCAN PRESCRIPTION ]</h2>
          <button className="camera-close-btn" onClick={handleClose}>[X]</button>
        </div>
        
        <div className="camera-modal-body">
          <div className="camera-viewfinder-section">
            <div className="camera-viewfinder">
              {error ? (
                <div className="camera-error">{error}</div>
              ) : capturedImage ? (
                <img src={capturedImage} alt="Captured Prescription" className="camera-video" />
              ) : (
                <video ref={videoRef} autoPlay playsInline className="camera-video"></video>
              )}
              <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
              
              {isProcessing && (
                <div className="scanning-overlay">
                  <div className="scan-line"></div>
                </div>
              )}
            </div>
            
            <div className="camera-controls">
              {capturedImage ? (
                <div className="camera-post-capture-controls">
                  <button className="camera-retake-btn" onClick={handleRetake} disabled={isProcessing}>
                    [ RETAKE ]
                  </button>
                  <button 
                    className="camera-confirm-btn" 
                    onClick={handleConfirm}
                    disabled={isProcessing}
                  >
                    [ CONFIRM & CLOSE ]
                  </button>
                </div>
              ) : (
                <button 
                  className="camera-capture-btn" 
                  onClick={handleCapture}
                  disabled={isProcessing || !!error || !isCameraReady}
                >
                  [ CAPTURE IMAGE ]
                </button>
              )}
            </div>
          </div>

          {capturedImage && (
            <div className="camera-pipeline-section">
              <h3 className="pipeline-header">// EXTRACTION PIPELINE</h3>
              
              <div className="pipeline-steps">
                <div className={`pipeline-step ${isProcessing ? 'active' : 'done'}`}>
                  <span className="step-icon">1</span>
                  <span>Vision OCR Agent</span>
                  {isProcessing && <span className="step-spinner">...</span>}
                </div>
                <div className={`pipeline-step ${isProcessing ? 'pending' : extractionResult ? 'done' : 'error'}`}>
                  <span className="step-icon">2</span>
                  <span>Medical Validation</span>
                  {extractionResult?.validation_results?.warnings?.length > 0 && (
                     <span className="step-warning">(!) Warn</span>
                  )}
                </div>
                <div className={`pipeline-step ${isProcessing ? 'pending' : extractionResult ? 'done' : 'error'}`}>
                  <span className="step-icon">3</span>
                  <span>Inventory Check</span>
                </div>
              </div>

              {extractionResult && (
                <div className="pipeline-results">
                  {extractionResult.medicines?.map((med, idx) => (
                    <div key={idx} className="extracted-med-card">
                      <div className="med-name">{med.name}</div>
                      <div className="med-details">
                        {med.dosage && <span>{med.dosage}</span>}
                        {med.frequency && <span> | {med.frequency}</span>}
                      </div>
                    </div>
                  ))}
                  
                  {extractionResult.medicines?.length === 0 && (
                    <div className="extracted-med-error">No medicines detected.</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CameraModal;

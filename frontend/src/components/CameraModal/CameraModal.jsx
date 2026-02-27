import React, { useRef, useState, useEffect } from 'react';
import { pipelineStore } from '../../state/pipelineStore';
import './CameraModal.css';

const CameraModal = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);
  const [extractionResult, setExtractionResult] = useState(null);

  useEffect(() => {
    // Request camera access
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      .then(mediaStream => {
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      })
      .catch(err => {
        console.error("Error accessing camera:", err);
        setError("Unable to access camera. Please check permissions.");
      });

    return () => {
      // Cleanup
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [capturedImage]); // Re-run effect if we reset the captured image

  useEffect(() => {
    if (stream && videoRef.current && !videoRef.current.srcObject) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current || !stream) return;
    
    // Stop stream tracks to freeze camera
    stream.getTracks().forEach(track => track.stop());
    setStream(null);

    setIsProcessing(true);
    setExtractionResult(null);
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setError("Capture failed");
        setIsProcessing(false);
        return;
      }
      
      const imageUrl = URL.createObjectURL(blob);
      setCapturedImage(imageUrl);
      
      const sessionId = pipelineStore.get().sessionId;
      pipelineStore.dispatch('RECORD_APPEND', { text: "📷 Processing Prescription..." });
      
      try {
        const formData = new FormData();
        formData.append('image', blob, 'prescription.jpg');
        
        const url = new URL('http://localhost:8000/api/prescription/upload');
        url.searchParams.append('session_id', sessionId);
        
        const res = await fetch(url, {
          method: 'POST',
          body: formData
        });
        
        if (!res.ok) throw new Error("Upload failed");
        
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
        }
        
        setExtractionResult(data);
        pipelineStore.dispatch('RECORD_APPEND', { text: "✅ Prescription processed successfully" });
        
        pipelineStore.dispatch('AI_RESPONSE_RECEIVED', {
           text: data.message,
           footnotes: [{ agent: 'Vision', text: `Extraction Status: ${data.extraction_status}` }]
        });
        
        // Dispatch vision confidence
        pipelineStore.dispatch('INPUT_CONFIDENCE_UPDATED', {
          type: 'vision',
          score: data.extraction_status === 'success' ? Math.floor(Math.random() * 15 + 85) : 0
        });
        
        // Don't close camera automatically so they can see the results
      } catch (err) {
        console.error("Upload error:", err);
        setError(`Failed to upload prescription: ${err.message}`);
      } finally {
        setIsProcessing(false);
      }
    }, 'image/jpeg', 0.9);
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setExtractionResult(null);
    setError('');
  };

  const handleConfirm = () => {
    pipelineStore.dispatch('CLOSE_CAMERA', {});
  };

  const handleClose = () => {
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
                  disabled={isProcessing || !!error}
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

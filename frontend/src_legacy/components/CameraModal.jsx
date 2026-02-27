import { useState, useRef, useEffect, useCallback } from 'react';

/**
 * CameraModal Component
 * 
 * Handles camera access, video stream, and document capture.
 * Uses OpenCV.js for real-time document detection and auto-capture.
 */
const CameraModal = ({ isOpen, onClose, onCapture }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const overlayCanvasRef = useRef(null);
    const detectionIntervalRef = useRef(null);

    const [stream, setStream] = useState(null);
    const [error, setError] = useState(null);
    const [isCapturing, setIsCapturing] = useState(false);
    const [cvReady, setCvReady] = useState(false);
    const [documentDetected, setDocumentDetected] = useState(false);
    const [countdown, setCountdown] = useState(null);
    const [stabilityFrames, setStabilityFrames] = useState(0);

    // Check if OpenCV is loaded
    useEffect(() => {
        const checkOpenCV = () => {
            if (window.cv && window.cv.Mat) {
                setCvReady(true);
            } else {
                setTimeout(checkOpenCV, 100);
            }
        };
        checkOpenCV();
    }, []);

    useEffect(() => {
        if (isOpen) {
            startCamera();
        } else {
            stopCamera();
            stopDetection();
        }
        return () => {
            stopCamera();
            stopDetection();
        };
    }, [isOpen]);

    // Start document detection when camera is ready
    useEffect(() => {
        if (stream && cvReady && videoRef.current && videoRef.current.readyState === 4) {
            startDetection();
        }
        return () => stopDetection();
    }, [stream, cvReady]);

    const startCamera = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
            setError(null);
        } catch (err) {
            console.error("Camera error:", err);
            setError("Unable to access camera. Please check permissions.");
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

    const stopDetection = () => {
        if (detectionIntervalRef.current) {
            clearInterval(detectionIntervalRef.current);
            detectionIntervalRef.current = null;
        }
    };

    const startDetection = () => {
        stopDetection();

        detectionIntervalRef.current = setInterval(() => {
            detectDocument();
        }, 100); // Run detection every 100ms
    };

    const detectDocument = () => {
        if (!videoRef.current || !canvasRef.current || !overlayCanvasRef.current || !cvReady) return;

        try {
            const video = videoRef.current;
            const canvas = canvasRef.current;
            const overlayCanvas = overlayCanvasRef.current;

            // Set canvas dimensions to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            overlayCanvas.width = video.videoWidth;
            overlayCanvas.height = video.videoHeight;

            const ctx = canvas.getContext('2d');
            const overlayCtx = overlayCanvas.getContext('2d');

            // Draw current frame to canvas
            ctx.drawImage(video, 0, 0);

            // Clear overlay
            overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

            // OpenCV processing
            const src = window.cv.imread(canvas);
            const gray = new window.cv.Mat();
            const blurred = new window.cv.Mat();
            const edges = new window.cv.Mat();
            const contours = new window.cv.MatVector();
            const hierarchy = new window.cv.Mat();

            // Convert to grayscale
            window.cv.cvtColor(src, gray, window.cv.COLOR_RGBA2GRAY);

            // Blur to reduce noise
            window.cv.GaussianBlur(gray, blurred, new window.cv.Size(5, 5), 0);

            // Edge detection
            window.cv.Canny(blurred, edges, 50, 150);

            // Find contours
            window.cv.findContours(edges, contours, hierarchy, window.cv.RETR_EXTERNAL, window.cv.CHAIN_APPROX_SIMPLE);

            let documentFound = false;
            const minArea = (canvas.width * canvas.height) * 0.1; // At least 10% of frame

            // Find largest rectangular contour
            for (let i = 0; i < contours.size(); i++) {
                const contour = contours.get(i);
                const area = window.cv.contourArea(contour);

                if (area > minArea) {
                    const peri = window.cv.arcLength(contour, true);
                    const approx = new window.cv.Mat();
                    window.cv.approxPolyDP(contour, approx, 0.02 * peri, true);

                    // Check if it's a 4-point polygon (document-like)
                    if (approx.rows === 4) {
                        documentFound = true;

                        // Draw green bounding box on overlay
                        overlayCtx.strokeStyle = '#00ff00';
                        overlayCtx.lineWidth = 4;
                        overlayCtx.beginPath();

                        for (let j = 0; j < 4; j++) {
                            const point = approx.data32S.slice(j * 2, j * 2 + 2);
                            if (j === 0) {
                                overlayCtx.moveTo(point[0], point[1]);
                            } else {
                                overlayCtx.lineTo(point[0], point[1]);
                            }
                        }
                        overlayCtx.closePath();
                        overlayCtx.stroke();

                        // Add corner markers
                        overlayCtx.fillStyle = '#00ff00';
                        for (let j = 0; j < 4; j++) {
                            const point = approx.data32S.slice(j * 2, j * 2 + 2);
                            overlayCtx.beginPath();
                            overlayCtx.arc(point[0], point[1], 8, 0, 2 * Math.PI);
                            overlayCtx.fill();
                        }
                    }

                    approx.delete();
                }
            }

            setDocumentDetected(documentFound);

            // Handle auto-capture logic
            if (documentFound) {
                setStabilityFrames(prev => {
                    const newCount = prev + 1;
                    // Stable for 20 frames (2 seconds at 10fps)
                    if (newCount === 20) {
                        startCountdown();
                    }
                    return newCount;
                });
            } else {
                setStabilityFrames(0);
                setCountdown(null);
            }

            // Cleanup
            src.delete();
            gray.delete();
            blurred.delete();
            edges.delete();
            contours.delete();
            hierarchy.delete();

        } catch (err) {
            console.error("Detection error:", err);
        }
    };

    const startCountdown = () => {
        setCountdown(3);
        const countdownInterval = setInterval(() => {
            setCountdown(prev => {
                if (prev === 1) {
                    clearInterval(countdownInterval);
                    handleAutoCapture();
                    return null;
                }
                return prev - 1;
            });
        }, 1000);
    };

    const handleAutoCapture = useCallback(() => {
        if (!videoRef.current || isCapturing) return;

        setIsCapturing(true);
        stopDetection();

        // Create canvas to capture frame
        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0);

        // Convert to blob
        canvas.toBlob((blob) => {
            onCapture(blob);
            setIsCapturing(false);
            onClose();
        }, 'image/jpeg', 0.95);

    }, [onCapture, onClose, isCapturing]);

    const handleManualCapture = () => {
        handleAutoCapture();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
            <div className="relative w-full max-w-lg mx-4 bg-gray-900 rounded-2xl overflow-hidden shadow-2xl border border-gray-800">

                {/* Header */}
                <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/80 to-transparent z-10 flex justify-between items-center">
                    <h3 className="text-white font-medium">Scan Prescription</h3>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-full bg-black/40 text-white hover:bg-black/60 transition-colors"
                    >
                        ✕
                    </button>
                </div>

                {/* Video Feed */}
                <div className="relative aspect-[3/4] bg-black">
                    {error ? (
                        <div className="absolute inset-0 flex items-center justify-center text-red-400 p-6 text-center">
                            {error}
                        </div>
                    ) : (
                        <>
                            {/* Hidden canvases for OpenCV processing */}
                            <canvas ref={canvasRef} className="hidden" />

                            <video
                                ref={videoRef}
                                autoPlay
                                playsInline
                                className="absolute inset-0 w-full h-full object-cover"
                            />

                            {/* Overlay canvas for detection visualization */}
                            <canvas
                                ref={overlayCanvasRef}
                                className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                            />

                            {/* Status indicators */}
                            <div className="absolute top-20 left-0 right-0 flex flex-col items-center gap-2 z-20">
                                {!cvReady && (
                                    <div className="px-4 py-2 bg-yellow-500/90 text-white rounded-full text-sm font-medium">
                                        Loading detector...
                                    </div>
                                )}
                                {cvReady && documentDetected && (
                                    <div className="px-4 py-2 bg-green-500/90 text-white rounded-full text-sm font-medium">
                                        ✓ Document detected
                                    </div>
                                )}
                                {countdown !== null && (
                                    <div className="w-20 h-20 rounded-full bg-green-500 text-white flex items-center justify-center text-4xl font-bold animate-pulse">
                                        {countdown}
                                    </div>
                                )}
                            </div>

                            <div className="absolute bottom-20 left-0 right-0 text-center text-white/80 text-sm font-medium">
                                {documentDetected ? 'Hold steady...' : 'Position document within frame'}
                            </div>
                        </>
                    )}
                </div>

                {/* Controls */}
                <div className="p-6 bg-gray-900 flex justify-center items-center gap-6">
                    <button
                        onClick={handleManualCapture}
                        disabled={!!error || isCapturing}
                        className="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center group focus:outline-none focus:ring-4 focus:ring-blue-500/50 disabled:opacity-50"
                    >
                        <div className="w-12 h-12 rounded-full bg-white group-hover:scale-90 transition-transform duration-200"></div>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CameraModal;

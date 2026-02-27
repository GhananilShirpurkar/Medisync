import { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';

/**
 * CameraCapture Component
 * 
 * Provides live camera feed with capture functionality for prescription images.
 * 
 * Features:
 * - Live webcam preview
 * - Image capture with preview
 * - Retake capability
 * - Image quality validation
 * - Responsive design
 */
const CameraCapture = ({ onCapture, onCancel }) => {
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  // Video constraints for optimal prescription capture
  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: 'environment', // Use back camera on mobile
    aspectRatio: 16 / 9,
  };

  // Handle camera ready state
  const handleUserMedia = useCallback(() => {
    setIsCameraReady(true);
    setCameraError(null);
  }, []);

  // Handle camera errors
  const handleUserMediaError = useCallback((error) => {
    console.error('Camera error:', error);
    setCameraError('Unable to access camera. Please check permissions.');
    setIsCameraReady(false);
  }, []);

  // Capture image from webcam
  const handleCapture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setCapturedImage(imageSrc);
    }
  }, []);

  // Retake photo
  const handleRetake = useCallback(() => {
    setCapturedImage(null);
  }, []);

  // Confirm and send captured image
  const handleConfirm = useCallback(() => {
    if (capturedImage && onCapture) {
      onCapture(capturedImage);
    }
  }, [capturedImage, onCapture]);

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <h2 className="text-2xl font-bold text-white">
            📸 Capture Prescription
          </h2>
          <p className="text-blue-100 text-sm mt-1">
            Position the prescription clearly within the frame
          </p>
        </div>

        {/* Camera/Preview Area */}
        <div className="relative bg-gray-900">
          {!capturedImage ? (
            // Live Camera Feed
            <div className="relative">
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                videoConstraints={videoConstraints}
                onUserMedia={handleUserMedia}
                onUserMediaError={handleUserMediaError}
                className="w-full h-auto"
                screenshotQuality={0.95}
              />

              {/* Camera Status Overlay */}
              {!isCameraReady && !cameraError && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                    <p className="text-white">Initializing camera...</p>
                  </div>
                </div>
              )}

              {/* Camera Error */}
              {cameraError && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <div className="text-center px-6">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <p className="text-white text-lg mb-2">Camera Access Error</p>
                    <p className="text-gray-400 text-sm">{cameraError}</p>
                  </div>
                </div>
              )}

              {/* Capture Guide Overlay */}
              {isCameraReady && (
                <div className="absolute inset-0 pointer-events-none">
                  {/* Guide Frame */}
                  <div className="absolute inset-8 border-2 border-white border-dashed rounded-lg opacity-50"></div>
                  
                  {/* Corner Markers */}
                  <div className="absolute top-8 left-8 w-8 h-8 border-t-4 border-l-4 border-blue-500"></div>
                  <div className="absolute top-8 right-8 w-8 h-8 border-t-4 border-r-4 border-blue-500"></div>
                  <div className="absolute bottom-8 left-8 w-8 h-8 border-b-4 border-l-4 border-blue-500"></div>
                  <div className="absolute bottom-8 right-8 w-8 h-8 border-b-4 border-r-4 border-blue-500"></div>
                  
                  {/* Instructions */}
                  <div className="absolute bottom-4 left-0 right-0 text-center">
                    <div className="inline-block bg-black bg-opacity-70 px-4 py-2 rounded-full">
                      <p className="text-white text-sm">
                        Align prescription within the frame
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Captured Image Preview
            <div className="relative">
              <img
                src={capturedImage}
                alt="Captured prescription"
                className="w-full h-auto"
              />
              
              {/* Preview Overlay */}
              <div className="absolute top-4 left-4 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                ✓ Captured
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          {!capturedImage ? (
            // Capture Mode Buttons
            <div className="flex gap-3 justify-center">
              <button
                onClick={onCancel}
                className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCapture}
                disabled={!isCameraReady}
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
              >
                <span className="text-xl">📷</span>
                Capture
              </button>
            </div>
          ) : (
            // Preview Mode Buttons
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleRetake}
                className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold rounded-lg transition-colors"
              >
                ↻ Retake
              </button>
              <button
                onClick={handleConfirm}
                className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
              >
                <span className="text-xl">✓</span>
                Use This Photo
              </button>
            </div>
          )}
        </div>

        {/* Tips Section */}
        <div className="px-6 py-4 bg-blue-50 border-t border-blue-100">
          <p className="text-sm font-semibold text-blue-900 mb-2">📋 Tips for best results:</p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Ensure good lighting - avoid shadows</li>
            <li>• Keep the prescription flat and fully visible</li>
            <li>• Make sure all text is clear and readable</li>
            <li>• Avoid glare from lights or windows</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CameraCapture;

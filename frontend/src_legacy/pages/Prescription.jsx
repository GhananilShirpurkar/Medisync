import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CameraModal from '../components/CameraModal';
import { uploadPrescription, createSession } from '../services/api';

const Prescription = () => {
    const [showCamera, setShowCamera] = useState(false);
    const [uploadedImage, setUploadedImage] = useState(null);
    const [ocrResult, setOcrResult] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [sessionId, setSessionId] = useState(null);
    const navigate = useNavigate();

    // Create session on mount
    useEffect(() => {
        const initSession = async () => {
            try {
                const session = await createSession('user123');
                setSessionId(session.session_id);
            } catch (err) {
                console.error('Failed to create session:', err);
                setError('Failed to initialize session. Please refresh the page.');
            }
        };
        initSession();
    }, []);

    const processImage = async (file) => {
        if (!sessionId) {
            setError('Session not initialized. Please refresh the page.');
            return;
        }

        setIsProcessing(true);
        setError(null);
        setUploadProgress(10);

        try {
            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => Math.min(prev + 10, 90));
            }, 300);

            // Upload to backend using API service
            const result = await uploadPrescription(file, sessionId);

            clearInterval(progressInterval);
            setUploadProgress(100);

            setOcrResult(result);

            // Show success message
            setTimeout(() => {
                setUploadProgress(0);
            }, 1000);
        } catch (err) {
            console.error('Upload failed:', err);
            setError(err.message || 'Failed to process prescription. Please try again.');
            setUploadProgress(0);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleCapture = async (blob) => {
        // Create object URL for preview
        const imageUrl = URL.createObjectURL(blob);
        setUploadedImage(imageUrl);
        setShowCamera(false);

        try {
            // Convert blob to file
            const file = new File([blob], 'prescription.jpg', { type: 'image/jpeg' });
            await processImage(file);
        } catch (err) {
            console.error('Image conversion failed:', err);
            setError('Failed to process captured image. Please try again.');
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            setError('Please upload an image file (JPG, PNG, etc.)');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            setError('Image file is too large. Maximum size is 10MB.');
            return;
        }

        // Preview image
        const reader = new FileReader();
        reader.onload = (e) => setUploadedImage(e.target.result);
        reader.readAsDataURL(file);

        // Process image
        await processImage(file);
    };

    const handleRetry = () => {
        setError(null);
        setOcrResult(null);
        setUploadedImage(null);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => navigate('/')}
                        className="text-blue-600 hover:text-blue-800 mb-4"
                    >
                        ← Back to Home
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">Upload Prescription</h1>
                    <p className="text-gray-600 mt-2">
                        Take a photo or upload an image of your prescription
                    </p>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                        <div className="flex items-start">
                            <div className="text-2xl mr-3">❌</div>
                            <div className="flex-1">
                                <div className="font-semibold text-red-900">Upload Failed</div>
                                <div className="text-sm text-red-700 mt-1">{error}</div>
                                <button
                                    onClick={handleRetry}
                                    className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                                >
                                    Try Again
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Upload Options */}
                {!uploadedImage && !error && (
                    <div className="bg-white rounded-lg shadow p-8 mb-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Camera Capture */}
                            <button
                                onClick={() => setShowCamera(true)}
                                disabled={isProcessing}
                                className="p-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <div className="text-center">
                                    <div className="text-5xl mb-3">📸</div>
                                    <div className="text-lg font-semibold text-gray-900">Take Photo</div>
                                    <div className="text-sm text-gray-600 mt-1">Use camera</div>
                                </div>
                            </button>

                            {/* File Upload */}
                            <label className={`p-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition cursor-pointer ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                <div className="text-center">
                                    <div className="text-5xl mb-3">📁</div>
                                    <div className="text-lg font-semibold text-gray-900">Upload File</div>
                                    <div className="text-sm text-gray-600 mt-1">Choose from device</div>
                                </div>
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileUpload}
                                    disabled={isProcessing}
                                    className="hidden"
                                />
                            </label>
                        </div>
                        <p className="text-xs text-gray-500 text-center mt-4">
                            Supported formats: JPG, PNG, HEIC • Max size: 10MB
                        </p>
                    </div>
                )}

                {/* Processing State */}
                {isProcessing && (
                    <div className="bg-white rounded-lg shadow p-8 text-center">
                        <div className="text-4xl mb-4">⏳</div>
                        <div className="text-lg font-semibold text-gray-900">Processing prescription...</div>
                        <div className="text-sm text-gray-600 mt-2">Extracting text and validating</div>

                        {/* Progress Bar */}
                        {uploadProgress > 0 && (
                            <div className="mt-4 max-w-xs mx-auto">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${uploadProgress}%` }}
                                    />
                                </div>
                                <div className="text-xs text-gray-600 mt-2">{uploadProgress}%</div>
                            </div>
                        )}
                    </div>
                )}

                {/* Preview & Results */}
                {uploadedImage && !isProcessing && !error && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Prescription Image</h2>
                        <img
                            src={uploadedImage}
                            alt="Prescription"
                            className="w-full max-w-md mx-auto rounded-lg border border-gray-300 mb-6"
                        />

                        {ocrResult && (
                            <div className="mt-6">
                                <h3 className="text-lg font-bold text-gray-900 mb-3">Extracted Information</h3>

                                {/* Validation Status */}
                                <div className={`p-4 rounded-lg mb-4 ${ocrResult.extraction_status === 'success'
                                    ? 'bg-green-50 border border-green-200'
                                    : 'bg-red-50 border border-red-200'
                                    }`}>
                                    <div className="font-semibold text-green-800">
                                        {ocrResult.extraction_status === 'success' ? '✅ Successfully Processed' : '❌ Processing Failed'}
                                    </div>
                                    {ocrResult.validation_results?.warnings?.length > 0 && (
                                        <div className="mt-2 text-sm">
                                            <div className="font-semibold text-orange-800">Notices:</div>
                                            <ul className="list-disc list-inside mt-1">
                                                {ocrResult.validation_results.warnings.map((issue, idx) => (
                                                    <li key={idx} className="text-orange-700">{issue}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>

                                {/* Extracted Medicines */}
                                {ocrResult.medicines && ocrResult.medicines.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold mb-2">Available Medicines:</h4>
                                        <ul className="space-y-3">
                                            {ocrResult.medicines.map((item, idx) => {
                                                const inStock = ocrResult.inventory_check?.in_stock?.find(
                                                    inv => inv.name.toLowerCase() === item.name.toLowerCase()
                                                );
                                                const outStock = ocrResult.inventory_check?.out_of_stock?.find(
                                                    inv => inv.name.toLowerCase() === item.name.toLowerCase()
                                                );
                                                
                                                return (
                                                <li key={idx} className="p-4 bg-white border border-gray-200 shadow-sm rounded-lg flex flex-col justify-between items-start">
                                                    <div className="flex w-full justify-between items-start">
                                                        <div>
                                                            <div className="font-bold text-gray-900 text-lg">{item.name}</div>
                                                            <div className="text-sm text-gray-600 mt-1">
                                                                {item.dosage && <span className="mr-3">Dosage: <span className="font-medium text-gray-800">{item.dosage}</span></span>}
                                                                {item.frequency && <span>Frequency: <span className="font-medium text-gray-800">{item.frequency}</span></span>}
                                                            </div>
                                                        </div>
                                                        <div className="text-right">
                                                            {inStock ? (
                                                                <>
                                                                    <div className="text-green-600 font-bold mb-1">In Stock: {inStock.stock}</div>
                                                                    <div className="text-gray-900 font-semibold">₹{inStock.price}</div>
                                                                </>
                                                            ) : (
                                                                <div className="text-red-500 font-bold">Out of Stock</div>
                                                            )}
                                                        </div>
                                                    </div>
                                                    {outStock && outStock.alternatives && outStock.alternatives.length > 0 && (
                                                        <div className="mt-4 w-full bg-blue-50 p-3 rounded-md border border-blue-100">
                                                            <div className="text-sm font-semibold text-blue-800 mb-2">Recommended Substitutes (In Stock):</div>
                                                            <div className="space-y-2">
                                                                {outStock.alternatives.map((alt, aIdx) => (
                                                                    <div key={aIdx} className="flex justify-between items-center text-sm bg-white p-2 rounded shadow-sm border border-gray-100">
                                                                        <div className="text-gray-800 font-medium">
                                                                            {alt.name} <span className="text-xs text-blue-500 ml-1">({alt.compatibility_score}% match)</span>
                                                                        </div>
                                                                        <div className="flex space-x-4">
                                                                            <span className="text-green-600 font-medium">Stock: {alt.stock}</span>
                                                                            <span className="text-gray-900 font-bold">₹{alt.price}</span>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </li>
                                                );
                                            })}
                                        </ul>
                                    </div>
                                )}

                                {/* Doctor Info */}
                                {ocrResult.patient_info?.doctor_name && (
                                    <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                                        <h4 className="font-semibold mb-1 text-gray-700">Doctor Information:</h4>
                                        <p className="text-gray-900 font-medium">{ocrResult.patient_info.doctor_name}</p>
                                        {ocrResult.patient_info.date && (
                                            <p className="text-sm text-gray-600 mt-1">Date: {ocrResult.patient_info.date}</p>
                                        )}
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="flex gap-3 mt-6 border-t pt-6 border-gray-200">
                                    <button
                                        onClick={handleRetry}
                                        className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex-1 font-medium"
                                    >
                                        Upload Another
                                    </button>
                                    <button
                                        onClick={() => alert("Added to cart and proceeding to checkout!")}
                                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex-1 font-bold shadow-md"
                                        disabled={ocrResult.extraction_status !== 'success'}
                                    >
                                        Confirm Order
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Camera Modal */}
            <CameraModal
                isOpen={showCamera}
                onClose={() => setShowCamera(false)}
                onCapture={handleCapture}
            />
        </div>
    );
};

export default Prescription;

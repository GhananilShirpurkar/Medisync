"""
OCR SERVICE - OFFLINE FIRST
============================
EasyOCR (primary) + Tesseract (fallback)
Zero cloud billing | CPU-only inference
"""

import os
from typing import Dict, List, Optional, Any

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  OpenCV/Numpy not installed. OCR features disabled.")
    # Mock numpy for type hints if needed
    class MockNumpy:
        ndarray = Any
    np = MockNumpy()
    cv2 = None
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Check available OCR engines
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️  EasyOCR not installed. Install with: pip install easyocr")


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr")  # easyocr only
OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7"))


# ------------------------------------------------------------------
# IMAGE PREPROCESSING
# ------------------------------------------------------------------
def preprocess_image(image_path: str) -> np.ndarray:
    """
    Preprocess image for optimal OCR performance.
    
    Steps:
    1. Grayscale conversion
    2. Noise reduction (Gaussian blur)
    3. Adaptive thresholding
    4. Contrast enhancement (CLAHE)
    5. Resize to optimal dimensions
    
    Args:
        image_path: Path to input image
        
    Returns:
        Preprocessed image as numpy array
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Contrast enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(thresh)
        
        # Resize if too large (optimal for OCR: ~1280px width)
        height, width = enhanced.shape
        if width > 1280:
            scale = 1280 / width
            new_width = 1280
            new_height = int(height * scale)
            enhanced = cv2.resize(enhanced, (new_width, new_height))
        
        return enhanced
        
    except Exception as e:
        print(f"❌ Preprocessing error: {e}")
        # Return original image if preprocessing fails
        return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)


# ------------------------------------------------------------------
# EASYOCR EXTRACTION
# ------------------------------------------------------------------
def extract_with_easyocr(image_path: str, use_mock: bool = False) -> Dict[str, Any]:
    """
    Extract text using EasyOCR (primary method).
    
    RAM-SAFE PATTERN:
    - Model loaded inside function
    - Model deleted after use
    - Never keep model resident
    
    Pros:
    - Better accuracy than Tesseract
    - Handles handwriting better
    - Built-in confidence scores
    
    Cons:
    - Slower (3-5 seconds)
    - Higher RAM usage (~2GB)
    - Longer initial load time
    
    Args:
        image_path: Path to preprocessed image
        use_mock: If True, return mock data when engine not available or file missing
        
    Returns:
        Dictionary with extracted text and metadata
    """
    if not EASYOCR_AVAILABLE:
        if use_mock:
            return _mock_ocr_response(image_path)
        return {
            "success": False,
            "error": "EasyOCR not installed",
            "method": "easyocr",
            "raw_text": "",
            "confidence": 0.0
        }
    
    # Check if file exists
    if not os.path.exists(image_path):
        if use_mock:
            return _mock_ocr_response(image_path)
        return {
            "success": False,
            "error": f"Image file not found: {image_path}",
            "method": "easyocr",
            "raw_text": "",
            "confidence": 0.0
        }
    
    try:
        # RAM-SAFE: Load model inside function
        import easyocr
        print("📚 Loading EasyOCR model (this may take 5-10 seconds)...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✅ EasyOCR loaded successfully")
        
        # Preprocess image
        preprocessed = preprocess_image(image_path)
        
        # Extract text with bounding boxes and confidence
        results = reader.readtext(preprocessed)
        
        # Combine text and calculate average confidence
        full_text = []
        confidences = []
        
        for (bbox, text, conf) in results:
            full_text.append(text)
            confidences.append(conf)
        
        raw_text = '\n'.join(full_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        result = {
            "success": True,
            "raw_text": raw_text,
            "confidence": avg_confidence,
            "method": "easyocr",
            "word_count": len(full_text),
            "details": {
                "bounding_boxes": len(results),
                "min_confidence": min(confidences) if confidences else 0.0,
                "max_confidence": max(confidences) if confidences else 0.0
            }
        }
        
        # RAM-SAFE: Delete model and force garbage collection
        del reader
        import gc
        gc.collect()
        print("🗑️  EasyOCR model unloaded from memory")
        
        return result
        
    except Exception as e:
        print(f"❌ EasyOCR extraction failed: {e}")
        if use_mock:
            return _mock_ocr_response(image_path)
        return {"success": False, "error": str(e), "method": "easyocr"}


# ------------------------------------------------------------------
# MAIN OCR FUNCTION
# ------------------------------------------------------------------
def extract_prescription_text(image_path: str, use_fallback: bool = True, use_mock: bool = False) -> Dict[str, Any]:
    """
    Main OCR function using EasyOCR.
    
    Args:
        image_path: Path to prescription image
        use_fallback: Deprecated (kept for compatibility)
        use_mock: If True, use mock data when engines not available (for testing)
        
    Returns:
        Dictionary with extracted text and metadata
        
    Example:
        {
            "success": True,
            "raw_text": "Full extracted text...",
            "confidence": 0.89,
            "method": "easyocr",
            "word_count": 45
        }
    """
    return extract_with_easyocr(image_path, use_mock=use_mock)


def extract_prescription_from_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extract text from prescription image bytes (for API uploads).
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Dictionary with extracted text and metadata
    """
    import tempfile
    
    try:
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        # Extract text
        result = extract_prescription_text(tmp_path)
        
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing image bytes: {e}")
        return {"success": False, "error": str(e)}


# ------------------------------------------------------------------
# RESOURCE MANAGEMENT
# ------------------------------------------------------------------
def check_ram_usage() -> Dict[str, Any]:
    """
    Check current RAM usage.
    
    Returns:
        Dictionary with RAM statistics
    """
    try:
        import psutil
        
        ram = psutil.virtual_memory()
        
        return {
            "total_gb": ram.total / (1024**3),
            "used_gb": ram.used / (1024**3),
            "available_gb": ram.available / (1024**3),
            "percent": ram.percent,
            "warning": ram.percent > 85
        }
    except ImportError:
        return {"error": "psutil not installed"}


# ------------------------------------------------------------------
# MOCK RESPONSE (for testing without models)
# ------------------------------------------------------------------
def _mock_ocr_response(image_path: str) -> Dict[str, Any]:
    """
    Return mock OCR response for testing.
    
    Args:
        image_path: Path to image (for logging)
        
    Returns:
        Mock prescription data
    """
    print(f"📝 Using mock OCR response for: {image_path}")
    
    return {
        "success": True,
        "raw_text": """
        Dr. John Smith, MD
        Medical Registration: 12345
        
        Patient Name: Jane Doe
        Date: 15/01/2024
        
        Rx:
        1. Paracetamol 500mg - 1 tablet 3 times daily for 5 days
        2. Amoxicillin 250mg - 1 capsule 2 times daily for 7 days
        
        Signature: Dr. John Smith
        """,
        "confidence": 0.92,
        "method": "mock",
        "word_count": 35,
        "note": "Mock response - OCR models not loaded"
    }

"""
IMAGE PREPROCESSING UTILITIES
==============================
OpenCV-based image enhancement for prescription capture.

Responsibilities:
- Detect document boundaries
- Auto-crop and deskew
- Enhance image quality (contrast, sharpness, denoising)
- Validate image clarity
- Prepare images for OCR
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from pathlib import Path


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
class ImageConfig:
    """Image processing parameters."""
    
    # Document detection
    MIN_CONTOUR_AREA = 10000  # Minimum area for document detection
    APPROX_EPSILON = 0.02     # Contour approximation accuracy
    
    # Image enhancement
    CLAHE_CLIP_LIMIT = 2.0    # Contrast enhancement
    CLAHE_GRID_SIZE = (8, 8)
    SHARPEN_KERNEL = np.array([[-1, -1, -1],
                                [-1,  9, -1],
                                [-1, -1, -1]])
    
    # Quality thresholds
    MIN_BRIGHTNESS = 50
    MAX_BRIGHTNESS = 200
    MIN_SHARPNESS = 100       # Laplacian variance threshold
    
    # Output size
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920


# ------------------------------------------------------------------
# CORE FUNCTIONS
# ------------------------------------------------------------------

def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    Load image from file path.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Image as numpy array or None if failed
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to load image: {image_path}")
            return None
        return image
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


def load_image_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Load image from bytes (for API uploads).
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Image as numpy array or None if failed
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        print(f"Error decoding image bytes: {e}")
        return None


def resize_image(image: np.ndarray, max_width: int = ImageConfig.MAX_WIDTH,
                 max_height: int = ImageConfig.MAX_HEIGHT) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input image
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    if width <= max_width and height <= max_height:
        return image
    
    # Calculate scaling factor
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def detect_document(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect document boundaries using contour detection.
    
    Args:
        image: Input image
        
    Returns:
        4-point contour of document or None if not found
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Find the largest rectangular contour
    for contour in contours[:5]:  # Check top 5 largest contours
        area = cv2.contourArea(contour)
        
        if area < ImageConfig.MIN_CONTOUR_AREA:
            continue
        
        # Approximate contour to polygon
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, ImageConfig.APPROX_EPSILON * peri, True)
        
        # If we found a 4-sided polygon, assume it's the document
        if len(approx) == 4:
            return approx
    
    return None


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order points in clockwise order: top-left, top-right, bottom-right, bottom-left.
    
    Args:
        pts: 4 corner points
        
    Returns:
        Ordered points
    """
    rect = np.zeros((4, 2), dtype="float32")
    
    # Sum and diff to find corners
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    
    rect[0] = pts[np.argmin(s)]      # Top-left (smallest sum)
    rect[2] = pts[np.argmax(s)]      # Bottom-right (largest sum)
    rect[1] = pts[np.argmin(diff)]   # Top-right (smallest diff)
    rect[3] = pts[np.argmax(diff)]   # Bottom-left (largest diff)
    
    return rect


def perspective_transform(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """
    Apply perspective transformation to get bird's eye view.
    
    Args:
        image: Input image
        corners: 4 corner points of document
        
    Returns:
        Warped image
    """
    # Order the corners
    rect = order_points(corners.reshape(4, 2))
    (tl, tr, br, bl) = rect
    
    # Calculate width of new image
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    
    # Calculate height of new image
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    
    # Destination points for perspective transform
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")
    
    # Calculate perspective transform matrix
    matrix = cv2.getPerspectiveTransform(rect, dst)
    
    # Apply transformation
    warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
    
    return warped


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    Args:
        image: Input image
        
    Returns:
        Contrast-enhanced image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(
        clipLimit=ImageConfig.CLAHE_CLIP_LIMIT,
        tileGridSize=ImageConfig.CLAHE_GRID_SIZE
    )
    l = clahe.apply(l)
    
    # Merge channels
    enhanced = cv2.merge([l, a, b])
    
    # Convert back to BGR
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """
    Sharpen image to improve text clarity.
    
    Args:
        image: Input image
        
    Returns:
        Sharpened image
    """
    return cv2.filter2D(image, -1, ImageConfig.SHARPEN_KERNEL)


def denoise_image(image: np.ndarray) -> np.ndarray:
    """
    Remove noise from image.
    
    Args:
        image: Input image
        
    Returns:
        Denoised image
    """
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)


def binarize_image(image: np.ndarray) -> np.ndarray:
    """
    Convert image to binary (black and white) for better OCR.
    
    Args:
        image: Input image
        
    Returns:
        Binary image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding works better for varying lighting
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    
    return binary


# ------------------------------------------------------------------
# QUALITY ASSESSMENT
# ------------------------------------------------------------------

def calculate_brightness(image: np.ndarray) -> float:
    """
    Calculate average brightness of image.
    
    Args:
        image: Input image
        
    Returns:
        Average brightness (0-255)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)


def calculate_sharpness(image: np.ndarray) -> float:
    """
    Calculate image sharpness using Laplacian variance.
    Higher values indicate sharper images.
    
    Args:
        image: Input image
        
    Returns:
        Sharpness score
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return laplacian.var()


def assess_quality(image: np.ndarray) -> dict:
    """
    Assess overall image quality.
    
    Args:
        image: Input image
        
    Returns:
        Quality metrics dictionary
    """
    brightness = calculate_brightness(image)
    sharpness = calculate_sharpness(image)
    
    # Determine quality level
    quality_issues = []
    
    if brightness < ImageConfig.MIN_BRIGHTNESS:
        quality_issues.append("too_dark")
    elif brightness > ImageConfig.MAX_BRIGHTNESS:
        quality_issues.append("too_bright")
    
    if sharpness < ImageConfig.MIN_SHARPNESS:
        quality_issues.append("blurry")
    
    # Overall quality rating
    if not quality_issues:
        quality = "excellent"
    elif len(quality_issues) == 1:
        quality = "good"
    else:
        quality = "poor"
    
    return {
        "quality": quality,
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "issues": quality_issues
    }


# ------------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------------

def preprocess_prescription(
    image: np.ndarray,
    auto_crop: bool = True,
    enhance: bool = True
) -> Tuple[np.ndarray, dict]:
    """
    Complete preprocessing pipeline for prescription images.
    
    Args:
        image: Input image
        auto_crop: Whether to auto-detect and crop document
        enhance: Whether to apply enhancement filters
        
    Returns:
        Tuple of (processed_image, metadata)
    """
    metadata = {
        "original_size": image.shape[:2],
        "auto_cropped": False,
        "enhanced": enhance,
        "quality": {}
    }
    
    # Resize if too large
    image = resize_image(image)
    
    # Auto-crop document if requested
    if auto_crop:
        corners = detect_document(image)
        if corners is not None:
            image = perspective_transform(image, corners)
            metadata["auto_cropped"] = True
    
    # Enhancement pipeline
    if enhance:
        image = denoise_image(image)
        image = enhance_contrast(image)
        image = sharpen_image(image)
    
    # Assess quality
    metadata["quality"] = assess_quality(image)
    metadata["processed_size"] = image.shape[:2]
    
    return image, metadata


def save_image(image: np.ndarray, output_path: str) -> bool:
    """
    Save processed image to file.
    
    Args:
        image: Image to save
        output_path: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_path, image)
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def image_to_bytes(image: np.ndarray, format: str = ".jpg") -> Optional[bytes]:
    """
    Convert image to bytes for API responses.
    
    Args:
        image: Input image
        format: Image format (.jpg, .png)
        
    Returns:
        Image bytes or None if failed
    """
    try:
        success, encoded = cv2.imencode(format, image)
        if success:
            return encoded.tobytes()
        return None
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

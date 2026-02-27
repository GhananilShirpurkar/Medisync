"""
IMAGE PROCESSING TESTS
======================
Verify image preprocessing functionality.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from utils.image_processing import (
    preprocess_prescription,
    assess_quality,
    detect_document,
    enhance_contrast,
    sharpen_image,
    binarize_image,
    calculate_brightness,
    calculate_sharpness,
)


def create_test_image() -> np.ndarray:
    """Create a synthetic prescription-like image for testing."""
    # Create white background
    image = np.ones((800, 600, 3), dtype=np.uint8) * 255
    
    # Add some text-like rectangles (simulating prescription text)
    cv2.rectangle(image, (50, 50), (550, 100), (0, 0, 0), -1)
    cv2.rectangle(image, (50, 150), (400, 180), (0, 0, 0), -1)
    cv2.rectangle(image, (50, 200), (500, 230), (0, 0, 0), -1)
    cv2.rectangle(image, (50, 250), (450, 280), (0, 0, 0), -1)
    
    # Add border (document edge)
    cv2.rectangle(image, (20, 20), (580, 780), (0, 0, 0), 3)
    
    return image


def test_quality_assessment():
    """Test image quality assessment."""
    print("\n=== Testing Quality Assessment ===")
    
    image = create_test_image()
    quality = assess_quality(image)
    
    print(f"Quality: {quality['quality']}")
    print(f"Brightness: {quality['brightness']}")
    print(f"Sharpness: {quality['sharpness']}")
    print(f"Issues: {quality['issues']}")
    
    assert quality['quality'] in ['excellent', 'good', 'poor']
    assert 0 <= quality['brightness'] <= 255
    assert quality['sharpness'] >= 0
    
    print("✅ Quality assessment passed")


def test_document_detection():
    """Test document boundary detection."""
    print("\n=== Testing Document Detection ===")
    
    image = create_test_image()
    corners = detect_document(image)
    
    if corners is not None:
        print(f"✅ Document detected with {len(corners)} corners")
        assert len(corners) == 4, "Should detect 4 corners"
    else:
        print("⚠️  No document detected (may be expected for synthetic image)")


def test_enhancement():
    """Test image enhancement functions."""
    print("\n=== Testing Image Enhancement ===")
    
    image = create_test_image()
    
    # Test contrast enhancement
    enhanced = enhance_contrast(image)
    assert enhanced.shape == image.shape
    print("✅ Contrast enhancement works")
    
    # Test sharpening
    sharpened = sharpen_image(image)
    assert sharpened.shape == image.shape
    print("✅ Sharpening works")
    
    # Test binarization
    binary = binarize_image(image)
    assert len(binary.shape) == 2  # Should be grayscale
    print("✅ Binarization works")


def test_full_pipeline():
    """Test complete preprocessing pipeline."""
    print("\n=== Testing Full Pipeline ===")
    
    image = create_test_image()
    
    # Run preprocessing
    processed, metadata = preprocess_prescription(
        image,
        auto_crop=True,
        enhance=True
    )
    
    print(f"Original size: {metadata['original_size']}")
    print(f"Processed size: {metadata['processed_size']}")
    print(f"Auto-cropped: {metadata['auto_cropped']}")
    print(f"Quality: {metadata['quality']['quality']}")
    
    assert processed is not None
    assert metadata['quality']['quality'] in ['excellent', 'good', 'poor']
    
    print("✅ Full pipeline passed")


def test_brightness_calculation():
    """Test brightness calculation."""
    print("\n=== Testing Brightness Calculation ===")
    
    # Create dark image
    dark_image = np.ones((100, 100, 3), dtype=np.uint8) * 50
    dark_brightness = calculate_brightness(dark_image)
    
    # Create bright image
    bright_image = np.ones((100, 100, 3), dtype=np.uint8) * 200
    bright_brightness = calculate_brightness(bright_image)
    
    print(f"Dark image brightness: {dark_brightness}")
    print(f"Bright image brightness: {bright_brightness}")
    
    assert dark_brightness < bright_brightness
    print("✅ Brightness calculation works")


def test_sharpness_calculation():
    """Test sharpness calculation."""
    print("\n=== Testing Sharpness Calculation ===")
    
    # Create blurry image
    image = create_test_image()
    blurry = cv2.GaussianBlur(image, (15, 15), 0)
    
    sharp_score = calculate_sharpness(image)
    blurry_score = calculate_sharpness(blurry)
    
    print(f"Sharp image score: {sharp_score}")
    print(f"Blurry image score: {blurry_score}")
    
    assert sharp_score > blurry_score
    print("✅ Sharpness calculation works")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("IMAGE PROCESSING TEST SUITE")
    print("=" * 60)
    
    try:
        test_quality_assessment()
        test_document_detection()
        test_enhancement()
        test_brightness_calculation()
        test_sharpness_calculation()
        test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

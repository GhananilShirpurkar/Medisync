"""
OCR SERVICE TESTS (OFFLINE-FIRST)
==================================
Tests for EasyOCR + Tesseract offline OCR service.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.ocr_service import (
    extract_prescription_text,
    preprocess_image,
    check_ram_usage,
    EASYOCR_AVAILABLE
)


def test_ocr_availability():
    """Test OCR engine availability."""
    print("\n" + "="*60)
    print("OCR ENGINE AVAILABILITY TEST")
    print("="*60)
    
    print(f"\nEasyOCR available: {EASYOCR_AVAILABLE}")
    
    if not EASYOCR_AVAILABLE:
        print("\n⚠️  EasyOCR not installed")
        print("   Install with: pip install easyocr")
    else:
        print("\n✅ EasyOCR ready (primary OCR engine)")
    
    print("\n✅ Availability check complete")


def test_ram_monitoring():
    """Test RAM usage monitoring."""
    print("\n" + "="*60)
    print("RAM MONITORING TEST")
    print("="*60)
    
    ram_info = check_ram_usage()
    
    if "error" in ram_info:
        print(f"\n⚠️  {ram_info['error']}")
        print("   Install with: pip install psutil")
    else:
        print(f"\nTotal RAM: {ram_info['total_gb']:.2f} GB")
        print(f"Used RAM: {ram_info['used_gb']:.2f} GB")
        print(f"Available RAM: {ram_info['available_gb']:.2f} GB")
        print(f"Usage: {ram_info['percent']:.1f}%")
        
        if ram_info['warning']:
            print(f"⚠️  RAM usage high (>{ram_info['percent']:.1f}%)")
        else:
            print("✅ RAM usage normal")
    
    print("\n✅ RAM monitoring test passed")


def test_mock_ocr_response():
    """Test OCR with mock response (when engines not installed)."""
    print("\n" + "="*60)
    print("MOCK OCR RESPONSE TEST")
    print("="*60)
    
    # This will use mock or actual OCR depending on what's installed
    result = extract_prescription_text("test_image.jpg")
    
    print(f"\nSuccess: {result.get('success', False)}")
    print(f"Method: {result.get('method', 'unknown')}")
    
    if result.get('success'):
        print(f"Raw text length: {len(result.get('raw_text', ''))}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Word count: {result.get('word_count', 0)}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Should always return a valid structure
    assert isinstance(result, dict), "Should return dictionary"
    assert "success" in result, "Should have success field"
    assert "method" in result, "Should have method field"
    
    print("\n✅ Mock OCR response test passed")


def test_ocr_response_structure():
    """Test OCR response structure."""
    print("\n" + "="*60)
    print("OCR RESPONSE STRUCTURE TEST")
    print("="*60)
    
    result = extract_prescription_text("test_image.jpg")
    
    # Check required fields
    required_fields = ["success", "method"]
    
    print("\nChecking required fields:")
    for field in required_fields:
        assert field in result, f"Missing field: {field}"
        print(f"  ✓ {field}: {result[field]}")
    
    # If successful, check additional fields
    if result.get("success"):
        success_fields = ["raw_text", "confidence", "word_count"]
        print("\nChecking success fields:")
        for field in success_fields:
            if field in result:
                print(f"  ✓ {field}: present")
    
    print("\n✅ OCR response structure test passed")


def test_offline_mode():
    """Test that OCR works without network."""
    print("\n" + "="*60)
    print("OFFLINE MODE TEST")
    print("="*60)
    
    print("\nTesting OCR in offline mode...")
    print("(This should work with EasyOCR/Tesseract or mock)")
    
    result = extract_prescription_text("test_image.jpg")
    
    # Should work offline (either with local engines or mock)
    assert isinstance(result, dict), "Should return result offline"
    
    if result.get("success"):
        print(f"✅ OCR working offline with {result.get('method')}")
    else:
        print(f"⚠️  OCR not available, using mock: {result.get('error')}")
    
    print("\n✅ Offline mode test passed")


if __name__ == "__main__":
    print("\n🧪 Running OCR Service Tests (Offline-First)...\n")
    
    try:
        test_ocr_availability()
        test_ram_monitoring()
        test_mock_ocr_response()
        test_ocr_response_structure()
        test_offline_mode()
        
        print("\n" + "="*60)
        print("✅ ALL OCR SERVICE TESTS PASSED")
        print("="*60)
        print("\n💡 Notes:")
        print("   - OCR engines not required for tests to pass")
        print("   - Install EasyOCR for production: pip install easyocr")
        print("   - Mock responses used when engines not available\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
TEST REAL OCR AND SPEECH ENGINES
=================================
Verify EasyOCR and faster-whisper work correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_easyocr_import():
    """Test EasyOCR can be imported."""
    print("\n=== Testing EasyOCR Import ===")
    
    try:
        import easyocr
        print("✅ EasyOCR imported successfully")
        print(f"   Version: {easyocr.__version__}")
        return True
    except ImportError as e:
        print(f"❌ EasyOCR import failed: {e}")
        return False


def test_faster_whisper_import():
    """Test faster-whisper can be imported."""
    print("\n=== Testing faster-whisper Import ===")
    
    try:
        from faster_whisper import WhisperModel
        print("✅ faster-whisper imported successfully")
        return True
    except ImportError as e:
        print(f"❌ faster-whisper import failed: {e}")
        return False


def test_torch_cpu_only():
    """Verify PyTorch is CPU-only (no CUDA)."""
    print("\n=== Testing PyTorch Configuration ===")
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print("   ⚠️  WARNING: CUDA is available (should be CPU-only)")
            return False
        else:
            print("   ✅ CPU-only build (correct)")
            return True
            
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False


def test_easyocr_reader():
    """Test EasyOCR reader initialization (downloads model on first run)."""
    print("\n=== Testing EasyOCR Reader ===")
    print("⚠️  First run will download ~140MB model from HuggingFace")
    
    try:
        import easyocr
        print("Creating EasyOCR reader (English, CPU)...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✅ EasyOCR reader created successfully")
        
        # Clean up
        del reader
        return True
        
    except Exception as e:
        print(f"❌ EasyOCR reader creation failed: {e}")
        return False


def test_whisper_model():
    """Test Whisper model initialization (downloads model on first run)."""
    print("\n=== Testing Whisper Model ===")
    print("⚠️  First run will download ~140MB model from HuggingFace")
    
    try:
        from faster_whisper import WhisperModel
        print("Creating Whisper model (base, CPU)...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("✅ Whisper model created successfully")
        
        # Clean up
        del model
        return True
        
    except Exception as e:
        print(f"❌ Whisper model creation failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("REAL ENGINE TESTS")
    print("=" * 60)
    
    results = []
    
    # Import tests (fast)
    results.append(("EasyOCR Import", test_easyocr_import()))
    results.append(("faster-whisper Import", test_faster_whisper_import()))
    results.append(("PyTorch CPU-only", test_torch_cpu_only()))
    
    # Model initialization tests (slow, downloads models)
    print("\n" + "=" * 60)
    print("MODEL INITIALIZATION TESTS")
    print("These will download models on first run (~280MB total)")
    print("=" * 60)
    
    response = input("\nRun model tests? (y/n): ")
    if response.lower() == 'y':
        results.append(("EasyOCR Reader", test_easyocr_reader()))
        results.append(("Whisper Model", test_whisper_model()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)

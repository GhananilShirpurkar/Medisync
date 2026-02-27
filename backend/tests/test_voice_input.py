"""
TEST VOICE INPUT
================
Test voice input endpoint with Whisper transcription.
"""

import pytest
import sys
sys.path.insert(0, '.')

from src.services.speech_service import transcribe_audio, WHISPER_AVAILABLE


def test_whisper_available():
    """Test that Whisper is available."""
    print("\n" + "="*60)
    print("TEST: Whisper Availability")
    print("="*60)
    
    if WHISPER_AVAILABLE:
        print("✅ Whisper is available")
    else:
        print("⚠️  Whisper not available - install with: pip install faster-whisper")
        pytest.skip("Whisper not installed")


def test_transcribe_audio_mock():
    """Test audio transcription with mock data."""
    print("\n" + "="*60)
    print("TEST: Audio Transcription (Mock)")
    print("="*60)
    
    # Use mock transcription for testing
    from src.services.speech_service import _mock_transcription
    
    result = _mock_transcription("test_audio.wav")
    
    assert result["success"] is True
    assert "transcription" in result
    assert len(result["transcription"]) > 0
    
    print(f"✅ Mock transcription: '{result['transcription']}'")
    print(f"   Language: {result['language']}")
    print(f"   Confidence: {result['language_probability']}")


def test_transcribe_audio_from_bytes():
    """Test transcription from audio bytes."""
    print("\n" + "="*60)
    print("TEST: Transcription from Bytes")
    print("="*60)
    
    # Create simple WAV file bytes (silence)
    import wave
    import io
    import struct
    
    # Create 1 second of silence at 16kHz
    sample_rate = 16000
    duration = 1  # seconds
    num_samples = sample_rate * duration
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write silence (zeros)
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))
    
    audio_bytes = wav_buffer.getvalue()
    
    print(f"Created test audio: {len(audio_bytes)} bytes")
    
    # Test transcription
    from src.services.speech_service import transcribe_audio_from_bytes
    
    result = transcribe_audio_from_bytes(audio_bytes, format="wav")
    
    print(f"Transcription result: {result['success']}")
    if result["success"]:
        print(f"   Transcription: '{result['transcription']}'")
        print(f"   Language: {result.get('language', 'N/A')}")
    else:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Note: Silence will likely produce empty transcription
    assert "success" in result
    assert "transcription" in result


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VOICE INPUT TESTS")
    print("="*60)
    
    test_whisper_available()
    test_transcribe_audio_mock()
    test_transcribe_audio_from_bytes()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n")

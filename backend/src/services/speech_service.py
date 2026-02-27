"""
SPEECH SERVICE - OFFLINE FIRST
===============================
faster-whisper (CPU inference)
Zero cloud billing | Sequential processing
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Check if faster-whisper is available
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️  faster-whisper not installed. Install with: pip install faster-whisper")


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")  # tiny | base | small
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")  # en | hi | auto


# ------------------------------------------------------------------
# AUDIO PREPROCESSING
# ------------------------------------------------------------------
def preprocess_audio(audio_path: str) -> str:
    """
    Preprocess audio for optimal transcription.
    
    Steps:
    1. Convert to 16kHz mono WAV
    2. Normalize volume
    3. Remove silence (optional)
    
    Args:
        audio_path: Path to input audio file
        
    Returns:
        Path to preprocessed audio file
    """
    try:
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
        except ImportError:
            print("⚠️  pydub not installed, skipping audio preprocessing")
            return audio_path

        # Load audio
        audio = AudioSegment.from_file(audio_path)
        
        # Convert to mono
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Convert to 16kHz (Whisper's native sample rate)
        if audio.frame_rate != 16000:
            audio = audio.set_frame_rate(16000)
        
        # Normalize volume
        audio = normalize(audio)
        
        # Save preprocessed audio
        output_path = "/tmp/preprocessed_audio.wav"
        audio.export(output_path, format="wav")
        
        return output_path
        
    except Exception as e:
        print(f"⚠️  Audio preprocessing failed: {e}, using original file")
        return audio_path


# ------------------------------------------------------------------
# SPEECH-TO-TEXT
# ------------------------------------------------------------------
def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe audio file to text using Whisper.
    
    RAM-SAFE PATTERN:
    - Model loaded inside function
    - Model deleted after use
    - Never keep model resident
    
    Args:
        audio_path: Path to audio file (WAV, MP3, etc.)
        language: Language code (en, hi, etc.) or None for auto-detection
        
    Returns:
        Dictionary with transcription and metadata
        
    Example:
        {
            "success": True,
            "transcription": "I need paracetamol and cough syrup",
            "language": "en",
            "language_probability": 0.98,
            "duration": 3.5,
            "method": "faster-whisper-base"
        }
    """
    if not WHISPER_AVAILABLE:
        return {
            "success": False,
            "error": "faster-whisper not installed",
            "transcription": ""
        }
    
    try:
        # RAM-SAFE: Load model inside function
        print(f"🎤 Loading Whisper {WHISPER_MODEL_SIZE} model (this may take 3-5 seconds)...")
        model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8"  # Quantized for faster CPU inference
        )
        print("✅ Whisper model loaded successfully")
        
        # Preprocess audio (optional, can be skipped for speed)
        # preprocessed_path = preprocess_audio(audio_path)
        preprocessed_path = audio_path  # Skip preprocessing for now
        
        # Determine language
        lang = language or WHISPER_LANGUAGE
        if lang == "auto":
            lang = None  # Let Whisper detect automatically
        
        # Transcribe
        segments, info = model.transcribe(
            preprocessed_path,
            beam_size=5,
            language=lang,
            vad_filter=True,  # Voice activity detection (removes silence)
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Combine segments
        full_text = []
        for segment in segments:
            full_text.append(segment.text)
        
        transcription = ' '.join(full_text).strip()
        
        result = {
            "success": True,
            "transcription": transcription,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "method": f"faster-whisper-{WHISPER_MODEL_SIZE}"
        }
        
        # RAM-SAFE: Delete model and force garbage collection
        del model
        import gc
        gc.collect()
        print("🗑️  Whisper model unloaded from memory")
        
        return result
        
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "transcription": ""
        }


def transcribe_audio_from_bytes(audio_bytes: bytes, format: str = "wav") -> Dict[str, Any]:
    """
    Transcribe audio from bytes (for API uploads).
    
    Args:
        audio_bytes: Raw audio bytes
        format: Audio format (wav, mp3, etc.)
        
    Returns:
        Dictionary with transcription and metadata
    """
    import tempfile
    
    try:
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Transcribe
        result = transcribe_audio(tmp_path)
        
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing audio bytes: {e}")
        return {
            "success": False,
            "error": str(e),
            "transcription": ""
        }


# ------------------------------------------------------------------
# MOCK RESPONSE (for testing without model)
# ------------------------------------------------------------------
def _mock_transcription(audio_path: str) -> Dict[str, Any]:
    """
    Return mock transcription for testing.
    
    Args:
        audio_path: Path to audio file (for logging)
        
    Returns:
        Mock transcription data
    """
    print(f"🎤 Using mock transcription for: {audio_path}")
    
    return {
        "success": True,
        "transcription": "I need paracetamol 500mg and cough syrup",
        "language": "en",
        "language_probability": 0.95,
        "duration": 3.5,
        "method": "mock",
        "note": "Mock response - Whisper model not loaded"
    }

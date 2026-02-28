"""
SPEECH SERVICE - OFFLINE FIRST
===============================
faster-whisper (CPU inference)
Zero cloud billing | Sequential processing
"""

import os
import threading
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
logger = logging.getLogger(__name__)

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
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")  # tiny | base | small | medium
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")     # en | hi | auto

# Domain-specific prompt for pharmacy context (reduces hallucination)
WHISPER_PROMPT = (
    "This is a pharmacy consultation. The patient is describing symptoms "
    "like headache, fever, cold, cough, body pain, stomach ache, or "
    "requesting medicines like paracetamol, ibuprofen, aspirin, cough syrup. "
    "They may state their age, allergies, or how long they have had symptoms."
)


# ------------------------------------------------------------------
# RESIDENT MODEL SINGLETON
# ------------------------------------------------------------------
_whisper_model = None
_whisper_lock = threading.Lock()

def _get_whisper_model():
    """Load Whisper model once and keep it resident for fast inference."""
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                if not WHISPER_AVAILABLE:
                    return None
                print(f"🎤 Loading Whisper '{WHISPER_MODEL_SIZE}' model (one-time, stays resident)...")
                _whisper_model = WhisperModel(
                    WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="int8"  # Quantized for faster CPU inference
                )
                print(f"✅ Whisper '{WHISPER_MODEL_SIZE}' model loaded and resident in memory")
    return _whisper_model


# ------------------------------------------------------------------
# AUDIO PREPROCESSING
# ------------------------------------------------------------------
def preprocess_audio(audio_path: str) -> str:
    """
    Preprocess audio for optimal transcription.
    Convert to 16kHz mono WAV + normalize volume.
    """
    try:
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
        except ImportError:
            print("⚠️  pydub not installed, skipping audio preprocessing")
            return audio_path

        audio = AudioSegment.from_file(audio_path)
        
        if audio.channels > 1:
            audio = audio.set_channels(1)
        if audio.frame_rate != 16000:
            audio = audio.set_frame_rate(16000)
        
        audio = normalize(audio)
        
        output_path = "/tmp/preprocessed_audio.wav"
        audio.export(output_path, format="wav")
        return output_path
        
    except Exception as e:
        print(f"⚠️  Audio preprocessing failed: {e}, using original file")
        return audio_path


# ------------------------------------------------------------------
# SPEECH-TO-TEXT (fast — model stays resident)
# ------------------------------------------------------------------
def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe audio file to text using resident Whisper model.
    First call loads the model (~5s). Subsequent calls are instant.
    """
    model = _get_whisper_model()
    if model is None:
        return {
            "success": False,
            "error": "faster-whisper not installed",
            "transcription": ""
        }
    
    try:
        # Preprocess audio for better quality
        preprocessed_path = preprocess_audio(audio_path)
        
        # Determine language
        lang = language or WHISPER_LANGUAGE
        if lang == "auto":
            lang = None
        
        # Transcribe with domain prompt
        segments, info = model.transcribe(
            preprocessed_path,
            beam_size=5,
            language=lang,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt=WHISPER_PROMPT
        )
        
        full_text = [segment.text for segment in segments]
        transcription = ' '.join(full_text).strip()
        
        return {
            "success": True,
            "transcription": transcription,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "method": f"faster-whisper-{WHISPER_MODEL_SIZE}"
        }
        
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

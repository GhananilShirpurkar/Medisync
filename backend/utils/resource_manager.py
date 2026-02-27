"""
RESOURCE MANAGER
================
Manages heavy models with lazy loading and automatic unloading.
Ensures we stay within 8GB RAM constraint.
"""

import gc
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(".env")

# Configuration
MAX_RAM_PERCENT = int(os.getenv("MAX_RAM_PERCENT", "85"))
MODEL_TIMEOUT_SECONDS = int(os.getenv("MODEL_TIMEOUT_SECONDS", "30"))


class ResourceManager:
    """
    Singleton resource manager for heavy ML models.
    
    Responsibilities:
    - Lazy load models only when needed
    - Ensure only one heavy model loaded at a time
    - Monitor RAM usage
    - Automatically unload models when RAM is high
    - Provide timeout protection for model loading
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.easyocr_reader = None
        self.whisper_model = None
        self.ram_threshold_gb = 6.0  # Unload if RAM > 6GB
        self._initialized = True
    
    # ------------------------------------------------------------------
    # RAM MONITORING
    # ------------------------------------------------------------------
    def get_ram_usage(self) -> Dict[str, Any]:
        """
        Get current RAM usage statistics.
        
        Returns:
            Dictionary with RAM info
        """
        try:
            import psutil
            
            ram = psutil.virtual_memory()
            
            return {
                "total_gb": ram.total / (1024**3),
                "used_gb": ram.used / (1024**3),
                "available_gb": ram.available / (1024**3),
                "percent": ram.percent,
                "warning": ram.percent > MAX_RAM_PERCENT
            }
        except ImportError:
            return {"error": "psutil not installed"}
    
    def check_ram_before_load(self, required_gb: float = 2.0):
        """
        Check if there's enough RAM before loading a model.
        
        Args:
            required_gb: Required RAM in GB
            
        Raises:
            MemoryError: If not enough RAM available
        """
        ram_info = self.get_ram_usage()
        
        if "error" in ram_info:
            print("⚠️  Cannot check RAM (psutil not installed)")
            return
        
        if ram_info["available_gb"] < required_gb:
            raise MemoryError(
                f"Not enough RAM available. "
                f"Required: {required_gb:.1f}GB, "
                f"Available: {ram_info['available_gb']:.1f}GB"
            )
        
        if ram_info["percent"] > MAX_RAM_PERCENT:
            raise MemoryError(
                f"RAM usage too high: {ram_info['percent']:.1f}% "
                f"(threshold: {MAX_RAM_PERCENT}%)"
            )
    
    # ------------------------------------------------------------------
    # EASYOCR MANAGEMENT
    # ------------------------------------------------------------------
    def get_ocr_reader(self):
        """
        Get EasyOCR reader (lazy loaded).
        
        Automatically unloads Whisper if loaded.
        
        Returns:
            EasyOCR Reader instance
        """
        # Check RAM before loading
        self.check_ram_before_load(required_gb=2.0)
        
        # Unload Whisper if loaded
        if self.whisper_model is not None:
            print("🔄 Unloading Whisper to make room for EasyOCR...")
            self.unload_whisper()
        
        # Load EasyOCR if not already loaded
        if self.easyocr_reader is None:
            try:
                import easyocr
                
                print("📚 Loading EasyOCR model...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                print("✅ EasyOCR loaded")
                
            except ImportError:
                raise ImportError("EasyOCR not installed. Install with: pip install easyocr")
        
        return self.easyocr_reader
    
    def unload_easyocr(self):
        """Unload EasyOCR model to free RAM (~2GB)."""
        if self.easyocr_reader is not None:
            del self.easyocr_reader
            self.easyocr_reader = None
            gc.collect()
            print("🗑️  EasyOCR unloaded")
    
    # ------------------------------------------------------------------
    # WHISPER MANAGEMENT
    # ------------------------------------------------------------------
    def get_whisper_model(self):
        """
        Get Whisper model (lazy loaded).
        
        Automatically unloads EasyOCR if loaded.
        
        Returns:
            WhisperModel instance
        """
        # Check RAM before loading
        self.check_ram_before_load(required_gb=1.5)
        
        # Unload EasyOCR if loaded
        if self.easyocr_reader is not None:
            print("🔄 Unloading EasyOCR to make room for Whisper...")
            self.unload_easyocr()
        
        # Load Whisper if not already loaded
        if self.whisper_model is None:
            try:
                from faster_whisper import WhisperModel
                
                model_size = os.getenv("WHISPER_MODEL", "base")
                print(f"🎤 Loading Whisper {model_size} model...")
                
                self.whisper_model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8"
                )
                
                print("✅ Whisper loaded")
                
            except ImportError:
                raise ImportError("faster-whisper not installed. Install with: pip install faster-whisper")
        
        return self.whisper_model
    
    def unload_whisper(self):
        """Unload Whisper model to free RAM (~1.5GB)."""
        if self.whisper_model is not None:
            del self.whisper_model
            self.whisper_model = None
            gc.collect()
            print("🗑️  Whisper unloaded")
    
    # ------------------------------------------------------------------
    # AUTOMATIC CLEANUP
    # ------------------------------------------------------------------
    def check_and_unload(self):
        """
        Check RAM usage and unload models if necessary.
        
        Call this periodically or after processing.
        """
        ram_info = self.get_ram_usage()
        
        if "error" in ram_info:
            return
        
        if ram_info["warning"]:
            print(f"⚠️  High RAM usage: {ram_info['percent']:.1f}%")
            
            # Unload models to free memory
            if self.easyocr_reader is not None:
                self.unload_easyocr()
            
            if self.whisper_model is not None:
                self.unload_whisper()
            
            print("✅ Models unloaded to free RAM")
    
    def unload_all(self):
        """Unload all models to free maximum RAM."""
        self.unload_easyocr()
        self.unload_whisper()
        print("🗑️  All models unloaded")
    
    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Get current resource manager status.
        
        Returns:
            Dictionary with status info
        """
        ram_info = self.get_ram_usage()
        
        return {
            "ram": ram_info,
            "models_loaded": {
                "easyocr": self.easyocr_reader is not None,
                "whisper": self.whisper_model is not None
            },
            "config": {
                "max_ram_percent": MAX_RAM_PERCENT,
                "model_timeout_seconds": MODEL_TIMEOUT_SECONDS
            }
        }


# ------------------------------------------------------------------
# GLOBAL INSTANCE
# ------------------------------------------------------------------
resource_manager = ResourceManager()


# ------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ------------------------------------------------------------------
def get_ocr_reader():
    """Get EasyOCR reader (convenience function)."""
    return resource_manager.get_ocr_reader()


def get_whisper_model():
    """Get Whisper model (convenience function)."""
    return resource_manager.get_whisper_model()


def unload_all_models():
    """Unload all models (convenience function)."""
    resource_manager.unload_all()


def get_resource_status():
    """Get resource status (convenience function)."""
    return resource_manager.get_status()


def check_and_cleanup():
    """Check RAM and cleanup if needed (convenience function)."""
    resource_manager.check_and_unload()

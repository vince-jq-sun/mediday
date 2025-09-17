#!/usr/bin/env python3
"""
Simple test to verify OpenAI STT is working as default
"""
import sys
from pathlib import Path

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

def test_pipeline_stt():
    """Test pipeline STT configuration"""
    from audio_pipeline.pipeline import AudioProcessingPipeline
    from audio_pipeline.config import STT_PROVIDER
    
    print("🧪 Testing OpenAI STT Configuration")
    print("=" * 40)
    
    # Test config
    print(f"Config STT_PROVIDER: {STT_PROVIDER}")
    
    # Test pipeline initialization
    pipeline = AudioProcessingPipeline()
    print(f"Pipeline STT provider: {pipeline.stt_provider}")
    
    # Test speech recognizer
    print(f"SpeechRecognizer provider: {pipeline.speech_recognizer.provider}")
    
    if pipeline.stt_provider == "openai" and pipeline.speech_recognizer.provider == "openai":
        print("\n✅ OpenAI is correctly set as default STT provider!")
        return True
    else:
        print("\n❌ OpenAI is not set as default STT provider")
        return False

if __name__ == "__main__":
    success = test_pipeline_stt()
    sys.exit(0 if success else 1)

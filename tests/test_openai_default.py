#!/usr/bin/env python3
"""
Test script to verify OpenAI is used as default STT provider
"""
import sys
from pathlib import Path

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from audio_pipeline.config import STT_PROVIDER
from audio_pipeline.speech_recognition import SpeechRecognizer
from audio_pipeline.pipeline import AudioProcessingPipeline

def test_config_default():
    """Test that config has OpenAI as default"""
    print(f"✓ Config STT_PROVIDER: {STT_PROVIDER}")
    assert STT_PROVIDER == "openai", f"Expected 'openai', got '{STT_PROVIDER}'"

def test_speech_recognizer_default():
    """Test that SpeechRecognizer defaults to OpenAI"""
    recognizer = SpeechRecognizer()
    print(f"✓ SpeechRecognizer default provider: {recognizer.provider}")
    assert recognizer.provider == "openai", f"Expected 'openai', got '{recognizer.provider}'"

def test_pipeline_default():
    """Test that AudioProcessingPipeline uses OpenAI by default"""
    pipeline = AudioProcessingPipeline()
    print(f"✓ Pipeline STT provider: {pipeline.stt_provider}")
    assert pipeline.stt_provider == "openai", f"Expected 'openai', got '{pipeline.stt_provider}'"

def main():
    """Run all tests"""
    print("🧪 Testing OpenAI as default STT provider...")
    print("=" * 50)
    
    try:
        test_config_default()
        test_speech_recognizer_default()
        test_pipeline_default()
        
        print("\n✅ All tests passed! OpenAI is now the default STT provider.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

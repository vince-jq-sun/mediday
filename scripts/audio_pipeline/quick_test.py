#!/usr/bin/env python3
"""
Quick test script to verify the pipeline components
"""
import sys
from pathlib import Path
import tempfile
import json

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_audio_preprocessing():
    """Test audio preprocessing with a sample file"""
    print("🧪 Testing Audio Preprocessing...")
    
    from audio_pipeline.audio_preprocessor import AudioPreprocessor
    from audio_pipeline.config import AWAKE_WHERE_YOU_ARE_DIR
    
    preprocessor = AudioPreprocessor(silence_threshold_seconds=2.0)  # Lower threshold for testing
    
    # Find first audio file
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
    audio_file = None
    
    for file_path in AWAKE_WHERE_YOU_ARE_DIR.iterdir():
        if file_path.suffix.lower() in audio_extensions:
            audio_file = file_path
            break
    
    if not audio_file:
        print("❌ No audio files found for testing")
        return False
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata = preprocessor.segment_audio(audio_file, temp_path)
            
            print(f"✅ Processed: {audio_file.name}")
            print(f"   Total duration: {metadata['total_duration']:.1f}s")
            print(f"   Segments created: {metadata['total_segments']}")
            print(f"   Silence segments: {len(metadata['silence_segments'])}")
            
            return True
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}")
        return False

def test_speech_recognition():
    """Test speech recognition with Google API"""
    print("\n🧪 Testing Speech Recognition...")
    
    try:
        from audio_pipeline.speech_recognition import SpeechRecognizer
        
        recognizer = SpeechRecognizer()
        print("✅ Speech recognizer initialized")
        
        # Test with a very short audio file if available
        # For now, just test initialization
        return True
    except Exception as e:
        print(f"❌ Speech recognition test failed: {e}")
        return False

def test_translation():
    """Test translation with Google API"""
    print("\n🧪 Testing Translation...")
    
    try:
        from audio_pipeline.translator import Translator
        from audio_pipeline.config import AUDIO_PIPELINE_DIR
        
        terminology_file = AUDIO_PIPELINE_DIR / "terminology.json"
        translator = Translator(terminology_file)
        
        # Test translation
        test_text = "This is a test of mindfulness meditation practice."
        result = translator.translate_text(test_text)
        
        if result.get('translated_text'):
            print(f"✅ Translation successful")
            print(f"   EN: {test_text}")
            print(f"   ZH: {result['translated_text']}")
            return True
        else:
            print(f"❌ Translation failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_text_to_speech():
    """Test text-to-speech with Google API"""
    print("\n🧪 Testing Text-to-Speech...")
    
    try:
        from audio_pipeline.text_to_speech import TextToSpeechSynthesizer
        
        tts = TextToSpeechSynthesizer()
        
        # Test getting available voices
        voices = tts.get_available_voices("zh-CN")
        
        if voices:
            print(f"✅ Text-to-Speech API connected")
            print(f"   Available Chinese voices: {len(voices)}")
            for voice in voices[:3]:  # Show first 3
                print(f"   - {voice['name']} ({voice['ssml_gender']})")
            return True
        else:
            print("❌ No voices available")
            return False
    except Exception as e:
        print(f"❌ Text-to-Speech test failed: {e}")
        return False

def test_gui_imports():
    """Test GUI imports"""
    print("\n🧪 Testing GUI Dependencies...")
    
    try:
        import tkinter as tk
        print("✅ tkinter available")
        
        import pygame
        print("✅ pygame available")
        
        import pyaudio
        print("✅ pyaudio available")
        
        return True
    except ImportError as e:
        print(f"❌ GUI dependency missing: {e}")
        return False

def main():
    """Run all tests"""
    print("🔬 Quick Pipeline Test Suite")
    print("=" * 40)
    
    tests = [
        ("Audio Preprocessing", test_audio_preprocessing),
        ("Speech Recognition", test_speech_recognition),
        ("Translation", test_translation),
        ("Text-to-Speech", test_text_to_speech),
        ("GUI Dependencies", test_gui_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Pipeline is ready to use.")
    else:
        print("⚠️  Some tests failed. Check your setup and API credentials.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()

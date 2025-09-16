#!/usr/bin/env python3
"""
Quick test script to check Google Cloud API accessibility
"""
import os
from pathlib import Path

def test_credentials():
    """Test if Google Cloud credentials are accessible"""
    print("=== Google Cloud Credentials Test ===")
    
    # Check environment variables
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
    print(f"GOOGLE_CLOUD_PROJECT_ID: {project_id}")
    
    if creds_path:
        creds_file = Path(creds_path)
        if creds_file.exists():
            print(f"✓ Credentials file exists: {creds_file}")
        else:
            print(f"✗ Credentials file not found: {creds_file}")
    else:
        print("✗ GOOGLE_APPLICATION_CREDENTIALS not set")
    
    return creds_path and project_id

def test_speech_to_text():
    """Test Speech-to-Text API"""
    print("\n=== Speech-to-Text API Test ===")
    try:
        from google.cloud import speech
        client = speech.SpeechClient()
        print("✓ Speech-to-Text client created successfully")
        return True
    except Exception as e:
        print(f"✗ Speech-to-Text API error: {e}")
        return False

def test_translation():
    """Test Translation API"""
    print("\n=== Translation API Test ===")
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        
        # Simple test
        result = client.translate("Hello", target_language='zh-CN')
        print(f"✓ Translation API working: 'Hello' -> '{result['translatedText']}'")
        return True
    except Exception as e:
        print(f"✗ Translation API error: {e}")
        return False

def test_text_to_speech():
    """Test Text-to-Speech API"""
    print("\n=== Text-to-Speech API Test ===")
    try:
        from google.cloud import texttospeech
        client = texttospeech.TextToSpeechClient()
        print("✓ Text-to-Speech client created successfully")
        return True
    except Exception as e:
        print(f"✗ Text-to-Speech API error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Google Cloud API setup...\n")
    
    # Load environment variables from .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        print("Loading environment variables from .env file...")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print()
    
    creds_ok = test_credentials()
    
    if creds_ok:
        stt_ok = test_speech_to_text()
        translate_ok = test_translation()
        tts_ok = test_text_to_speech()
        
        if all([stt_ok, translate_ok, tts_ok]):
            print("\n🎉 All APIs are working! You can run the full pipeline.")
        else:
            print("\n⚠️  Some APIs have issues. Check the errors above.")
    else:
        print("\n❌ Google Cloud credentials not properly configured.")
        print("Please check your .env file and service account key.")

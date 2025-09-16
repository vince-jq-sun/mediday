#!/usr/bin/env python3
"""
Environment setup script for the audio processing pipeline
"""
import os
import sys
from pathlib import Path
import subprocess
import json

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_virtual_environment():
    """Check if running in virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        env_name = os.path.basename(sys.prefix)
        print(f"✅ Virtual environment: {env_name}")
        return True
    else:
        print("⚠️  Not running in virtual environment")
        print("   Recommended: conda activate mediday")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def check_google_cloud_setup():
    """Check Google Cloud setup"""
    print("\n☁️  Checking Google Cloud setup...")
    
    # Check environment variables
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Please copy .env.example to .env and configure it")
        return False
    
    # Load environment variables
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set in .env")
        return False
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT_ID not set in .env")
        return False
    
    credentials_file = Path(credentials_path)
    if not credentials_file.exists():
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    print(f"✅ Credentials file: {credentials_path}")
    print(f"✅ Project ID: {project_id}")
    
    return True

def test_google_apis():
    """Test Google Cloud APIs"""
    print("\n🧪 Testing Google Cloud APIs...")
    
    # Test Speech-to-Text
    try:
        from google.cloud import speech
        client = speech.SpeechClient()
        print("✅ Speech-to-Text API connection successful")
    except Exception as e:
        print(f"❌ Speech-to-Text API error: {e}")
        return False
    
    # Test Translation
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        print("✅ Translation API connection successful")
    except Exception as e:
        print(f"❌ Translation API error: {e}")
        return False
    
    # Test Text-to-Speech
    try:
        from google.cloud import texttospeech
        client = texttospeech.TextToSpeechClient()
        print("✅ Text-to-Speech API connection successful")
    except Exception as e:
        print(f"❌ Text-to-Speech API error: {e}")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    from audio_pipeline.config import ensure_directories
    ensure_directories()
    print("✅ Directories created")

def check_audio_files():
    """Check for audio files to process"""
    print("\n🎵 Checking for audio files...")
    
    from audio_pipeline.config import AWAKE_WHERE_YOU_ARE_DIR
    
    if not AWAKE_WHERE_YOU_ARE_DIR.exists():
        print(f"❌ Audio directory not found: {AWAKE_WHERE_YOU_ARE_DIR}")
        return False
    
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
    audio_files = []
    
    for file_path in AWAKE_WHERE_YOU_ARE_DIR.iterdir():
        if file_path.suffix.lower() in audio_extensions:
            audio_files.append(file_path)
    
    if not audio_files:
        print(f"⚠️  No audio files found in {AWAKE_WHERE_YOU_ARE_DIR}")
        return False
    
    print(f"✅ Found {len(audio_files)} audio files:")
    for audio_file in audio_files[:5]:  # Show first 5
        print(f"   - {audio_file.name}")
    if len(audio_files) > 5:
        print(f"   ... and {len(audio_files) - 5} more")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Audio Processing Pipeline Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check virtual environment
    check_virtual_environment()
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Check Google Cloud setup
    if not check_google_cloud_setup():
        success = False
        print("\n📋 Next steps for Google Cloud setup:")
        print("1. Copy .env.example to .env")
        print("2. Follow the API_TESTING_GUIDE.md for detailed setup")
        print("3. Set GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT_ID")
    else:
        # Test APIs if setup is complete
        if not test_google_apis():
            success = False
    
    # Create directories
    try:
        create_directories()
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        success = False
    
    # Check audio files
    check_audio_files()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python -m audio_pipeline.pipeline full")
        print("2. Or follow the step-by-step guide in API_TESTING_GUIDE.md")
    else:
        print("⚠️  Setup completed with warnings")
        print("Please address the issues above before running the pipeline")
    
    return success

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Alternative dependency installation script for Python 3.12 compatibility
"""
import subprocess
import sys
from pathlib import Path

def install_package(package, upgrade=False):
    """Install a single package with error handling"""
    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(package)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package}: {e.stderr.strip()}")
        return False

def install_dependencies():
    """Install dependencies one by one for better error handling"""
    print("📦 Installing dependencies for Python 3.12...")
    
    # Core packages first
    core_packages = [
        "setuptools>=68.0.0",
        "wheel>=0.40.0",
        "pip>=23.0.0"
    ]
    
    print("\n🔧 Installing core packages...")
    for package in core_packages:
        install_package(package, upgrade=True)
    
    # Main dependencies
    main_packages = [
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "soundfile>=0.12.1",
        "librosa>=0.10.1",
        "pydub>=0.25.1",
        "pygame>=2.5.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "resampy>=0.4.0"
    ]
    
    print("\n🎵 Installing audio processing packages...")
    success_count = 0
    for package in main_packages:
        if install_package(package):
            success_count += 1
    
    # Google Cloud packages
    google_packages = [
        "google-cloud-speech>=2.21.0",
        "google-cloud-translate>=3.12.0", 
        "google-cloud-texttospeech>=2.16.3"
    ]
    
    print("\n☁️ Installing Google Cloud packages...")
    for package in google_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Installed {success_count}/{len(main_packages) + len(google_packages)} main packages")
    
    # PyAudio (optional, may need system dependencies)
    print("\n🎤 Installing PyAudio (optional for recording)...")
    if not install_package("pyaudio"):
        print("⚠️  PyAudio installation failed. You can install it manually later:")
        print("   macOS: brew install portaudio && pip install pyaudio")
        print("   This is only needed for manual recording functionality.")
    
    return success_count

def main():
    """Main installation function"""
    print("🚀 Alternative Dependency Installation")
    print("=" * 40)
    
    success_count = install_dependencies()
    
    print("\n" + "=" * 40)
    if success_count >= 10:  # Most important packages
        print("🎉 Core dependencies installed successfully!")
        print("You can now proceed with the pipeline setup.")
    else:
        print("⚠️  Some dependencies failed to install.")
        print("The pipeline may still work for basic functionality.")
    
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure Google Cloud credentials")
    print("2. Run: python scripts/audio_pipeline/quick_test.py")

if __name__ == "__main__":
    main()

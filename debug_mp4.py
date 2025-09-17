#!/usr/bin/env python3
"""
Debug script to test MP4 processing
"""
import sys
sys.path.append('/Users/vince/Documents/mediday')

from pathlib import Path
from scripts.audio_pipeline.audio_preprocessor import AudioPreprocessor

def test_mp4_processing():
    """Test MP4 file processing"""
    audio_file = Path("data/awake_where_you_are_english/1-2_foundational_meditation.mp3")
    output_dir = Path("temp/debug_test")
    
    print(f"Testing MP4 processing for: {audio_file}")
    print(f"Output directory: {output_dir}")
    
    try:
        preprocessor = AudioPreprocessor(silence_threshold_seconds=3.0)
        
        # Test MP4 detection
        is_mp4 = preprocessor._is_mp4_format(audio_file)
        print(f"Is MP4 format: {is_mp4}")
        
        if is_mp4:
            print("Converting MP4 to WAV...")
            temp_wav = preprocessor._convert_mp4_to_wav(audio_file)
            print(f"Temporary WAV created: {temp_wav}")
            print(f"Temp WAV exists: {temp_wav.exists()}")
            print(f"Temp WAV size: {temp_wav.stat().st_size / 1024 / 1024:.1f} MB")
            
            # Test loading with soundfile first
            import soundfile as sf
            print("Loading with soundfile...")
            y, sr = sf.read(str(temp_wav))
            print(f"Audio loaded with soundfile: {len(y)} samples, {sr} Hz, {len(y)/sr:.1f}s")
            
            # Test loading with librosa
            import librosa
            print("Loading with librosa...")
            y2, sr2 = librosa.load(str(temp_wav), sr=None)
            print(f"Audio loaded with librosa: {len(y2)} samples, {sr2} Hz, {len(y2)/sr2:.1f}s")
            
            # Clean up
            temp_wav.unlink()
            temp_wav.parent.rmdir()
            print("Temporary files cleaned up")
        
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mp4_processing()

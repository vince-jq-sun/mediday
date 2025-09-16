#!/usr/bin/env python3
"""
Simple audio slicing tool for creating test samples
"""
import librosa
import soundfile as sf
from pathlib import Path
import argparse
import subprocess
import tempfile
import os

def slice_audio(input_file: Path, output_file: Path, start_time: float, duration: float):
    """
    Cut a slice from an audio file
    
    Args:
        input_file: Path to input audio file
        output_file: Path to output audio file
        start_time: Start time in seconds
        duration: Duration in seconds
    """
    try:
        # Convert Path to string for librosa compatibility
        input_path_str = str(input_file)
        output_path_str = str(output_file)
        
        print(f"🔄 Loading audio from: {Path(input_path_str).name}")
        
        # Check if file is MP4/M4A and use ffmpeg directly for slicing
        file_ext = Path(input_path_str).suffix.lower()
        file_info = subprocess.run(['file', input_path_str], capture_output=True, text=True).stdout
        
        if file_ext in ['.mp4', '.m4a'] or 'ISO Media' in file_info:
            print(f"🔧 Detected MP4/M4A format, using ffmpeg for direct slicing...")
            
            # Get duration first
            duration_cmd = [
                '/opt/homebrew/Caskroom/miniforge/base/bin/ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', input_path_str
            ]
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            total_duration = float(result.stdout.strip())
            
            print(f"📁 Input file: {Path(input_path_str).name}")
            print(f"⏱️  Total duration: {total_duration:.1f}s")
            print(f"✂️  Slicing: {start_time:.1f}s to {start_time + duration:.1f}s")
            
            # Validate bounds
            if start_time >= total_duration:
                raise ValueError(f"Start time {start_time}s exceeds audio duration {total_duration:.1f}s")
            
            actual_duration = min(duration, total_duration - start_time)
            
            # Create output directory
            Path(output_path_str).parent.mkdir(parents=True, exist_ok=True)
            
            # Choose codec based on output file extension
            output_ext = Path(output_path_str).suffix.lower()
            if output_ext == '.mp3':
                # MP3 encoding
                slice_cmd = [
                    '/opt/homebrew/Caskroom/miniforge/base/bin/ffmpeg', '-i', input_path_str,
                    '-ss', str(start_time), '-t', str(actual_duration),
                    '-vn', '-acodec', 'libmp3lame', '-b:a', '192k', '-ar', '44100', '-ac', '2',
                    '-y', output_path_str
                ]
            elif output_ext == '.wav':
                # WAV encoding
                slice_cmd = [
                    '/opt/homebrew/Caskroom/miniforge/base/bin/ffmpeg', '-i', input_path_str,
                    '-ss', str(start_time), '-t', str(actual_duration),
                    '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                    '-y', output_path_str
                ]
            else:
                # Default to WAV for other formats
                slice_cmd = [
                    '/opt/homebrew/Caskroom/miniforge/base/bin/ffmpeg', '-i', input_path_str,
                    '-ss', str(start_time), '-t', str(actual_duration),
                    '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                    '-y', output_path_str
                ]
            
            subprocess.run(slice_cmd, check=True, capture_output=True)
            
            print(f"✅ Saved slice: {output_path_str}")
            print(f"📊 Slice duration: {actual_duration:.1f}s")
            
            if Path(output_path_str).exists():
                file_size = Path(output_path_str).stat().st_size / 1024
                print(f"💾 File size: {file_size:.1f} KB")
                return True
            else:
                return False
            
        else:
            # Use librosa for standard audio formats
            y, sr = librosa.load(input_path_str, sr=None)
            total_duration = len(y) / sr
            
            if len(y) == 0:
                raise ValueError("Audio file appears to be empty or corrupted")
        
        print(f"📁 Input file: {Path(input_path_str).name}")
        print(f"⏱️  Total duration: {total_duration:.1f}s")
        print(f"✂️  Slicing: {start_time:.1f}s to {start_time + duration:.1f}s")
        
        # Calculate sample indices
        start_sample = int(start_time * sr)
        end_sample = int((start_time + duration) * sr)
        
        # Validate bounds
        if start_sample >= len(y):
            raise ValueError(f"Start time {start_time}s exceeds audio duration {total_duration:.1f}s")
        
        if end_sample > len(y):
            print(f"⚠️  End time exceeds audio duration, truncating to {total_duration:.1f}s")
            end_sample = len(y)
        
        # Extract slice
        audio_slice = y[start_sample:end_sample]
        actual_duration = len(audio_slice) / sr
        
        # Save slice
        output_file.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path_str, audio_slice, sr)
        
        print(f"✅ Saved slice: {output_file}")
        print(f"📊 Slice duration: {actual_duration:.1f}s")
        print(f"💾 File size: {output_file.stat().st_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error slicing audio: {e}")
        return False

def auto_slice_for_testing(input_file: Path, output_dir: Path, slice_duration: float = 30.0):
    """
    Automatically create test slices from an audio file
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory to save slices
        slice_duration: Duration of each slice in seconds
    """
    try:
        # Load audio to get duration
        y, sr = librosa.load(input_file, sr=None)
        total_duration = len(y) / sr
        
        print(f"📁 Processing: {input_file.name}")
        print(f"⏱️  Total duration: {total_duration:.1f}s")
        
        # Create slices
        output_dir.mkdir(parents=True, exist_ok=True)
        num_slices = max(1, int(total_duration // slice_duration))
        
        for i in range(num_slices):
            start_time = i * slice_duration
            actual_duration = min(slice_duration, total_duration - start_time)
            
            if actual_duration < 5.0:  # Skip very short slices
                break
            
            output_file = output_dir / f"{input_file.stem}_slice_{i+1:02d}_{int(actual_duration)}s.wav"
            
            success = slice_audio(input_file, output_file, start_time, actual_duration)
            if not success:
                break
        
        print(f"\n🎉 Created {i+1} test slices in {output_dir}")
        
    except Exception as e:
        print(f"❌ Error in auto slicing: {e}")

def main():
    parser = argparse.ArgumentParser(description="Audio Slicing Tool")
    parser.add_argument("input_file", type=Path, help="Input audio file")
    parser.add_argument("--output", "-o", type=Path, help="Output file (for single slice)")
    parser.add_argument("--start", "-s", type=float, default=0.0, help="Start time in seconds")
    parser.add_argument("--duration", "-d", type=float, default=30.0, help="Duration in seconds")
    parser.add_argument("--auto", "-a", action="store_true", help="Auto create multiple test slices")
    parser.add_argument("--output-dir", type=Path, default="temp/test_slices", help="Output directory for auto slices")
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"❌ Input file not found: {args.input_file}")
        return
    
    if args.auto:
        # Auto create multiple slices
        auto_slice_for_testing(args.input_file, args.output_dir, args.duration)
    else:
        # Create single slice
        if not args.output:
            # Generate output filename
            args.output = Path(f"temp/test_slices/{args.input_file.stem}_slice_{int(args.start)}s_{int(args.duration)}s.wav")
        
        slice_audio(args.input_file, args.output, args.start, args.duration)

if __name__ == "__main__":
    main()

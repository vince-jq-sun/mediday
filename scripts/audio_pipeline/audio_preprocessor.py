"""
Audio preprocessing module for silence detection and segmentation
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Tuple, Dict
import json
import subprocess
import tempfile
from .config import SILENCE_THRESHOLD_SECONDS, SEGMENTS_DIR, TEMP_DIR

class AudioPreprocessor:
    def __init__(self, silence_threshold_seconds: float = SILENCE_THRESHOLD_SECONDS):
        self.silence_threshold_seconds = silence_threshold_seconds
        
    def _convert_mp4_to_wav(self, audio_path: Path) -> Path:
        """
        Convert MP4/M4A file to temporary WAV file for processing
        Returns path to temporary WAV file
        """
        # Create temporary WAV file
        temp_dir = Path(tempfile.mkdtemp())
        temp_wav = temp_dir / f"{audio_path.stem}_temp.wav"
        
        # Use ffmpeg to extract audio track
        cmd = [
            '/opt/homebrew/Caskroom/miniforge/base/bin/ffmpeg', '-i', str(audio_path),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
            '-y', str(temp_wav)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return temp_wav
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to convert MP4 to WAV: {e}")
    
    def _is_mp4_format(self, audio_path: Path) -> bool:
        """
        Check if file is MP4/M4A format
        """
        file_ext = audio_path.suffix.lower()
        if file_ext in ['.mp4', '.m4a']:
            return True
        
        # Also check file content
        try:
            result = subprocess.run(['file', str(audio_path)], capture_output=True, text=True)
            return 'ISO Media' in result.stdout
        except:
            return False
        
    def detect_silence_segments(self, audio_path: Path) -> List[Tuple[float, float]]:
        """
        Detect silence segments in audio file
        Returns list of (start_time, end_time) tuples for silence segments
        """
        temp_wav = None
        try:
            # Handle MP4/M4A files by converting to temporary WAV
            if self._is_mp4_format(audio_path):
                print(f"🔧 Detected MP4/M4A format, converting to WAV for processing...")
                temp_wav = self._convert_mp4_to_wav(audio_path)
                audio_file_path = str(temp_wav)
                # Use soundfile for converted MP4 files to avoid numba issues
                y, sr = sf.read(audio_file_path)
                # Convert to mono if stereo (take mean of channels)
                if len(y.shape) > 1:
                    y = np.mean(y, axis=1)
            else:
                audio_file_path = str(audio_path)
                # Use librosa for regular audio files
                y, sr = librosa.load(audio_file_path, sr=None)
            
            # Calculate RMS energy
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            
            if temp_wav:  # For MP4 files, use numpy-based RMS calculation
                # Simple RMS calculation without librosa
                rms_values = []
                for i in range(0, len(y) - frame_length, hop_length):
                    frame = y[i:i + frame_length]
                    rms_val = np.sqrt(np.mean(frame ** 2))
                    rms_values.append(rms_val)
                
                rms = np.array(rms_values)
                # Convert to dB
                rms_db = 20 * np.log10(rms / np.max(rms) + 1e-10)  # Add small value to avoid log(0)
                
                # Create time array
                times = np.arange(len(rms)) * hop_length / sr
            else:
                # Use librosa for regular audio files
                rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
                # Convert to dB
                rms_db = librosa.amplitude_to_db(rms, ref=np.max)
                # Convert frame indices to time
                times = librosa.frames_to_time(np.arange(len(rms_db)), sr=sr, hop_length=hop_length)
            
            # Detect silence (threshold: -40 dB)
            silence_threshold_db = -40
            silence_frames = rms_db < silence_threshold_db
            
            # Group consecutive silence frames
            silence_segments = []
            start_time = None
            
            for i, is_silence in enumerate(silence_frames):
                if is_silence and start_time is None:
                    start_time = times[i]
                elif not is_silence and start_time is not None:
                    end_time = times[i]
                    duration = end_time - start_time
                    if duration >= self.silence_threshold_seconds:
                        silence_segments.append((start_time, end_time))
                    start_time = None
            
            # Handle case where audio ends with silence
            if start_time is not None:
                end_time = times[-1]
                duration = end_time - start_time
                if duration >= self.silence_threshold_seconds:
                    silence_segments.append((start_time, end_time))
            
            return silence_segments
            
        except Exception as e:
            raise RuntimeError(f"Failed to detect silence segments: {e}")
        finally:
            # Clean up temporary WAV file if created
            if temp_wav and temp_wav.exists():
                try:
                    temp_wav.unlink()
                    temp_wav.parent.rmdir()  # Remove temp directory if empty
                except:
                    pass
    
    def segment_audio(self, audio_path: Path, output_dir: Path = None) -> Dict:
        """
        Segment audio file by removing long silence periods
        Returns metadata about segments and silence gaps
        """
        if output_dir is None:
            output_dir = SEGMENTS_DIR
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        temp_wav = None
        try:
            # Handle MP4/M4A files by converting to temporary WAV
            if self._is_mp4_format(audio_path):
                print(f"🔧 Detected MP4/M4A format, converting to WAV for processing...")
                temp_wav = self._convert_mp4_to_wav(audio_path)
                audio_file_path = str(temp_wav)
                # Use soundfile for converted MP4 files to avoid numba issues
                y, sr = sf.read(audio_file_path)
                # Convert to mono if stereo (take mean of channels)
                if len(y.shape) > 1:
                    y = np.mean(y, axis=1)
            else:
                audio_file_path = str(audio_path)
                # Use librosa for regular audio files
                y, sr = librosa.load(audio_file_path, sr=None)
            total_duration = len(y) / sr
            
            # Detect silence segments
            silence_segments = self.detect_silence_segments(audio_path)
            
            # Create audio segments (non-silence parts)
            audio_segments = []
            segment_files = []
            
            current_start = 0.0
            
            for silence_start, silence_end in silence_segments:
                if silence_start > current_start:
                    # Add segment before silence
                    segment_start_sample = int(current_start * sr)
                    segment_end_sample = int(silence_start * sr)
                    
                    segment_audio = y[segment_start_sample:segment_end_sample]
                    
                    # Save segment
                    segment_filename = f"{audio_path.stem}_segment_{len(audio_segments):03d}.wav"
                    segment_path = output_dir / segment_filename
                    sf.write(str(segment_path), segment_audio, sr)
                    
                    audio_segments.append({
                        'segment_id': len(audio_segments),
                        'start_time': current_start,
                        'end_time': silence_start,
                        'duration': silence_start - current_start,
                        'file_path': str(segment_path)
                    })
                    
                    segment_files.append(segment_path)
                
                current_start = silence_end
            
            # Add final segment if there's audio after the last silence
            if current_start < total_duration:
                segment_start_sample = int(current_start * sr)
                segment_audio = y[segment_start_sample:]
                
                segment_filename = f"{audio_path.stem}_segment_{len(audio_segments):03d}.wav"
                segment_path = output_dir / segment_filename
                sf.write(str(segment_path), segment_audio, sr)
                
                audio_segments.append({
                    'segment_id': len(audio_segments),
                    'start_time': current_start,
                    'end_time': total_duration,
                    'duration': total_duration - current_start,
                    'file_path': str(segment_path)
                })
                
                segment_files.append(segment_path)
            
            # Create metadata
            metadata = {
                'original_file': str(audio_path),
                'total_duration': total_duration,
                'silence_threshold_seconds': self.silence_threshold_seconds,
                'silence_segments': [{'start': start, 'end': end, 'duration': end - start} 
                                   for start, end in silence_segments],
                'audio_segments': audio_segments,
                'total_segments': len(audio_segments),
                'total_silence_duration': sum(end - start for start, end in silence_segments),
                'total_audio_duration': sum(seg['duration'] for seg in audio_segments)
            }
            
            # Save metadata
            metadata_path = output_dir / f"{audio_path.stem}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return metadata
            
        except Exception as e:
            raise RuntimeError(f"Failed to segment audio: {e}")
        finally:
            # Clean up temporary WAV file if created
            if temp_wav and temp_wav.exists():
                try:
                    temp_wav.unlink()
                    temp_wav.parent.rmdir()  # Remove temp directory if empty
                except:
                    pass
    
    def process_directory(self, input_dir: Path, output_base_dir: Path = None) -> List[Dict]:
        """
        Process all audio files in a directory
        """
        if output_base_dir is None:
            output_base_dir = SEGMENTS_DIR
        
        results = []
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
        
        for audio_file in input_dir.iterdir():
            if audio_file.suffix.lower() in audio_extensions:
                print(f"Processing: {audio_file.name}")
                
                # Output directly to the specified output directory (no extra subdirectory)
                file_output_dir = output_base_dir
                
                try:
                    metadata = self.segment_audio(audio_file, file_output_dir)
                    results.append(metadata)
                    print(f"  → Created {metadata['total_segments']} segments")
                except Exception as e:
                    print(f"  → Error processing {audio_file.name}: {e}")
        
        return results

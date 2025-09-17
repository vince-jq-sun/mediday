"""
Audio preprocessing module for silence detection and segmentation
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Tuple, Dict
import json
from .config import SILENCE_THRESHOLD_SECONDS, SEGMENTS_DIR, TEMP_DIR

class AudioPreprocessor:
    def __init__(self, silence_threshold_seconds: float = SILENCE_THRESHOLD_SECONDS):
        self.silence_threshold_seconds = silence_threshold_seconds
        
    def detect_silence_segments(self, audio_path: Path) -> List[Tuple[float, float]]:
        """
        Detect silence segments in audio file
        Returns list of (start_time, end_time) tuples for silence segments
        """
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)
        
        # Calculate RMS energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Convert to dB
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        
        # Detect silence (threshold: -40 dB)
        silence_threshold_db = -40
        silence_frames = rms_db < silence_threshold_db
        
        # Convert frame indices to time
        times = librosa.frames_to_time(np.arange(len(silence_frames)), sr=sr, hop_length=hop_length)
        
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
    
    def segment_audio(self, audio_path: Path, output_dir: Path = None) -> Dict:
        """
        Segment audio file by removing long silence periods
        Returns metadata about segments and silence gaps
        """
        if output_dir is None:
            output_dir = SEGMENTS_DIR
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
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
                sf.write(segment_path, segment_audio, sr)
                
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
            sf.write(segment_path, segment_audio, sr)
            
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

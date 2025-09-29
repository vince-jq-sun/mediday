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
    def __init__(self, silence_threshold_seconds: float = SILENCE_THRESHOLD_SECONDS, min_segment_duration: float = 0.5, sec_len_approx: float = 0.0, boundary_search: float = 3.0, normalize_padding: bool = True, target_padding: float = 1.0):
        self.silence_threshold_seconds = silence_threshold_seconds
        self.min_segment_duration = min_segment_duration  # Minimum segment duration in seconds
        # Approximate section length mode. If >= 10 seconds, use approximate-length-based cuts.
        self.sec_len_approx = sec_len_approx or 0.0
        self.boundary_search = boundary_search or 3.0
        # Audio padding normalization settings
        self.normalize_padding = normalize_padding  # Whether to normalize front/back silence
        self.target_padding = target_padding  # Target padding duration in seconds (default 1.0s)
        
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
        
    def _detect_audio_boundaries(self, y: np.ndarray, sr: int) -> Tuple[float, float]:
        """
        Detect the start and end of actual audio content (non-silence)
        Returns (start_time, end_time) in seconds
        """
        # Calculate RMS energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        # Simple RMS calculation
        rms_values = []
        for i in range(0, len(y) - frame_length, hop_length):
            frame = y[i:i + frame_length]
            rms_val = np.sqrt(np.mean(frame ** 2))
            rms_values.append(rms_val)
        
        rms = np.array(rms_values)
        
        # Avoid division by zero
        max_rms = np.max(rms)
        if max_rms == 0:
            return 0.0, len(y) / sr
        
        # Convert to dB
        rms_db = 20 * np.log10(rms / max_rms + 1e-10)
        
        # Create time array
        times = np.arange(len(rms)) * hop_length / sr
        
        # Detect non-silence (threshold: -40 dB)
        silence_threshold_db = -40
        non_silence_frames = rms_db >= silence_threshold_db
        
        # Find first and last non-silence frames
        non_silence_indices = np.where(non_silence_frames)[0]
        
        if len(non_silence_indices) == 0:
            # All silence, return original boundaries
            return 0.0, len(y) / sr
        
        start_time = times[non_silence_indices[0]]
        end_time = times[non_silence_indices[-1]]
        
        return start_time, end_time
    
    def normalize_audio_padding(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Normalize the front and back silence/padding of audio to target_padding seconds
        """
        if not self.normalize_padding:
            return y
        
        # Detect actual audio boundaries
        audio_start, audio_end = self._detect_audio_boundaries(y, sr)
        total_duration = len(y) / sr
        
        print(f"  → Original audio: {total_duration:.2f}s, content: {audio_start:.2f}s - {audio_end:.2f}s")
        print(f"  → Front padding: {audio_start:.2f}s, back padding: {total_duration - audio_end:.2f}s")
        
        # Calculate target sample positions
        target_padding_samples = int(self.target_padding * sr)
        audio_start_sample = int(audio_start * sr)
        audio_end_sample = int(audio_end * sr)
        
        # Extract the actual audio content
        audio_content = y[audio_start_sample:audio_end_sample]
        
        # Create silence for padding
        front_silence = np.zeros(target_padding_samples)
        back_silence = np.zeros(target_padding_samples)
        
        # Combine: front_silence + audio_content + back_silence
        normalized_audio = np.concatenate([front_silence, audio_content, back_silence])
        
        new_duration = len(normalized_audio) / sr
        print(f"  → Normalized audio: {new_duration:.2f}s with {self.target_padding:.1f}s padding on each side")
        
        return normalized_audio
        
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
            
            # Apply audio padding normalization before segmentation
            if self.normalize_padding:
                print(f"🔧 Normalizing audio padding to {self.target_padding}s...")
                y = self.normalize_audio_padding(y, sr)
            
            total_duration = len(y) / sr
            
            # Detect silence segments (used either for direct silence-threshold cutting or for boundary search)
            # Note: We need to detect silence on the normalized audio, so we create a temporary file
            if self.normalize_padding:
                # Create temporary file with normalized audio for silence detection
                temp_normalized_path = Path(tempfile.mktemp(suffix='.wav'))
                sf.write(str(temp_normalized_path), y, sr)
                silence_segments = self.detect_silence_segments(temp_normalized_path)
                # Clean up temporary file
                try:
                    temp_normalized_path.unlink()
                except:
                    pass
            else:
                silence_segments = self.detect_silence_segments(audio_path)

            # Create audio segments according to the selected mode
            audio_segments = []
            segment_files = []

            # Mode A: Approximate-length based segmentation when sec_len_approx >= 10
            if self.sec_len_approx >= 10.0:
                print(f"  → Using approx-length mode: {self.sec_len_approx}s sections, ±{self.boundary_search}s search window")
                # Sequential boundary finding: start from each actual cut position and find next boundary
                cut_times = []
                current_pos = 0.0
                silence_cuts_found = 0
                
                while current_pos < total_duration:
                    # Calculate target position for next cut (current_pos + sec_len_approx)
                    target_pos = current_pos + self.sec_len_approx
                    
                    # If target is beyond audio end, stop
                    if target_pos >= total_duration:
                        break
                    
                    # Search window around target position
                    window_start = max(current_pos + 1.0, target_pos - self.boundary_search)  # Ensure at least 1s after current
                    window_end = min(total_duration, target_pos + self.boundary_search)
                    
                    # Find silence segments overlapping the search window
                    candidates = []
                    for s_start, s_end in silence_segments:
                        # Check if silence segment overlaps with search window
                        if s_start < window_end and s_end > window_start:
                            # Calculate the overlapping portion
                            overlap_start = max(s_start, window_start)
                            overlap_end = min(s_end, window_end)
                            overlap_duration = overlap_end - overlap_start
                            if overlap_duration > 0.1:  # At least 0.1s overlap
                                candidates.append((s_start, s_end, overlap_duration))
                    
                    if candidates:
                        # Choose the candidate with the longest overlap (not total duration)
                        s_start, s_end, _ = max(candidates, key=lambda x: x[2])
                        # Cut at the midpoint of the silence segment
                        cut_time = (s_start + s_end) / 2.0
                        silence_cuts_found += 1
                    else:
                        # No silence in the window; fall back to target time
                        cut_time = target_pos
                    
                    # Ensure cut_time is valid and after current position
                    cut_time = min(max(current_pos + 0.5, cut_time), total_duration)
                    cut_times.append(cut_time)
                    
                    # Update current position to the actual cut time for next iteration
                    current_pos = cut_time

                # Build boundaries from sequential cut times
                boundaries = [0.0] + cut_times + [total_duration]
                print(f"  → Found {silence_cuts_found} silence-based cuts out of {len(cut_times)} total cuts")

                # Emit segments between boundaries
                for i in range(len(boundaries) - 1):
                    seg_start = boundaries[i]
                    seg_end = boundaries[i + 1]
                    seg_duration = seg_end - seg_start
                    if seg_duration >= self.min_segment_duration:
                        start_sample = int(seg_start * sr)
                        end_sample = int(seg_end * sr)
                        segment_audio = y[start_sample:end_sample]
                        segment_filename = f"{audio_path.stem}_segment_{len(audio_segments):03d}.wav"
                        segment_path = output_dir / segment_filename
                        sf.write(str(segment_path), segment_audio, sr)
                        audio_segments.append({
                            'segment_id': len(audio_segments),
                            'start_time': seg_start,
                            'end_time': seg_end,
                            'duration': seg_duration,
                            'file_path': str(segment_path)
                        })
                        segment_files.append(segment_path)
                    else:
                        print(f"  → Skipping short segment ({seg_duration:.3f}s < {self.min_segment_duration}s)")

                used_mode = 'approx_length'
                cut_boundaries = boundaries
            else:
                # Mode B: Original silence-threshold-based segmentation
                current_start = 0.0
                for silence_start, silence_end in silence_segments:
                    if silence_start > current_start:
                        # Check if segment is long enough
                        segment_duration = silence_start - current_start
                        if segment_duration >= self.min_segment_duration:
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
                                'duration': segment_duration,
                                'file_path': str(segment_path)
                            })
                            
                            segment_files.append(segment_path)
                        else:
                            print(f"  → Skipping short segment ({segment_duration:.3f}s < {self.min_segment_duration}s)")
                    
                    current_start = silence_end
                
                # Add final segment if there's audio after the last silence
                if current_start < total_duration:
                    final_segment_duration = total_duration - current_start
                    if final_segment_duration >= self.min_segment_duration:
                        segment_start_sample = int(current_start * sr)
                        segment_audio = y[segment_start_sample:]
                        
                        segment_filename = f"{audio_path.stem}_segment_{len(audio_segments):03d}.wav"
                        segment_path = output_dir / segment_filename
                        sf.write(str(segment_path), segment_audio, sr)
                        
                        audio_segments.append({
                            'segment_id': len(audio_segments),
                            'start_time': current_start,
                            'end_time': total_duration,
                            'duration': final_segment_duration,
                            'file_path': str(segment_path)
                        })
                        
                        segment_files.append(segment_path)
                    else:
                        print(f"  → Skipping short final segment ({final_segment_duration:.3f}s < {self.min_segment_duration}s)")

                used_mode = 'silence_threshold'
                cut_boundaries = None
            
            # Create metadata
            metadata = {
                'original_file': str(audio_path),
                'total_duration': total_duration,
                'silence_threshold_seconds': self.silence_threshold_seconds,
                'min_segment_duration': self.min_segment_duration,
                'mode': used_mode,
                'sec_len_approx': self.sec_len_approx,
                'boundary_search': self.boundary_search,
                'silence_segments': [{'start': start, 'end': end, 'duration': end - start} 
                                   for start, end in silence_segments],
                'audio_segments': audio_segments,
                'total_segments': len(audio_segments),
                'total_silence_duration': sum(end - start for start, end in silence_segments),
                'total_audio_duration': sum(seg['duration'] for seg in audio_segments)
            }
            if cut_boundaries is not None:
                metadata['cut_boundaries'] = cut_boundaries
            
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

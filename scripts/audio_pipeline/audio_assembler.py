"""
Audio assembly module to combine segments with silence and create final output
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import json
from typing import Dict, List, Optional
from pydub import AudioSegment
from .config import OUTPUT_DIR, MANUAL_RECORDINGS_DIR, AUDIO_SYNTHESIS_DIR

class AudioAssembler:
    def __init__(self):
        pass
    
    def create_silence(self, duration_seconds: float, sample_rate: int = 44100) -> np.ndarray:
        """Create silence audio array"""
        samples = int(duration_seconds * sample_rate)
        return np.zeros(samples)
    
    def calculate_rms_volume(self, audio_data: np.ndarray) -> float:
        """Calculate RMS (Root Mean Square) volume of audio data"""
        if len(audio_data) == 0:
            return 0.0
        return np.sqrt(np.mean(audio_data ** 2))
    
    def scale_audio_volume(self, audio_data: np.ndarray, target_rms: float) -> np.ndarray:
        """Scale audio data to match target RMS volume"""
        if len(audio_data) == 0:
            return audio_data
        
        current_rms = self.calculate_rms_volume(audio_data)
        if current_rms == 0:
            return audio_data
        
        # Calculate scaling factor
        scale_factor = target_rms / current_rms
        
        # Apply scaling with clipping protection
        scaled_audio = audio_data * scale_factor
        
        # Check for clipping and apply more conservative protection
        max_val = np.max(np.abs(scaled_audio))
        if max_val > 0.95:  # Use 0.95 instead of 1.0 to leave some headroom
            # Reduce scale factor to prevent clipping
            safe_scale_factor = scale_factor * (0.95 / max_val)
            scaled_audio = audio_data * safe_scale_factor
            actual_rms = self.calculate_rms_volume(scaled_audio)
            print(f"⚠️  Clipping protection: reduced scale factor from {scale_factor:.3f} to {safe_scale_factor:.3f}")
            print(f"   Target RMS: {target_rms:.6f}, Achieved RMS: {actual_rms:.6f}")
        
        return scaled_audio
    
    def get_original_segment_volume(self, segment_id: int, original_file_path: str) -> float:
        """Get the RMS volume of the original audio segment"""
        # Parse the original file path to extract collection and project info
        original_path = Path(original_file_path)
        base_filename = original_path.stem
        
        # Extract collection name from the path
        # Expected format: data/{collection}/{project}.mp3
        if len(original_path.parts) >= 3 and original_path.parts[-3] == "data":
            collection_name = original_path.parts[-2]
        else:
            # Fallback: try to extract from filename or use default
            collection_name = "awake_where_you_are_english"  # Default collection
        
        # Try multiple possible segment file locations
        possible_paths = [
            # New hierarchical structure: temp/{collection}/{project}/segments/
            Path(f"temp/{collection_name}/{base_filename}/segments/{base_filename}_segment_{segment_id:03d}.wav"),
            # Legacy structure: segments/{project}/
            Path(f"segments/{base_filename}/{base_filename}_segment_{segment_id:03d}.wav"),
            # Direct segments directory
            Path(f"segments/{base_filename}_segment_{segment_id:03d}.wav")
        ]
        
        segment_file = None
        for path in possible_paths:
            if path.exists():
                segment_file = path
                break
        
        if not segment_file:
            print(f"Warning: Original segment file not found for segment {segment_id}. Tried paths:")
            for path in possible_paths:
                print(f"  - {path}")
            print(f"Original file path: {original_file_path}")
            print(f"Collection: {collection_name}, Project: {base_filename}")
            return 0.1  # Default RMS value
        
        try:
            audio_data, _ = librosa.load(segment_file, sr=None)
            rms_volume = self.calculate_rms_volume(audio_data)
            print(f"📊 Original segment {segment_id} RMS volume: {rms_volume:.6f} (from {segment_file})")
            return rms_volume
        except Exception as e:
            print(f"Error loading original segment {segment_id} from {segment_file}: {e}")
            return 0.1  # Default RMS value
    
    def load_audio_segment(self, file_path: Path) -> tuple[np.ndarray, int]:
        """Load audio segment and return audio data and sample rate"""
        try:
            audio_data, sr = librosa.load(file_path, sr=None)
            return audio_data, sr
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return np.array([]), 44100
    
    def assemble_from_manual_recordings(self, translation_data: Dict, 
                                      output_path: Path = None,
                                      compression_settings: Dict = None,
                                      manual_recordings_dir: Path = None,
                                      enable_volume_scaling: bool = True) -> Dict:
        """
        Assemble final audio from manual recordings
        """
        if output_path is None:
            base_filename = Path(translation_data['original_file']).stem
            output_path = OUTPUT_DIR / f"{base_filename}_manual_final.mp3"
        
        if compression_settings is None:
            compression_settings = {
                'bitrate': '128k',
                'format': 'mp3'
            }
        
        # Load original metadata to get silence information
        original_file = Path(translation_data['original_file'])
        metadata_file = None
        
        # Find corresponding metadata file
        for metadata_path in Path(original_file.parent).glob("*_metadata.json"):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                if metadata['original_file'] == str(original_file):
                    metadata_file = metadata_path
                    break
        
        if not metadata_file:
            print("Warning: No metadata file found, assembling without silence restoration")
            silence_segments = []
        else:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                silence_segments = metadata.get('silence_segments', [])
        
        # Collect audio segments
        audio_segments = []
        base_filename = Path(translation_data['original_file']).stem
        
        # Use custom manual recordings directory if provided, otherwise use default
        recordings_dir = manual_recordings_dir if manual_recordings_dir else MANUAL_RECORDINGS_DIR
        
        for segment in translation_data['segments']:
            segment_id = segment['segment_id']
            
            # Look for manual recording first
            manual_recording = recordings_dir / f"{base_filename}_segment_{segment_id:03d}_manual.wav"
            
            if manual_recording.exists():
                audio_data, sr = self.load_audio_segment(manual_recording)
                if len(audio_data) > 0:
                    audio_segments.append({
                        'audio_data': audio_data,
                        'sample_rate': sr,
                        'segment_id': segment_id,
                        'source': 'manual'
                    })
                    print(f"Using manual recording for segment {segment_id}")
                else:
                    print(f"Failed to load manual recording for segment {segment_id}")
            else:
                print(f"No manual recording found for segment {segment_id}")
        
        if not audio_segments:
            return {
                'success': False,
                'error': 'No audio segments found',
                'output_path': str(output_path)
            }
        
        # Assemble final audio
        return self._assemble_audio_segments(audio_segments, silence_segments, 
                                           output_path, compression_settings,
                                           original_file_path=translation_data['original_file'],
                                           enable_volume_scaling=enable_volume_scaling)
    
    def assemble_from_synthesis(self, synthesis_data: Dict,
                               output_path: Path = None,
                               compression_settings: Dict = None,
                               enable_volume_scaling: bool = True) -> Dict:
        """
        Assemble final audio from synthesized speech
        """
        if output_path is None:
            base_filename = Path(synthesis_data['original_file']).stem
            output_path = OUTPUT_DIR / f"{base_filename}_synthesis_final.mp3"
        
        if compression_settings is None:
            compression_settings = {
                'bitrate': '128k',
                'format': 'mp3'
            }
        
        # Load original metadata for silence information
        original_file = Path(synthesis_data['original_file'])
        metadata_file = None
        
        for metadata_path in Path(original_file.parent).glob("*_metadata.json"):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                if metadata['original_file'] == str(original_file):
                    metadata_file = metadata_path
                    break
        
        if not metadata_file:
            print("Warning: No metadata file found, assembling without silence restoration")
            silence_segments = []
        else:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                silence_segments = metadata.get('silence_segments', [])
        
        # Collect synthesized audio segments
        audio_segments = []
        
        for segment in synthesis_data['segments']:
            synthesis_result = segment.get('synthesis_result', {})
            
            if synthesis_result.get('success') and synthesis_result.get('output_path'):
                audio_path = Path(synthesis_result['output_path'])
                
                if audio_path.exists():
                    audio_data, sr = self.load_audio_segment(audio_path)
                    if len(audio_data) > 0:
                        audio_segments.append({
                            'audio_data': audio_data,
                            'sample_rate': sr,
                            'segment_id': segment['segment_id'],
                            'source': 'synthesis'
                        })
                        print(f"Using synthesized audio for segment {segment['segment_id']}")
                    else:
                        print(f"Failed to load synthesized audio for segment {segment['segment_id']}")
                else:
                    print(f"Synthesized audio file not found: {audio_path}")
            else:
                print(f"No valid synthesis result for segment {segment['segment_id']}")
        
        if not audio_segments:
            return {
                'success': False,
                'error': 'No audio segments found',
                'output_path': str(output_path)
            }
        
        # Assemble final audio
        return self._assemble_audio_segments(audio_segments, silence_segments,
                                           output_path, compression_settings,
                                           original_file_path=synthesis_data['original_file'],
                                           enable_volume_scaling=enable_volume_scaling)
    
    def _assemble_audio_segments(self, audio_segments: List[Dict], 
                                silence_segments: List[Dict],
                                output_path: Path,
                                compression_settings: Dict,
                                original_file_path: str = None,
                                enable_volume_scaling: bool = True) -> Dict:
        """
        Internal method to assemble audio segments with silence
        """
        try:
            # Sort segments by segment_id
            audio_segments.sort(key=lambda x: x['segment_id'])
            
            # Use the sample rate from the first segment
            target_sr = audio_segments[0]['sample_rate']
            
            # Resample all segments to the same sample rate if needed and apply volume scaling
            for segment in audio_segments:
                if segment['sample_rate'] != target_sr:
                    segment['audio_data'] = librosa.resample(
                        segment['audio_data'], 
                        orig_sr=segment['sample_rate'], 
                        target_sr=target_sr
                    )
                
                # Apply volume scaling to match original segment volume
                if enable_volume_scaling and original_file_path:
                    segment_id = segment['segment_id']
                    original_rms = self.get_original_segment_volume(segment_id, original_file_path)
                    current_rms = self.calculate_rms_volume(segment['audio_data'])
                    
                    if original_rms > 0 and current_rms > 0:
                        segment['audio_data'] = self.scale_audio_volume(segment['audio_data'], original_rms)
                        # Calculate actual achieved RMS after scaling
                        actual_rms = self.calculate_rms_volume(segment['audio_data'])
                        scale_factor = original_rms / current_rms
                        print(f"🔊 Segment {segment_id} volume scaling:")
                        print(f"   Original: {current_rms:.6f} -> Target: {original_rms:.6f} -> Actual: {actual_rms:.6f}")
                        print(f"   Scale factor: {scale_factor:.3f}, Effectiveness: {(actual_rms/original_rms)*100:.1f}%")
                    else:
                        print(f"⚠️  Skipping volume scaling for segment {segment_id} (zero volume detected)")
                else:
                    if enable_volume_scaling:
                        print(f"⚠️  Volume scaling enabled but no original file path provided for segment {segment['segment_id']}")
                    else:
                        print(f"📢 Volume scaling disabled for segment {segment['segment_id']}")
            
            # Assemble audio with silence
            final_audio = np.array([])
            
            for i, segment in enumerate(audio_segments):
                # Add the audio segment
                final_audio = np.concatenate([final_audio, segment['audio_data']])
                
                # Add silence after this segment (except for the last segment)
                if i < len(audio_segments) - 1 and i < len(silence_segments):
                    silence_duration = silence_segments[i]['duration']
                    silence_audio = self.create_silence(silence_duration, target_sr)
                    final_audio = np.concatenate([final_audio, silence_audio])
            
            # Save as WAV first (high quality)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temp_wav_path = output_path.with_suffix('.wav')
            sf.write(temp_wav_path, final_audio, target_sr)
            
            # Convert to final format with compression
            if compression_settings['format'].lower() == 'mp3':
                audio_segment = AudioSegment.from_wav(str(temp_wav_path))
                audio_segment.export(
                    str(output_path),
                    format="mp3",
                    bitrate=compression_settings['bitrate']
                )
                # Remove temporary WAV file
                temp_wav_path.unlink()
            else:
                # Keep as WAV or convert to other formats as needed
                if output_path.suffix.lower() != '.wav':
                    temp_wav_path.rename(output_path)
            
            # Calculate statistics
            total_duration = len(final_audio) / target_sr
            file_size = output_path.stat().st_size
            
            return {
                'success': True,
                'output_path': str(output_path),
                'total_duration': total_duration,
                'file_size': file_size,
                'sample_rate': target_sr,
                'total_segments': len(audio_segments),
                'compression_settings': compression_settings
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output_path': str(output_path)
            }
    
    def create_mixed_assembly(self, translation_data: Dict, synthesis_data: Dict,
                             output_path: Path = None,
                             prefer_manual: bool = True,
                             compression_settings: Dict = None,
                             manual_recordings_dir: Path = None,
                             enable_volume_scaling: bool = True) -> Dict:
        """
        Create assembly using both manual recordings and synthesized audio
        Prefer manual recordings when available
        """
        if output_path is None:
            base_filename = Path(translation_data['original_file']).stem
            output_path = OUTPUT_DIR / f"{base_filename}_mixed_final.mp3"
        
        if compression_settings is None:
            compression_settings = {
                'bitrate': '128k',
                'format': 'mp3'
            }
        
        # Load original metadata for silence information
        original_file = Path(translation_data['original_file'])
        metadata_file = None
        
        for metadata_path in Path(original_file.parent).glob("*_metadata.json"):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                if metadata['original_file'] == str(original_file):
                    metadata_file = metadata_path
                    break
        
        if not metadata_file:
            print("Warning: No metadata file found, assembling without silence restoration")
            silence_segments = []
        else:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                silence_segments = metadata.get('silence_segments', [])
        
        # Collect audio segments (prefer manual over synthesis)
        audio_segments = []
        base_filename = Path(translation_data['original_file']).stem
        
        # Create lookup for synthesis results
        synthesis_lookup = {}
        for segment in synthesis_data.get('segments', []):
            synthesis_lookup[segment['segment_id']] = segment
        
        # Use custom manual recordings directory if provided, otherwise use default
        recordings_dir = manual_recordings_dir if manual_recordings_dir else MANUAL_RECORDINGS_DIR
        
        for segment in translation_data['segments']:
            segment_id = segment['segment_id']
            
            # Check for manual recording first
            manual_recording = recordings_dir / f"{base_filename}_segment_{segment_id:03d}_manual.wav"
            
            if prefer_manual and manual_recording.exists():
                audio_data, sr = self.load_audio_segment(manual_recording)
                if len(audio_data) > 0:
                    audio_segments.append({
                        'audio_data': audio_data,
                        'sample_rate': sr,
                        'segment_id': segment_id,
                        'source': 'manual'
                    })
                    print(f"Using manual recording for segment {segment_id}")
                    continue
            
            # Fall back to synthesis
            if segment_id in synthesis_lookup:
                synthesis_segment = synthesis_lookup[segment_id]
                synthesis_result = synthesis_segment.get('synthesis_result', {})
                
                if synthesis_result.get('success') and synthesis_result.get('output_path'):
                    audio_path = Path(synthesis_result['output_path'])
                    
                    if audio_path.exists():
                        audio_data, sr = self.load_audio_segment(audio_path)
                        if len(audio_data) > 0:
                            audio_segments.append({
                                'audio_data': audio_data,
                                'sample_rate': sr,
                                'segment_id': segment_id,
                                'source': 'synthesis'
                            })
                            print(f"Using synthesized audio for segment {segment_id}")
                            continue
            
            print(f"No audio found for segment {segment_id}")
        
        if not audio_segments:
            return {
                'success': False,
                'error': 'No audio segments found',
                'output_path': str(output_path)
            }
        
        # Assemble final audio
        result = self._assemble_audio_segments(audio_segments, silence_segments,
                                             output_path, compression_settings,
                                             original_file_path=translation_data['original_file'],
                                             enable_volume_scaling=enable_volume_scaling)
        
        # Add source information
        if result['success']:
            manual_count = sum(1 for seg in audio_segments if seg['source'] == 'manual')
            synthesis_count = sum(1 for seg in audio_segments if seg['source'] == 'synthesis')
            
            result['source_breakdown'] = {
                'manual_recordings': manual_count,
                'synthesized_audio': synthesis_count,
                'total_segments': len(audio_segments)
            }
        
        return result

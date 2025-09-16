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
                                      compression_settings: Dict = None) -> Dict:
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
        
        for segment in translation_data['segments']:
            segment_id = segment['segment_id']
            
            # Look for manual recording first
            manual_recording = MANUAL_RECORDINGS_DIR / f"{base_filename}_segment_{segment_id:03d}_manual.wav"
            
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
                                           output_path, compression_settings)
    
    def assemble_from_synthesis(self, synthesis_data: Dict,
                               output_path: Path = None,
                               compression_settings: Dict = None) -> Dict:
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
                                           output_path, compression_settings)
    
    def _assemble_audio_segments(self, audio_segments: List[Dict], 
                                silence_segments: List[Dict],
                                output_path: Path,
                                compression_settings: Dict) -> Dict:
        """
        Internal method to assemble audio segments with silence
        """
        try:
            # Sort segments by segment_id
            audio_segments.sort(key=lambda x: x['segment_id'])
            
            # Use the sample rate from the first segment
            target_sr = audio_segments[0]['sample_rate']
            
            # Resample all segments to the same sample rate if needed
            for segment in audio_segments:
                if segment['sample_rate'] != target_sr:
                    segment['audio_data'] = librosa.resample(
                        segment['audio_data'], 
                        orig_sr=segment['sample_rate'], 
                        target_sr=target_sr
                    )
            
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
                             compression_settings: Dict = None) -> Dict:
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
        
        for segment in translation_data['segments']:
            segment_id = segment['segment_id']
            
            # Check for manual recording first
            manual_recording = MANUAL_RECORDINGS_DIR / f"{base_filename}_segment_{segment_id:03d}_manual.wav"
            
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
                                             output_path, compression_settings)
        
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

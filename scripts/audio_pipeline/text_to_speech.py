"""
Google Text-to-Speech integration for high-quality speech synthesis
"""
from google.cloud import texttospeech
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
from pathlib import Path
import json
import os
import re
import numpy as np
from pydub import AudioSegment
from typing import Dict, List, Tuple
from .config import (
    TTS_LANGUAGE_CODE,
    TTS_VOICE_NAME,
    TTS_AUDIO_ENCODING,
    AUDIO_SYNTHESIS_DIR
)

class TextToSpeechSynthesizer:
    def __init__(self):
        # Set Google Cloud credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json"
        
        # Use REST transport to avoid gRPC 503 errors
        self.client = texttospeech.TextToSpeechClient(transport="rest")
        
    def synthesize_text(self, text: str, output_path: Path, 
                       voice_name: str = TTS_VOICE_NAME,
                       speaking_rate: float = 1.0,
                       pitch: float = 0.0) -> Dict:
        """
        Synthesize speech from text using Google Text-to-Speech
        """
        if not text.strip():
            return {
                'text': text,
                'output_path': str(output_path),
                'error': 'Empty text',
                'success': False
            }
        
        try:
            # Set up synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=TTS_LANGUAGE_CODE,
                name=voice_name
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            
            # Perform synthesis with timeout
            request = texttospeech.SynthesizeSpeechRequest(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            response = self.client.synthesize_speech(request=request, timeout=30)
            
            # Save audio file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            return {
                'text': text,
                'output_path': str(output_path),
                'voice_name': voice_name,
                'speaking_rate': speaking_rate,
                'pitch': pitch,
                'success': True,
                'file_size': output_path.stat().st_size
            }
            
        except InvalidArgument as e:
            return {
                'text': text,
                'output_path': str(output_path),
                'error': f'Invalid voice or configuration: {e}',
                'success': False
            }
        except GoogleAPICallError as e:
            return {
                'text': text,
                'output_path': str(output_path),
                'error': f'Google API call failed: {e}',
                'success': False
            }
        except Exception as e:
            return {
                'text': text,
                'output_path': str(output_path),
                'error': str(e),
                'success': False
            }
    
    def synthesize_translation_results(self, translation_data: Dict, output_dir: Path = None,
                                     voice_settings: Dict = None, use_pause_aware: bool = True) -> Dict:
        """
        Synthesize speech for all translated segments
        
        Args:
            translation_data: Translation results data
            output_dir: Output directory for synthesis files
            voice_settings: Voice configuration settings
            use_pause_aware: Whether to use pause-aware synthesis for texts with pause markers
        """
        if voice_settings is None:
            voice_settings = {
                'voice_name': TTS_VOICE_NAME,
                'speaking_rate': 1.0,
                'pitch': 0.0
            }
        
        results = {
            'original_file': translation_data['original_file'],
            'total_segments': translation_data['total_segments'],
            'voice_settings': voice_settings,
            'use_pause_aware': use_pause_aware,
            'segments': []
        }
        
        base_filename = Path(translation_data['original_file']).stem
        
        # Use the specified output directory directly (no extra subdirectory)
        if output_dir is None:
            output_dir = AUDIO_SYNTHESIS_DIR
        project_synthesis_dir = output_dir
        project_synthesis_dir.mkdir(parents=True, exist_ok=True)
        
        for segment in translation_data['segments']:
            segment_id = segment['segment_id']
            chinese_text = segment['translated_text']
            
            print(f"Synthesizing segment {segment_id + 1}/{translation_data['total_segments']}")
            
            if chinese_text:
                # Create output filename in project subfolder
                output_filename = f"{base_filename}_segment_{segment_id:03d}_synthesis.mp3"
                output_path = project_synthesis_dir / output_filename
                
                # Check if text contains pause markers and use appropriate synthesis method
                has_pause_markers = re.search(r'<\d+(?:\.\d+)?>', chinese_text) is not None
                
                if use_pause_aware and has_pause_markers:
                    print(f"  → Using pause-aware synthesis for text with pause markers")
                    synthesis_result = self.synthesize_text_with_pauses(
                        chinese_text, 
                        output_path,
                        **voice_settings
                    )
                else:
                    synthesis_result = self.synthesize_text(
                        chinese_text, 
                        output_path,
                        **voice_settings
                    )
                
                print(f"  → Text: {chinese_text[:50]}...")
                if synthesis_result['success']:
                    print(f"  → Saved: {output_path.name}")
                    if has_pause_markers and use_pause_aware:
                        print(f"  → Processed {synthesis_result.get('segments_processed', 0)} segments with pauses")
                else:
                    print(f"  → Error: {synthesis_result.get('error', 'Unknown error')}")
            else:
                synthesis_result = {
                    'text': '',
                    'output_path': '',
                    'error': 'No Chinese text available',
                    'success': False
                }
            
            segment_result = {
                'segment_id': segment_id,
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'translated_text': chinese_text,
                'synthesis_result': synthesis_result
            }
            
            results['segments'].append(segment_result)
        
        # Save synthesis results in the output directory
        results_output_path = project_synthesis_dir / f"{base_filename}_synthesis_results.json"
        
        with open(results_output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def get_available_voices(self, language_code: str = TTS_LANGUAGE_CODE) -> List[Dict]:
        """
        Get list of available voices for the specified language
        """
        try:
            voices = self.client.list_voices()
            
            available_voices = []
            for voice in voices.voices:
                if language_code in voice.language_codes:
                    voice_info = {
                        'name': voice.name,
                        'language_codes': list(voice.language_codes),
                        'ssml_gender': voice.ssml_gender.name,
                        'natural_sample_rate_hertz': voice.natural_sample_rate_hertz
                    }
                    available_voices.append(voice_info)
            
            return available_voices
            
        except Exception as e:
            print(f"Error getting available voices: {e}")
            return []
    
    def parse_pause_text(self, text: str) -> List[Tuple[str, float]]:
        """
        Parse text with pause markers and return list of (text_segment, pause_duration) tuples
        
        Args:
            text: Text with pause markers like "Hello <1.55> world <2.0> end"
            
        Returns:
            List of tuples: [(text_segment, pause_duration), ...]
            pause_duration is 0 for text segments, actual duration for pause segments
        """
        if not text:
            return []
        
        # Pattern to match pause markers: <number> format like <1.55> or <2.0>
        pause_pattern = r'<(\d+(?:\.\d+)?)>'
        
        segments = []
        last_end = 0
        
        for match in re.finditer(pause_pattern, text):
            # Add text segment before the pause
            text_before = text[last_end:match.start()].strip()
            if text_before:
                segments.append((text_before, 0.0))
            
            # Add pause segment
            pause_duration_str = match.group(1)
            pause_duration = float(pause_duration_str)
            
            segments.append(("", pause_duration))
            last_end = match.end()
        
        # Add remaining text after last pause
        remaining_text = text[last_end:].strip()
        if remaining_text:
            segments.append((remaining_text, 0.0))
        
        return segments
    
    def create_silence(self, duration_seconds: float, sample_rate: int = 24000) -> AudioSegment:
        """
        Create a silent audio segment of specified duration
        
        Args:
            duration_seconds: Duration of silence in seconds
            sample_rate: Audio sample rate
            
        Returns:
            AudioSegment with silence
        """
        # Create silence using pydub
        silence_ms = int(duration_seconds * 1000)  # Convert to milliseconds
        silence = AudioSegment.silent(duration=silence_ms, frame_rate=sample_rate)
        return silence
    
    def synthesize_text_with_pauses(self, text: str, output_path: Path,
                                  voice_name: str = TTS_VOICE_NAME,
                                  speaking_rate: float = 1.0,
                                  pitch: float = 0.0) -> Dict:
        """
        Synthesize text with pause markers, creating separate audio segments and combining them
        
        Args:
            text: Text with pause markers like "Hello <pause:2.5> world"
            output_path: Path for the final combined audio file
            voice_name: TTS voice to use
            speaking_rate: Speaking rate
            pitch: Pitch adjustment
            
        Returns:
            Dictionary with synthesis results
        """
        if not text.strip():
            return {
                'text': text,
                'output_path': str(output_path),
                'error': 'Empty text',
                'success': False
            }
        
        try:
            # Parse text into segments
            segments = self.parse_pause_text(text)
            
            if not segments:
                return {
                    'text': text,
                    'output_path': str(output_path),
                    'error': 'No valid segments found',
                    'success': False
                }
            
            # Create temporary directory for segment files
            temp_dir = output_path.parent / f"{output_path.stem}_temp_segments"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            audio_segments = []
            segment_results = []
            
            for i, (segment_text, pause_duration) in enumerate(segments):
                if segment_text:  # Text segment - synthesize
                    temp_output = temp_dir / f"segment_{i:03d}.mp3"
                    
                    synthesis_result = self.synthesize_text(
                        segment_text, temp_output, voice_name, speaking_rate, pitch
                    )
                    
                    if synthesis_result['success']:
                        # Load the synthesized audio
                        audio_segment = AudioSegment.from_mp3(temp_output)
                        audio_segments.append(audio_segment)
                        segment_results.append({
                            'type': 'text',
                            'content': segment_text,
                            'file_path': str(temp_output),
                            'success': True
                        })
                    else:
                        segment_results.append({
                            'type': 'text',
                            'content': segment_text,
                            'error': synthesis_result.get('error'),
                            'success': False
                        })
                        # Continue with other segments even if one fails
                        
                elif pause_duration > 0:  # Pause segment - create silence
                    silence = self.create_silence(pause_duration)
                    audio_segments.append(silence)
                    segment_results.append({
                        'type': 'pause',
                        'duration': pause_duration,
                        'success': True
                    })
            
            # Combine all audio segments
            if audio_segments:
                combined_audio = audio_segments[0]
                for segment in audio_segments[1:]:
                    combined_audio += segment
                
                # Export the combined audio
                output_path.parent.mkdir(parents=True, exist_ok=True)
                combined_audio.export(str(output_path), format="mp3")
                
                # Clean up temporary files
                for temp_file in temp_dir.glob("*.mp3"):
                    temp_file.unlink()
                temp_dir.rmdir()
                
                return {
                    'text': text,
                    'output_path': str(output_path),
                    'voice_name': voice_name,
                    'speaking_rate': speaking_rate,
                    'pitch': pitch,
                    'success': True,
                    'file_size': output_path.stat().st_size,
                    'segments_processed': len(segments),
                    'segment_results': segment_results
                }
            else:
                return {
                    'text': text,
                    'output_path': str(output_path),
                    'error': 'No audio segments generated',
                    'success': False,
                    'segment_results': segment_results
                }
                
        except Exception as e:
            return {
                'text': text,
                'output_path': str(output_path),
                'error': f'Error in pause-aware synthesis: {str(e)}',
                'success': False
            }
    
    def batch_synthesize_directory(self, translations_dir: Path, output_dir: Path = None,
                                 voice_settings: Dict = None, use_pause_aware: bool = True) -> List[Dict]:
        """
        Batch synthesize all translation files in a directory
        
        Args:
            translations_dir: Directory containing translation JSON files
            output_dir: Output directory for synthesis files
            voice_settings: Voice configuration settings
            use_pause_aware: Whether to use pause-aware synthesis for texts with pause markers
        """
        results = []
        
        for translation_file in translations_dir.glob("*_translations.json"):
            print(f"\nProcessing translations: {translation_file.name}")
            
            with open(translation_file, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            
            synthesis_results = self.synthesize_translation_results(
                translation_data, output_dir, voice_settings, use_pause_aware
            )
            results.append(synthesis_results)
        
        return results

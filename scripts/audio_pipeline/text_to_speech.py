"""
Google Text-to-Speech integration for high-quality speech synthesis
"""
from google.cloud import texttospeech
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
from pathlib import Path
import json
import os
from typing import Dict, List
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
                                     voice_settings: Dict = None) -> Dict:
        """
        Synthesize speech for all translated segments
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
            chinese_text = segment['chinese_text']
            
            print(f"Synthesizing segment {segment_id + 1}/{translation_data['total_segments']}")
            
            if chinese_text:
                # Create output filename in project subfolder
                output_filename = f"{base_filename}_segment_{segment_id:03d}_synthesis.mp3"
                output_path = project_synthesis_dir / output_filename
                
                synthesis_result = self.synthesize_text(
                    chinese_text, 
                    output_path,
                    **voice_settings
                )
                
                print(f"  → Text: {chinese_text[:50]}...")
                if synthesis_result['success']:
                    print(f"  → Saved: {output_path.name}")
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
                'chinese_text': chinese_text,
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
    
    def batch_synthesize_directory(self, translations_dir: Path, output_dir: Path = None,
                                 voice_settings: Dict = None) -> List[Dict]:
        """
        Batch synthesize all translation files in a directory
        """
        results = []
        
        for translation_file in translations_dir.glob("*_translations.json"):
            print(f"\nProcessing translations: {translation_file.name}")
            
            with open(translation_file, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            
            synthesis_results = self.synthesize_translation_results(
                translation_data, output_dir, voice_settings
            )
            results.append(synthesis_results)
        
        return results

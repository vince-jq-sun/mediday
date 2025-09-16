"""
Translation module supporting both Google Translate API and LLM-based translation
"""
from google.cloud import translate_v2 as translate
from pathlib import Path
import json
import os
from typing import Dict, List, Optional
from .config import SOURCE_LANGUAGE, TARGET_LANGUAGE, TRANSLATIONS_DIR
from .llm_translator import LLMTranslator

class Translator:
    def __init__(self, terminology_file: Optional[Path] = None, use_llm: bool = None):
        """
        Initialize translator with support for both Google Translate and LLM
        
        Args:
            terminology_file: Path to terminology JSON file
            use_llm: Whether to use LLM translation. If None, reads from environment
        """
        # Traditional Google Translate client
        self.client = translate.Client()
        self.terminology = {}
        
        # LLM translation setup
        if use_llm is None:
            translation_provider = os.getenv('TRANSLATION_PROVIDER', 'google').lower()
            use_llm = translation_provider != 'google'
        
        self.use_llm = use_llm
        self.llm_translator = None
        
        if self.use_llm:
            try:
                provider = os.getenv('TRANSLATION_PROVIDER', 'gemini')
                model = os.getenv('TRANSLATION_MODEL', 'gemini-2.0-flash-exp')
                self.llm_translator = LLMTranslator(provider, model, terminology_file)
                print(f"✅ LLM translator initialized: {provider} ({model})")
            except Exception as e:
                print(f"⚠️ LLM translator failed to initialize: {e}")
                print("   Falling back to Google Translate")
                self.use_llm = False
        
        if terminology_file and terminology_file.exists():
            self.load_terminology(terminology_file)
    
    def load_terminology(self, terminology_file: Path):
        """Load terminology dictionary from JSON file"""
        try:
            with open(terminology_file, 'r', encoding='utf-8') as f:
                self.terminology = json.load(f)
            print(f"Loaded {len(self.terminology)} terminology entries")
        except Exception as e:
            print(f"Error loading terminology: {e}")
            self.terminology = {}
    
    def apply_terminology(self, text: str) -> str:
        """Apply terminology replacements to text before translation"""
        processed_text = text
        for english_term, chinese_term in self.terminology.items():
            # Case-insensitive replacement
            processed_text = processed_text.replace(english_term, f"[TERM]{chinese_term}[/TERM]")
        return processed_text
    
    def post_process_translation(self, translation: str) -> str:
        """Post-process translation to restore terminology"""
        processed_translation = translation
        # Restore terminology markers
        processed_translation = processed_translation.replace("[TERM]", "").replace("[/TERM]", "")
        return processed_translation
    
    def translate_text(self, text: str, use_terminology: bool = True, context: str = "") -> Dict:
        """
        Translate text from English to Chinese using either Google Translate or LLM
        """
        if not text.strip():
            return {
                'original_text': text,
                'translated_text': '',
                'confidence': 0.0,
                'error': 'Empty text',
                'provider': 'llm' if self.use_llm else 'google'
            }
        
        # Use LLM translation if enabled
        if self.use_llm and self.llm_translator:
            return self.llm_translator.translate_text(text, context)
        
        # Fall back to Google Translate
        try:
            # Apply terminology if enabled
            processed_text = text
            if use_terminology and self.terminology:
                processed_text = self.apply_terminology(text)
            
            # Perform translation
            result = self.client.translate(
                processed_text,
                source_language=SOURCE_LANGUAGE,
                target_language=TARGET_LANGUAGE
            )
            
            translated_text = result['translatedText']
            
            # Post-process to restore terminology
            if use_terminology and self.terminology:
                translated_text = self.post_process_translation(translated_text)
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'detected_language': result.get('detectedSourceLanguage', SOURCE_LANGUAGE),
                'confidence': 1.0,  # Google Translate doesn't provide confidence scores
                'use_terminology': use_terminology,
                'provider': 'google'
            }
            
        except Exception as e:
            return {
                'original_text': text,
                'translated_text': '',
                'error': str(e),
                'confidence': 0.0,
                'provider': 'google'
            }
    
    def translate_transcription_results(self, transcription_data: Dict) -> Dict:
        """
        Translate all transcription results using either Google Translate or LLM
        """
        # Use LLM translation if enabled
        if self.use_llm and self.llm_translator:
            return self.llm_translator.translate_transcription_results(transcription_data, use_context=True)
        
        # Fall back to Google Translate
        results = {
            'original_file': transcription_data['original_file'],
            'total_segments': transcription_data['total_segments'],
            'translation_provider': 'google',
            'segments': []
        }
        
        for segment in transcription_data['segments']:
            print(f"Translating segment {segment['segment_id'] + 1}/{transcription_data['total_segments']}")
            
            transcription = segment['transcription']
            english_text = transcription.get('full_transcript', '')
            
            if english_text:
                translation_result = self.translate_text(english_text)
                print(f"  → EN: {english_text[:50]}...")
                print(f"  → ZH: {translation_result['translated_text'][:50]}...")
            else:
                translation_result = {
                    'original_text': '',
                    'translated_text': '',
                    'error': 'No transcription available',
                    'confidence': 0.0
                }
            
            segment_result = {
                'segment_id': segment['segment_id'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'english_text': english_text,
                'chinese_text': translation_result['translated_text'],
                'translation_metadata': translation_result
            }
            
            results['segments'].append(segment_result)
        
        # Save translation results
        output_path = TRANSLATIONS_DIR / f"{Path(transcription_data['original_file']).stem}_translations.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def retranslate_segment(self, text: str, use_terminology: bool = True) -> Dict:
        """
        Re-translate a single text segment (for GUI use)
        """
        return self.translate_text(text, use_terminology)
    
    def batch_translate_directory(self, transcripts_dir: Path) -> List[Dict]:
        """
        Batch translate all transcription files in a directory
        """
        results = []
        
        for transcript_file in transcripts_dir.glob("*_transcriptions.json"):
            print(f"\nProcessing transcriptions: {transcript_file.name}")
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcription_data = json.load(f)
            
            translation_results = self.translate_transcription_results(transcription_data)
            results.append(translation_results)
        
        return results

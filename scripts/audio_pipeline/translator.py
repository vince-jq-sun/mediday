"""
Translation module supporting Google Translate API, LLM-based translation, and GPT translation
"""
try:
    from google.cloud import translate_v2 as translate
except ImportError:
    translate = None
from pathlib import Path
import json
import os
from typing import Dict, List, Optional
from .config import SOURCE_LANGUAGE, TARGET_LANGUAGE, TRANSLATIONS_DIR, TRANSLATION_PROVIDER, USE_ENHANCED_GPT, GPT_MODEL
from .llm_translator import LLMTranslator
from .gpt_translator import GPTTranslator
from .enhanced_gpt_translator import EnhancedGPTTranslator

class Translator:
    def __init__(self, terminology_file: Optional[Path] = None, provider: str = None):
        """
        Initialize translator with support for multiple providers
        
        Args:
            terminology_file: Path to terminology JSON file
            provider: Translation provider ('google', 'llm', 'gpt'). If None, reads from environment
        """
        # Determine provider
        if provider is None:
            provider = os.getenv('TRANSLATION_PROVIDER', TRANSLATION_PROVIDER).lower()
        
        self.provider = provider
        self.terminology = {}
        
        # Initialize clients based on provider
        self.google_client = None
        self.llm_translator = None
        self.gpt_translator = None
        self.enhanced_gpt_translator = None
        
        if provider == 'gpt':
            try:
                model = os.getenv('GPT_MODEL', GPT_MODEL)
                # Check if enhanced GPT should be used
                use_enhanced = os.getenv('USE_ENHANCED_GPT', str(USE_ENHANCED_GPT).lower()).lower() == 'true'
                
                if use_enhanced:
                    self.enhanced_gpt_translator = EnhancedGPTTranslator(model=model, terminology_file=terminology_file)
                    print(f"✅ Enhanced GPT translator initialized: {model}")
                else:
                    self.gpt_translator = GPTTranslator(model=model, terminology_file=terminology_file)
                    print(f"✅ GPT translator initialized: {model}")
            except Exception as e:
                print(f"⚠️ GPT translator failed to initialize: {e}")
                print("   Falling back to Google Translate")
                self.provider = 'google'
        
        elif provider in ['llm', 'gemini', 'anthropic', 'local']:
            try:
                model = os.getenv('TRANSLATION_MODEL', 'gemini-2.0-flash-exp')
                self.llm_translator = LLMTranslator(provider, model, terminology_file)
                print(f"✅ LLM translator initialized: {provider} ({model})")
            except Exception as e:
                print(f"⚠️ LLM translator failed to initialize: {e}")
                print("   Falling back to Google Translate")
                self.provider = 'google'
        
        # Initialize Google Translate as fallback or primary
        if self.provider == 'google' or (not self.gpt_translator and not self.enhanced_gpt_translator and not self.llm_translator):
            self.google_client = translate.Client()
            self.provider = 'google'
            print("✅ Google Translate initialized")
        
        # Load terminology for Google Translate
        if terminology_file and terminology_file.exists() and self.provider == 'google':
            self.load_terminology(terminology_file)
    
    def load_terminology(self, terminology_file: Path):
        """Load terminology dictionary from JSON file"""
        try:
            with open(terminology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle flattened structure - exclude metadata
            self.terminology = {k: v for k, v in data.items() if not k.startswith('_')}
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
        Translate text using the configured provider
        """
        if not text.strip():
            return {
                'original_text': text,
                'translated_text': '',
                'confidence': 0.0,
                'error': 'Empty text',
                'provider': self.provider
            }
        
        # Use GPT translation (enhanced or regular)
        if self.provider == 'gpt':
            if self.enhanced_gpt_translator:
                return self.enhanced_gpt_translator.translate_text(text, context)
            elif self.gpt_translator:
                return self.gpt_translator.translate_text(text, context)
        
        # Use LLM translation
        if self.provider in ['llm', 'gemini', 'anthropic', 'local'] and self.llm_translator:
            return self.llm_translator.translate_text(text, context)
        
        # Fall back to Google Translate
        try:
            # Apply terminology if enabled
            processed_text = text
            if use_terminology and self.terminology:
                processed_text = self.apply_terminology(text)
            
            # Perform translation
            result = self.google_client.translate(
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
    
    def translate_transcription_results(self, transcription_data: Dict, output_dir: Path = None, use_context: bool = False,
                                       include_previous_translations: bool = True,
                                       context_window: int = 1) -> Dict:
        """
        Translate all transcription results using the configured provider
        """
        # Use GPT translation (enhanced or regular)
        if self.provider == 'gpt':
            if self.enhanced_gpt_translator:
                # Enhanced GPT translator doesn't have batch methods yet, use single translate
                return self._translate_with_enhanced_gpt(
                    transcription_data, use_context, include_previous_translations, context_window
                )
            elif self.gpt_translator:
                return self.gpt_translator.translate_transcription_results(
                    transcription_data, 
                    use_context=use_context,
                    include_previous_translations=include_previous_translations,
                    context_window=context_window
                )
        
        # Use LLM translation
        if self.provider in ['llm', 'gemini', 'anthropic', 'local'] and self.llm_translator:
            return self.llm_translator.translate_transcription_results(
                transcription_data, 
                use_context=use_context,
                include_previous_translations=include_previous_translations,
                context_window=context_window
            )
        
        # Fall back to Google Translate
        results = {
            'original_file': transcription_data['original_file'],
            'total_segments': transcription_data['total_segments'],
            'translation_provider': self.provider,
            'segments': []
        }
        
        for segment in transcription_data['segments']:
            print(f"Translating segment {segment['segment_id'] + 1}/{transcription_data['total_segments']}")
            
            transcription = segment.get('transcription', {})
            if not transcription:
                continue
            english_text = transcription.get('full_transcript', '') or ''
            
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
                'original_text': english_text,
                'translated_text': translation_result['translated_text'],
                'translation_metadata': {
                    'confidence': translation_result.get('confidence', 0.0),
                    'provider': translation_result.get('provider', ''),
                    'model': translation_result.get('model', ''),
                    'error': translation_result.get('error', ''),
                    'use_terminology': translation_result.get('use_terminology', False)
                }
            }
            results['segments'].append(segment_result)
        
        # Save translation results
        if output_dir is None or output_dir is False or not output_dir:
            output_dir = TRANSLATIONS_DIR
        else:
            # Clean and validate the provided output directory
            output_dir = str(output_dir).strip().replace('\n', '').replace('\r', '')
            if not output_dir:  # If empty after cleaning
                output_dir = TRANSLATIONS_DIR
        output_path = Path(output_dir) / f"{Path(transcription_data['original_file']).stem}_translations.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Enhanced GPT translations saved to: {output_path}")
        print(f"📊 Total tokens used: {total_tokens}")
        
        return results
    
    def _translate_with_enhanced_gpt(self, transcription_data: Dict, output_dir: Path = None, use_context: bool = False,
                                   include_previous_translations: bool = True,
                                   context_window: int = 1) -> Dict:
        """
        Translate transcription results using enhanced GPT translator
        """
        results = {
            'original_file': transcription_data['original_file'],
            'total_segments': transcription_data['total_segments'],
            'translation_provider': 'enhanced_openai_gpt',
            'translation_model': self.enhanced_gpt_translator.model,
            'segments': []
        }
        
        translations = []  # Store completed translations for context
        total_tokens = 0
        
        for i, segment in enumerate(transcription_data['segments']):
            print(f"Enhanced GPT translating segment {i + 1}/{transcription_data['total_segments']}")
            
            transcription = segment.get('transcription', {})
            if not transcription:
                translation_result = {
                    'original_text': '',
                    'translated_text': '',
                    'segment_id': segment.get('segment_id', i)
                }
                results.append(translation_result)
                continue
            english_text = transcription.get('full_transcript', '') or ''

            if not english_text:
                translation_result = {
                    'original_text': '',
                    'translated_text': '',
                    'error': 'No transcription available',
                    'confidence': 0.0,
                    'provider': 'enhanced_openai_gpt'
                }
            else:
                # Build context if enabled
                context = ""
                if use_context:
                    context_parts = []
                    
                    # Previous segments with translations
                    if include_previous_translations:
                        for j in range(max(0, i - context_window), i):
                            prev_segment = transcription_data['segments'][j]
                            prev_transcript = prev_segment.get('transcription', {})
                            if prev_transcript:
                                prev_en = prev_transcript.get('full_transcript', '') or ''
                                prev_en = prev_en.strip() if prev_en else ''
                                prev_zh = translations[j] if j < len(translations) else ''
                                
                                if prev_en:
                                    context_parts.append(f"前文段落 {j + 1}:")
                                    context_parts.append(f"  英文: {prev_en}")
                                    if prev_zh:
                                        context_parts.append(f"  中文: {prev_zh}")
                                    context_parts.append("")
                    
                    # Next segments (English only)
                    for j in range(i + 1, min(len(transcription_data['segments']), i + context_window + 1)):
                        next_segment = transcription_data['segments'][j]
                        next_transcript = next_segment.get('transcription', {})
                        if next_transcript:
                            next_text = next_transcript.get('full_transcript', '') or ''
                            next_text = next_text.strip() if next_text else ''
                            if next_text:
                                context_parts.append(f"后文段落 {j + 1}:")
                                context_parts.append(f"  英文: {next_text}")
                                context_parts.append("")
                    
                    context = "\n".join(context_parts).strip()
                
                translation_result = self.enhanced_gpt_translator.translate_text(english_text, context)
                
                # Store translation for future context
                translated_text = translation_result.get('translated_text', '')
                translations.append(translated_text)
                
                # Track token usage
                if 'tokens_used' in translation_result:
                    total_tokens += translation_result['tokens_used']
                
                print(f"  → EN: {english_text[:50]}...")
                print(f"  → ZH: {translated_text[:50]}...")
                if 'tokens_used' in translation_result:
                    print(f"  📊 Tokens: {translation_result['tokens_used']}")
            
            segment_result = {
                'segment_id': segment['segment_id'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'original_text': english_text,
                'translated_text': translation_result.get('translated_text', ''),
                'translation_metadata': {
                    'confidence': translation_result.get('confidence', 0.0),
                    'provider': translation_result.get('provider', ''),
                    'model': translation_result.get('model', ''),
                    'context_used': translation_result.get('context_used', False),
                    'terminology_applied': translation_result.get('terminology_applied', False),
                    'tokens_used': translation_result.get('tokens_used', 0),
                    'prompt_tokens': translation_result.get('prompt_tokens', 0),
                    'completion_tokens': translation_result.get('completion_tokens', 0),
                    'error': translation_result.get('error', '')
                }
            }
            
            results['segments'].append(segment_result)
        
        results['total_tokens_used'] = total_tokens
        
        # Save translation results
        if output_dir is None or output_dir is False or not output_dir:
            output_dir = TRANSLATIONS_DIR
        else:
            # Clean and validate the provided output directory
            output_dir = str(output_dir).strip().replace('\n', '').replace('\r', '')
            if not output_dir:  # If empty after cleaning
                output_dir = TRANSLATIONS_DIR
        output_path = Path(output_dir) / f"{Path(transcription_data['original_file']).stem}_translations.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Enhanced GPT translations saved to: {output_path}")
        print(f"📊 Total tokens used: {total_tokens}")
        
        return results
    
    def retranslate_segment(self, text: str, use_terminology: bool = True) -> Dict:
        """
        Re-translate a single text segment (for GUI use)
        Uses enhanced GPT mode with context window = 1 when available
        """
        # Use enhanced GPT translator with context window = 1 if available
        if self.provider == 'gpt' and self.enhanced_gpt_translator:
            # For retranslation, we use empty context but enable enhanced mode
            return self.enhanced_gpt_translator.translate_text(text, context="")
        
        # Fall back to regular translation
        return self.translate_text(text, use_terminology)
    
    def batch_translate_directory(self, transcripts_dir: Path, output_dir: Path = None, use_context: bool = False, 
                                 include_previous_translations: bool = True, 
                                 context_window: int = 1) -> List[Dict]:
        """
        Batch translate all transcription files in a directory
        
        Args:
            transcripts_dir: Directory containing transcription files
            use_context: Whether to use context for translation (for GPT/LLM providers)
            include_previous_translations: Whether to include previous translations in context
            context_window: Number of previous segments to include as context
        """
        results = []
        
        for transcript_file in transcripts_dir.glob("*_transcriptions.json"):
            print(f"\nProcessing transcriptions: {transcript_file.name}")
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcription_data = json.load(f)
            
            # Pass context parameters to GPT/LLM translators
            if self.provider == 'gpt':
                if self.enhanced_gpt_translator:
                    translation_results = self._translate_with_enhanced_gpt(
                        transcription_data, output_dir, use_context, include_previous_translations, context_window
                    )
                elif self.gpt_translator:
                    translation_results = self.gpt_translator.translate_transcription_results(
                        transcription_data, 
                        use_context=use_context,
                        include_previous_translations=include_previous_translations,
                        context_window=context_window
                    )
            elif self.provider in ['llm', 'gemini', 'anthropic', 'local'] and self.llm_translator:
                translation_results = self.llm_translator.translate_transcription_results(
                    transcription_data, 
                    use_context=use_context,
                    include_previous_translations=include_previous_translations,
                    context_window=context_window
                )
            else:
                # Google Translate doesn't use context
                translation_results = self.translate_transcription_results(transcription_data)
            
            results.append(translation_results)
        
        return results

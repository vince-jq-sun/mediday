"""
GPT-based translation module specifically optimized for mindfulness meditation content
Uses OpenAI GPT models with detailed prompts and terminology integration
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import time
from openai import OpenAI
from .config import SOURCE_LANGUAGE, TARGET_LANGUAGE, TRANSLATIONS_DIR

class GPTTranslator:
    def __init__(self, model: str = "gpt-4.1-mini", terminology_file: Optional[Path] = None, api_key: Optional[str] = None):
        """
        Initialize GPT translator for mindfulness content
        
        Args:
            model: GPT model to use (default: gpt-4.1-mini)
            terminology_file: Path to terminology JSON file
            api_key: OpenAI API key (if not provided, reads from environment)
        """
        self.model = model
        self.terminology = {}
        
        # Load API key
        if api_key:
            self.api_key = api_key
        else:
            # Try to load from config file first
            self.api_key = self._load_api_key_from_config()
            if not self.api_key:
                self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or provide in config file.")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Load terminology
        if terminology_file and terminology_file.exists():
            self.load_terminology(terminology_file)
        
        print(f"✅ GPT translator initialized with model: {self.model}")
        if self.terminology:
            print(f"✅ Loaded {len(self.terminology)} terminology entries")
    
    def _load_api_key_from_config(self) -> Optional[str]:
        """Load OpenAI API key from config file"""
        config_path = Path(__file__).parent.parent.parent / 'config' / 'openai.json'
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get('api')
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    def load_terminology(self, terminology_file: Path):
        """Load terminology dictionary from JSON file"""
        try:
            with open(terminology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle flattened structure - exclude metadata
            self.terminology = {k: v for k, v in data.items() if not k.startswith('_')}
            print(f"✅ Loaded {len(self.terminology)} terminology entries for GPT translation")
        except Exception as e:
            print(f"⚠️ Error loading terminology: {e}")
            self.terminology = {}
    
    def _create_translation_prompt(self, text: str, context: str = "") -> str:
        """Create a detailed prompt for GPT translation with specific requirements"""
        
        # Format terminology for the prompt
        terminology_section = ""
        if self.terminology:
            terminology_items = []
            for en, zh in self.terminology.items():
                terminology_items.append(f"  • {en} → {zh}")
            
            terminology_section = f"""
**重要术语对照表**：
{chr(10).join(terminology_items)}

请在翻译时严格按照上述术语对照表进行翻译，确保术语的准确性和一致性。
"""

        # Context section with error detection
        context_section = ""
        if context.strip():
            context_section = f"""
**上下文信息**：
{context}

**上下文使用指导**：
- 参考上下文理解语义连贯性和术语一致性
- 如果发现上下文中的中文翻译有明显错误或不自然，请忽略错误部分，以术语对照表和英文原文为准
- 优先保证当前段落翻译的准确性，不要被上下文中的错误影响
- 保持正念冥想内容的专业性和自然性
"""

        prompt = f"""你是一位专业的正念冥想翻译专家，精通英文和中文，对佛教、冥想、正念修行有深入理解。

**翻译任务**：把正念指导语翻译为简体中文

**翻译要求**：
1. **准确性**：准确传达原文的意思和意境，不遗漏重要信息
2. **自然性**：兼顾准确与语言的自然，使用自然流畅的中文表达，避免翻译腔
3. **专业性**：正确使用正念冥想的专业术语，保持术语一致性
4. **情感传达**：保持原文的温和、平静、引导性语调
5. **文化适应**：适当调整表达方式以符合中文语境和表达习惯
6. **错误防护**：如果上下文中存在明显的翻译错误，请基于英文原文和术语表进行独立判断，不要延续错误
7. **格式要求**：输出的翻译结果前后加大括号，格式为：{{翻译内容}}

{terminology_section}{context_section}
**待翻译文本**：
{text}

**重要提醒**：
- 术语对照表具有最高优先级，任何与术语表冲突的上下文翻译都应忽略
- 保持独立思考，不要盲目跟随可能存在错误的上下文翻译
- 确保翻译符合正念冥想的专业标准和自然的中文表达

请严格按照上述要求进行翻译，只返回带大括号的翻译结果，不要包含其他解释或说明。"""

        return prompt
    
    def _validate_translation_quality(self, original_text: str, translated_text: str) -> Dict:
        """
        Validate translation quality to detect potential errors
        
        Args:
            original_text: Original English text
            translated_text: Translated Chinese text
            
        Returns:
            Dict with validation results and quality score
        """
        validation_result = {
            'quality_score': 1.0,
            'warnings': [],
            'is_valid': True
        }
        
        # Check for obvious errors
        if not translated_text or translated_text.strip() == '':
            validation_result['warnings'].append('Empty translation')
            validation_result['quality_score'] = 0.0
            validation_result['is_valid'] = False
            return validation_result
        
        # Check for untranslated English words (except proper nouns)
        english_words = set(original_text.lower().split())
        chinese_text_lower = translated_text.lower()
        
        # Common English words that shouldn't appear in Chinese translation
        problematic_words = ['the', 'and', 'you', 'your', 'this', 'that', 'with', 'for', 'are', 'is', 'be', 'to', 'of', 'in', 'on', 'at']
        found_english = [word for word in problematic_words if word in chinese_text_lower]
        
        if found_english:
            validation_result['warnings'].append(f'Contains untranslated English words: {", ".join(found_english)}')
            validation_result['quality_score'] -= 0.3
        
        # Check for terminology consistency (improved)
        if self.terminology:
            for en_term, zh_term in self.terminology.items():
                if en_term.lower() in original_text.lower():
                    # Handle multiple options (comma-separated or | separated)
                    zh_options = []
                    if ',' in zh_term:
                        zh_options = [opt.strip() for opt in zh_term.split(',')]
                    elif '|' in zh_term:
                        zh_options = [opt.strip().split('[')[0].strip() for opt in zh_term.split('|')]
                    else:
                        zh_options = [zh_term]
                    
                    # More flexible terminology checking
                    term_found = False
                    for opt in zh_options:
                        # Check for exact match or partial match for compound terms
                        if opt in translated_text:
                            term_found = True
                            break
                        # For compound terms like "正念的", also check for "正念"
                        if len(opt) > 2 and opt.endswith('的'):
                            base_term = opt[:-1]  # Remove "的"
                            if base_term in translated_text:
                                term_found = True
                                break
                    
                    if not term_found:
                        # Only warn for critical terms, not all terms
                        critical_terms = ['mindfulness', 'meditation', 'awareness', 'present moment', 'breathing']
                        if en_term.lower() in critical_terms:
                            validation_result['warnings'].append(f'Missing critical terminology: "{en_term}" should include one of: {", ".join(zh_options)}')
                            validation_result['quality_score'] -= 0.15  # Reduced penalty
                        else:
                            # Minor penalty for non-critical terms
                            validation_result['quality_score'] -= 0.05
        
        # Check length ratio (adjusted for Chinese-English differences)
        length_ratio = len(translated_text) / len(original_text) if len(original_text) > 0 else 0
        # Chinese is typically 0.2-0.8 times the length of English
        if length_ratio < 0.15:  # Very short
            validation_result['warnings'].append('Translation seems unusually short')
            validation_result['quality_score'] -= 0.15
        elif length_ratio > 4.0:  # Very long
            validation_result['warnings'].append('Translation seems unusually long')
            validation_result['quality_score'] -= 0.1
        # Remove the 0.3 threshold as it's too strict for Chinese
        
        # Final quality assessment
        if validation_result['quality_score'] < 0.5:
            validation_result['is_valid'] = False
        
        return validation_result
    
    def translate_text(self, text: str, context: str = "", temperature: float = 0.3) -> Dict:
        """
        Translate text using GPT with mindfulness-specific prompts
        
        Args:
            text: Text to translate
            context: Additional context for better translation
            temperature: GPT temperature (0.3 for more consistent translations)
            
        Returns:
            Dict with translation result and metadata
        """
        if not text.strip():
            return {
                'original_text': text,
                'translated_text': '',
                'confidence': 0.0,
                'error': 'Empty text',
                'provider': 'openai_gpt',
                'model': self.model
            }
        
        try:
            prompt = self._create_translation_prompt(text, context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一位专业的正念冥想翻译专家。请严格按照用户要求进行翻译，确保术语准确、语言自然。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000,
                presence_penalty=0.1,  # Slightly encourage diverse vocabulary
                frequency_penalty=0.1   # Slightly reduce repetition
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Extract content from brackets if present
            if translated_text.startswith('{') and translated_text.endswith('}'):
                translated_text = translated_text[1:-1].strip()
            
            # Validate translation quality
            validation = self._validate_translation_quality(text, translated_text)
            
            result = {
                'original_text': text,
                'translated_text': translated_text,
                'confidence': 0.95 * validation['quality_score'],  # Adjust confidence based on quality
                'provider': 'openai_gpt',
                'model': self.model,
                'context_used': bool(context.strip()),
                'terminology_applied': bool(self.terminology),
                'tokens_used': response.usage.total_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'quality_validation': validation
            }
            
            # Log quality warnings if any
            if validation['warnings']:
                print(f"   ⚠️ Quality warnings: {'; '.join(validation['warnings'])}")
                print(f"   📊 Quality score: {validation['quality_score']:.2f}")
            
            return result
            
        except Exception as e:
            return {
                'original_text': text,
                'translated_text': '',
                'error': str(e),
                'confidence': 0.0,
                'provider': 'openai_gpt',
                'model': self.model
            }
    
    def translate_with_context(self, segments: List[Dict], context_window: int = 1, include_previous_translations: bool = True) -> List[Dict]:
        """
        Translate segments with enhanced context including previous translations
        
        Args:
            segments: List of segment dictionaries with 'english_text'
            context_window: Number of surrounding segments to include as context
            include_previous_translations: Whether to include previous Chinese translations in context
            
        Returns:
            List of segments with GPT translations
        """
        results = []
        translations = []  # Store completed translations for context
        
        for i, segment in enumerate(segments):
            english_text = segment.get('english_text', '')
            
            if not english_text.strip():
                segment['gpt_translation'] = {
                    'translated_text': '',
                    'error': 'No English text',
                    'confidence': 0.0
                }
                results.append(segment)
                translations.append('')  # Add empty translation to maintain index alignment
                continue
            
            # Build enhanced context
            context_parts = []
            
            # Previous segments with translations (if available and enabled)
            if include_previous_translations:
                for j in range(max(0, i - context_window), i):
                    prev_en = segments[j].get('english_text', '').strip()
                    prev_zh = translations[j] if j < len(translations) else ''
                    
                    if prev_en:
                        context_parts.append(f"前文段落 {j + 1}:")
                        context_parts.append(f"  英文: {prev_en}")
                        if prev_zh:
                            context_parts.append(f"  中文: {prev_zh}")
                        context_parts.append("")  # Empty line for readability
            else:
                # Original behavior - English only
                for j in range(max(0, i - context_window), i):
                    prev_text = segments[j].get('english_text', '').strip()
                    if prev_text:
                        context_parts.append(f"前文：{prev_text}")
            
            # Next segments (English only)
            for j in range(i + 1, min(len(segments), i + context_window + 1)):
                next_text = segments[j].get('english_text', '').strip()
                if next_text:
                    if include_previous_translations:
                        context_parts.append(f"后文段落 {j + 1}:")
                        context_parts.append(f"  英文: {next_text}")
                        context_parts.append("")  # Empty line for readability
                    else:
                        context_parts.append(f"后文：{next_text}")
            
            context = "\n".join(context_parts).strip() if context_parts else ""
            
            # Display context info
            prev_segments = min(i, context_window)
            next_segments = min(len(segments) - i - 1, context_window)
            total_context_segments = prev_segments + next_segments
            
            print(f"🤖 GPT translating segment {i + 1}/{len(segments)}")
            print(f"   📖 Context: {prev_segments} previous + {next_segments} next = {total_context_segments} segments")
            if include_previous_translations and prev_segments > 0:
                print(f"   🔄 Previous translations included: Yes")
            
            translation_result = self.translate_text(english_text, context)
            
            if translation_result.get('translated_text'):
                translated_text = translation_result['translated_text']
                translations.append(translated_text)  # Store for future context
                print(f"   ✅ {translated_text[:50]}...")
                if 'tokens_used' in translation_result:
                    print(f"   📊 Tokens used: {translation_result['tokens_used']}")
            else:
                translations.append('')  # Add empty translation to maintain index alignment
                print(f"   ❌ {translation_result.get('error', 'Unknown error')}")
            
            # Add context metadata to the result
            translation_result['context_metadata'] = {
                'context_segments_used': total_context_segments,
                'previous_translations_included': include_previous_translations and prev_segments > 0,
                'context_window': context_window
            }
            
            segment['gpt_translation'] = translation_result
            results.append(segment)
            
            # Rate limiting to avoid API limits
            time.sleep(0.5)
        
        return results
    
    def translate_transcription_results(self, transcription_data: Dict, use_context: bool = True, include_previous_translations: bool = True, context_window: int = 1) -> Dict:
        """
        Translate all transcription results using GPT
        
        Args:
            transcription_data: Transcription data from speech recognition
            use_context: Whether to use surrounding segments as context
            
        Returns:
            Translation results with GPT translations
        """
        results = {
            'original_file': transcription_data['original_file'],
            'total_segments': transcription_data['total_segments'],
            'translation_provider': 'openai_gpt',
            'translation_model': self.model,
            'segments': []
        }
        
        # Prepare segments for context-aware translation
        segments_for_translation = []
        for segment in transcription_data['segments']:
            segments_for_translation.append({
                'segment_id': segment['segment_id'],
                'english_text': segment['transcription'].get('full_transcript', ''),
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path']
            })
        
        # Translate with or without context
        if use_context:
            translated_segments = self.translate_with_context(
                segments_for_translation, 
                context_window=context_window,
                include_previous_translations=include_previous_translations
            )
        else:
            translated_segments = []
            for segment in segments_for_translation:
                translation_result = self.translate_text(segment['english_text'])
                segment['gpt_translation'] = translation_result
                translated_segments.append(segment)
        
        # Format results
        total_tokens = 0
        for segment in translated_segments:
            gpt_translation = segment.get('gpt_translation', {})
            
            segment_result = {
                'segment_id': segment['segment_id'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'english_text': segment['english_text'],
                'chinese_text': gpt_translation.get('translated_text', ''),
                'translation_metadata': gpt_translation
            }
            
            # Track token usage
            if 'tokens_used' in gpt_translation:
                total_tokens += gpt_translation['tokens_used']
            
            results['segments'].append(segment_result)
        
        results['total_tokens_used'] = total_tokens
        
        # Save translation results
        output_path = TRANSLATIONS_DIR / f"{Path(transcription_data['original_file']).stem}_gpt_translations.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 GPT translations saved to: {output_path}")
        print(f"📊 Total tokens used: {total_tokens}")
        
        return results
    
    def batch_translate_directory(self, transcripts_dir: Path, use_context: bool = True, include_previous_translations: bool = True, context_window: int = 1) -> List[Dict]:
        """
        Batch translate all transcription files in a directory using GPT
        """
        results = []
        total_tokens_all = 0
        
        for transcript_file in transcripts_dir.glob("*_transcriptions.json"):
            print(f"\n🤖 GPT processing transcriptions: {transcript_file.name}")
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcription_data = json.load(f)
            
            translation_results = self.translate_transcription_results(
                transcription_data, 
                use_context=use_context,
                include_previous_translations=include_previous_translations,
                context_window=context_window
            )
            results.append(translation_results)
            
            if 'total_tokens_used' in translation_results:
                total_tokens_all += translation_results['total_tokens_used']
        
        print(f"\n🎉 Batch translation completed!")
        print(f"📊 Total tokens used across all files: {total_tokens_all}")
        
        return results
    
    def estimate_cost(self, text: str) -> Dict:
        """
        Estimate the cost of translating given text
        
        Args:
            text: Text to estimate cost for
            
        Returns:
            Dict with cost estimation
        """
        # Rough token estimation (1 token ≈ 4 characters for English)
        estimated_input_tokens = len(text) // 4
        
        # Add prompt overhead (approximately 500-800 tokens for our detailed prompt)
        prompt_overhead = 700
        if self.terminology:
            prompt_overhead += len(str(self.terminology)) // 4
        
        total_input_tokens = estimated_input_tokens + prompt_overhead
        estimated_output_tokens = estimated_input_tokens * 1.2  # Chinese is typically longer
        
        # GPT-4o pricing (as of 2024)
        input_cost_per_1k = 0.005  # $0.005 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
        
        input_cost = (total_input_tokens / 1000) * input_cost_per_1k
        output_cost = (estimated_output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            'estimated_input_tokens': total_input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'estimated_total_tokens': total_input_tokens + estimated_output_tokens,
            'estimated_cost_usd': round(total_cost, 4),
            'input_cost_usd': round(input_cost, 4),
            'output_cost_usd': round(output_cost, 4),
            'model': self.model
        }

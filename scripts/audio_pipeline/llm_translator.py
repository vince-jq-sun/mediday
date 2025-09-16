"""
LLM-based translation module for more natural and fluent translations
Supports multiple LLM providers: OpenAI, Anthropic, Google Gemini, local models
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import time
from .config import SOURCE_LANGUAGE, TARGET_LANGUAGE, TRANSLATIONS_DIR

class LLMTranslator:
    def __init__(self, provider: str = "openai", model: str = None, terminology_file: Path = None):
        """
        Initialize LLM translator
        
        Args:
            provider: LLM provider ("openai", "anthropic", "gemini", "local")
            model: Specific model name
            terminology_file: Path to terminology JSON file
        """
        self.provider = provider.lower()
        self.model = model
        self.terminology = {}
        self.client = None
        
        if terminology_file and terminology_file.exists():
            self.load_terminology(terminology_file)
        
        self._initialize_client()
    
    def load_terminology(self, terminology_file: Path):
        """Load terminology dictionary from JSON file"""
        try:
            with open(terminology_file, 'r', encoding='utf-8') as f:
                self.terminology = json.load(f)
            print(f"✅ Loaded {len(self.terminology)} terminology entries for LLM translation")
        except Exception as e:
            print(f"⚠️ Error loading terminology: {e}")
            self.terminology = {}
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        try:
            if self.provider == "openai":
                import openai
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.model = self.model or "gpt-4o"
                print(f"✅ OpenAI client initialized with model: {self.model}")
            
            elif self.provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                self.model = self.model or "claude-3-5-sonnet-20241022"
                print(f"✅ Anthropic client initialized with model: {self.model}")
            
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
                self.client = genai.GenerativeModel(self.model or "gemini-2.0-flash-exp")
                self.model = self.model or "gemini-2.0-flash-exp"
                print(f"✅ Gemini client initialized with model: {self.model}")
            
            elif self.provider == "local":
                # For local models like Ollama
                import requests
                self.base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
                self.model = self.model or "llama3.1:8b"
                print(f"✅ Local LLM configured: {self.base_url} with model: {self.model}")
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except ImportError as e:
            print(f"❌ Failed to import {self.provider} library: {e}")
            print(f"   Install with: pip install {self._get_package_name()}")
            raise
        except Exception as e:
            print(f"❌ Failed to initialize {self.provider} client: {e}")
            raise
    
    def _get_package_name(self) -> str:
        """Get the package name for installation"""
        packages = {
            "openai": "openai",
            "anthropic": "anthropic", 
            "gemini": "google-generativeai",
            "local": "requests"
        }
        return packages.get(self.provider, "")
    
    def _create_translation_prompt(self, text: str, context: str = "") -> str:
        """Create a detailed prompt for LLM translation"""
        terminology_context = ""
        if self.terminology:
            terminology_context = f"""
重要术语对照表：
{json.dumps(self.terminology, ensure_ascii=False, indent=2)}

请在翻译时准确使用这些术语对照。
"""
        
        prompt = f"""你是一位专业的正念冥想翻译专家，精通英文和中文，对佛教、冥想、正念修行有深入理解。

请将以下英文正念冥想指导翻译成自然流畅的中文。要求：

1. **准确性**：准确传达原文的意思和意境
2. **自然性**：使用自然流畅的中文表达，避免翻译腔
3. **专业性**：正确使用正念冥想的专业术语
4. **情感传达**：保持原文的温和、平静、引导性语调
5. **文化适应**：适当调整表达方式以符合中文语境

{terminology_context}

{f"上下文：{context}" if context else ""}

请翻译以下文本：
{text}

请只返回翻译结果，不要包含其他解释或说明。"""

        return prompt
    
    def translate_text(self, text: str, context: str = "") -> Dict:
        """
        Translate text using LLM
        
        Args:
            text: Text to translate
            context: Additional context for better translation
            
        Returns:
            Dict with translation result and metadata
        """
        if not text.strip():
            return {
                'original_text': text,
                'translated_text': '',
                'confidence': 0.0,
                'error': 'Empty text',
                'provider': self.provider,
                'model': self.model
            }
        
        try:
            prompt = self._create_translation_prompt(text, context)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional mindfulness meditation translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more consistent translations
                    max_tokens=2000
                )
                translated_text = response.choices[0].message.content.strip()
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                translated_text = response.content[0].text.strip()
                
            elif self.provider == "gemini":
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 2000,
                    }
                )
                translated_text = response.text.strip()
                
            elif self.provider == "local":
                import requests
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 2000
                        }
                    },
                    timeout=120
                )
                response.raise_for_status()
                translated_text = response.json()["response"].strip()
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'confidence': 0.95,  # LLM translations are generally high quality
                'provider': self.provider,
                'model': self.model,
                'context_used': bool(context),
                'terminology_applied': bool(self.terminology)
            }
            
        except Exception as e:
            return {
                'original_text': text,
                'translated_text': '',
                'error': str(e),
                'confidence': 0.0,
                'provider': self.provider,
                'model': self.model
            }
    
    def translate_with_context(self, segments: List[Dict], context_window: int = 2) -> List[Dict]:
        """
        Translate segments with context from surrounding segments
        
        Args:
            segments: List of segment dictionaries with 'english_text'
            context_window: Number of surrounding segments to include as context
            
        Returns:
            List of segments with LLM translations
        """
        results = []
        
        for i, segment in enumerate(segments):
            english_text = segment.get('english_text', '')
            
            if not english_text.strip():
                segment['llm_translation'] = {
                    'translated_text': '',
                    'error': 'No English text',
                    'confidence': 0.0
                }
                results.append(segment)
                continue
            
            # Build context from surrounding segments
            context_parts = []
            
            # Previous segments
            for j in range(max(0, i - context_window), i):
                prev_text = segments[j].get('english_text', '').strip()
                if prev_text:
                    context_parts.append(f"前文：{prev_text}")
            
            # Next segments
            for j in range(i + 1, min(len(segments), i + context_window + 1)):
                next_text = segments[j].get('english_text', '').strip()
                if next_text:
                    context_parts.append(f"后文：{next_text}")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            print(f"🤖 LLM translating segment {i + 1}/{len(segments)}")
            translation_result = self.translate_text(english_text, context)
            
            if translation_result.get('translated_text'):
                print(f"   ✅ {translation_result['translated_text'][:50]}...")
            else:
                print(f"   ❌ {translation_result.get('error', 'Unknown error')}")
            
            segment['llm_translation'] = translation_result
            results.append(segment)
            
            # Rate limiting to avoid API limits
            time.sleep(0.5)
        
        return results
    
    def translate_transcription_results(self, transcription_data: Dict, use_context: bool = True) -> Dict:
        """
        Translate all transcription results using LLM
        
        Args:
            transcription_data: Transcription data from speech recognition
            use_context: Whether to use surrounding segments as context
            
        Returns:
            Translation results with LLM translations
        """
        results = {
            'original_file': transcription_data['original_file'],
            'total_segments': transcription_data['total_segments'],
            'translation_provider': self.provider,
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
            translated_segments = self.translate_with_context(segments_for_translation)
        else:
            translated_segments = []
            for segment in segments_for_translation:
                translation_result = self.translate_text(segment['english_text'])
                segment['llm_translation'] = translation_result
                translated_segments.append(segment)
        
        # Format results
        for segment in translated_segments:
            llm_translation = segment.get('llm_translation', {})
            
            segment_result = {
                'segment_id': segment['segment_id'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'english_text': segment['english_text'],
                'chinese_text': llm_translation.get('translated_text', ''),
                'translation_metadata': llm_translation
            }
            
            results['segments'].append(segment_result)
        
        # Save translation results
        output_path = TRANSLATIONS_DIR / f"{Path(transcription_data['original_file']).stem}_llm_translations.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def batch_translate_directory(self, transcripts_dir: Path, use_context: bool = True) -> List[Dict]:
        """
        Batch translate all transcription files in a directory using LLM
        """
        results = []
        
        for transcript_file in transcripts_dir.glob("*_transcriptions.json"):
            print(f"\n🤖 LLM processing transcriptions: {transcript_file.name}")
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcription_data = json.load(f)
            
            translation_results = self.translate_transcription_results(transcription_data, use_context)
            results.append(translation_results)
        
        return results

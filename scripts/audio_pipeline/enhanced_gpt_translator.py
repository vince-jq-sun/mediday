"""
Enhanced GPT-based translation module with improved terminology handling
Supports both simple and structured terminology formats
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import time
from openai import OpenAI
from .config import SOURCE_LANGUAGE, TARGET_LANGUAGE, TRANSLATIONS_DIR

class EnhancedGPTTranslator:
    def __init__(self, model: str = "gpt-4o", terminology_file: Optional[Path] = None, api_key: Optional[str] = None):
        """
        Initialize enhanced GPT translator with better terminology support
        
        Args:
            model: GPT model to use (default: gpt-4o)
            terminology_file: Path to terminology JSON file (supports both simple and structured formats)
            api_key: OpenAI API key (if not provided, reads from environment)
        """
        self.model = model
        self.terminology = {}
        self.structured_terminology = {}
        
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
        
        print(f"✅ Enhanced GPT translator initialized with model: {self.model}")
        if self.terminology or self.structured_terminology:
            total_terms = len(self.terminology) + len(self.structured_terminology)
            print(f"✅ Loaded {total_terms} terminology entries")
    
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
        """Load terminology dictionary from JSON file (supports both simple and structured formats)"""
        try:
            with open(terminology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Separate simple and structured terminology
            self.terminology = {}
            self.structured_terminology = {}
            
            for key, value in data.items():
                if key.startswith('_'):  # Skip metadata
                    continue
                
                if isinstance(value, dict) and 'options' in value:
                    # Structured terminology
                    self.structured_terminology[key] = value
                elif isinstance(value, str):
                    # Simple terminology (including comma-separated values)
                    self.terminology[key] = value
            
            total_terms = len(self.terminology) + len(self.structured_terminology)
            print(f"✅ Loaded {total_terms} terminology entries ({len(self.structured_terminology)} structured)")
            
        except Exception as e:
            print(f"⚠️ Error loading terminology: {e}")
            self.terminology = {}
            self.structured_terminology = {}
    
    def _format_terminology_for_prompt(self) -> str:
        """Format terminology for GPT prompt with enhanced instructions"""
        if not self.terminology and not self.structured_terminology:
            return ""
        
        terminology_items = []
        
        # Simple terminology
        for en, zh in self.terminology.items():
            if ',' in zh:
                # Handle comma-separated options
                options = [opt.strip() for opt in zh.split(',')]
                terminology_items.append(f"  • {en} → {options[0]} (首选) | {' | '.join(options[1:])} (备选)")
            else:
                terminology_items.append(f"  • {en} → {zh}")
        
        # Structured terminology
        for en, data in self.structured_terminology.items():
            options = data.get('options', [])
            default = data.get('default', options[0] if options else '')
            context_hints = data.get('context_hints', {})
            
            if len(options) > 1:
                option_text = f"{default} (首选)"
                for opt in options:
                    if opt != default:
                        hint = context_hints.get(opt, '')
                        option_text += f" | {opt}"
                        if hint:
                            option_text += f" ({hint})"
                terminology_items.append(f"  • {en} → {option_text}")
            else:
                terminology_items.append(f"  • {en} → {default}")
        
        return f"""
**重要术语对照表**：
{chr(10).join(terminology_items)}

**术语使用说明**：
- 当术语有多个选项时，请根据上下文选择最合适的翻译
- 首选选项适用于大多数情况，备选选项适用于特定语境
- 确保术语翻译的一致性和准确性
"""
    
    def _create_enhanced_translation_prompt(self, text: str, context: str = "") -> str:
        """Create an enhanced prompt with better terminology handling"""
        
        terminology_section = self._format_terminology_for_prompt()
        
        # Context section
        context_section = ""
        if context.strip():
            context_section = f"""
**上下文信息**：
{context}

请结合上下文进行翻译，确保语义连贯。
"""

        prompt = f"""你是一位专业的正念冥想翻译专家，精通英文和中文，对佛教、冥想、正念修行有深入理解。

**翻译任务**：把正念指导语翻译为简体中文

**翻译要求**：
1. **准确性**：准确传达原文的意思和意境，不遗漏重要信息
2. **自然性**：兼顾准确与语言的自然，使用自然流畅的中文表达，避免翻译腔
3. **专业性**：正确使用正念冥想的专业术语，保持术语一致性
4. **情感传达**：保持原文的温和、平静、引导性语调
5. **文化适应**：适当调整表达方式以符合中文语境和表达习惯
6. **术语选择**：当术语有多个翻译选项时，根据上下文选择最合适的翻译
7. **格式要求**：输出的翻译结果前后加大括号，格式为：{{翻译内容}}
8. **停顿标记**：原文中的停顿通过 <...> 标记，请直接保留在译文中的相应位置

{terminology_section}{context_section}
**待翻译文本**：
{text}

请严格按照上述要求进行翻译，根据上下文智能选择最合适的术语翻译，只返回带大括号的翻译结果，不要包含其他解释或说明。"""

        return prompt
    
    def translate_text(self, text: str, context: str = "", temperature: float = 0.3) -> Dict:
        """
        Translate text using enhanced GPT with better terminology handling
        """
        if not text.strip():
            return {
                'original_text': text,
                'translated_text': '',
                'confidence': 0.0,
                'error': 'Empty text',
                'provider': 'enhanced_openai_gpt',
                'model': self.model
            }
        
        try:
            prompt = self._create_enhanced_translation_prompt(text, context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一位专业的正念冥想翻译专家。请严格按照用户要求进行翻译，智能选择最合适的术语翻译，确保术语准确、语言自然。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Extract content from brackets if present
            if translated_text.startswith('{') and translated_text.endswith('}'):
                translated_text = translated_text[1:-1].strip()
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'confidence': 0.95,
                'provider': 'enhanced_openai_gpt',
                'model': self.model,
                'context_used': bool(context.strip()),
                'terminology_applied': bool(self.terminology or self.structured_terminology),
                'tokens_used': response.usage.total_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens
            }
            
        except Exception as e:
            return {
                'original_text': text,
                'translated_text': '',
                'error': str(e),
                'confidence': 0.0,
                'provider': 'enhanced_openai_gpt',
                'model': self.model
            }

#!/usr/bin/env python3
"""
Test script for Enhanced GPT-based translation with improved context handling
Tests context-aware translation with previous translations included in context
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import with proper module path
from scripts.audio_pipeline.enhanced_gpt_translator import EnhancedGPTTranslator
from scripts.audio_pipeline.config import TRANSLATIONS_DIR

# Configuration - modify these as needed
GPT_MODEL = "gpt-4.1-mini"  # Options: "gpt-4.1", "gpt-4.1-mini"
TERMINOLOGY_FILE = "terminology_enhanced_simple.json"
CONTEXT_WINDOW = 1  # Number of surrounding segments to include

def test_enhanced_gpt_translation_v2():
    """Test Enhanced GPT translation with improved context including previous translations"""
    print("Enhanced GPT Translation Test V2 - Improved Context Mode")
    print("=" * 65)
    print(f"Model: {GPT_MODEL}")
    print(f"Terminology: {TERMINOLOGY_FILE}")
    print(f"Context Window: {CONTEXT_WINDOW}")
    print()
    
    # Load terminology file
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / TERMINOLOGY_FILE
    
    # Test texts
    test_texts = [
        "Remind yourself. That you're here. You're awake and aware. And spend this first few moments of the meditation just settling. And sensing into being here. Sense of being awake in the midst of this moment.",
        "Take a moment to notice your breathing. Feel the natural rhythm of your breath. There's no need to change anything, just observe.",
        "Allow your attention to rest in the present moment. Notice any thoughts that arise, and gently let them pass like clouds in the sky."
    ]
    
    # Prepare results structure
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'model_used': GPT_MODEL,
        'terminology_file': TERMINOLOGY_FILE,
        'context_window': CONTEXT_WINDOW,
        'context_strategy': 'include_previous_translations',
        'terminology_loaded': False,
        'context_aware_translations': [],
        'total_tokens_used': 0
    }
    
    try:
        # Initialize Enhanced GPT translator
        print(f"🤖 Initializing Enhanced GPT translator...")
        translator = EnhancedGPTTranslator(
            model=GPT_MODEL,
            terminology_file=terminology_file
        )
        
        print(f"✅ Enhanced GPT translator initialized successfully")
        
        # Check terminology loading
        simple_terms = len(translator.terminology)
        structured_terms = len(translator.structured_terminology)
        total_terms = simple_terms + structured_terms
        
        print(f"📚 Total terminology entries: {total_terms}")
        test_results['terminology_loaded'] = total_terms > 0
        print()
        
        # Test improved context-aware translation
        print(f"🔄 Testing improved context-aware translation:")
        print("-" * 50)
        
        # Store translations as we go for context building
        translations = []
        context_results = []
        
        for i, text in enumerate(test_texts):
            print(f"\n📝 Segment {i + 1}/{len(test_texts)}:")
            print(f"   EN: {text[:80]}...")
            
            # Build improved context
            context_parts = []
            
            # Previous segments with their translations
            for j in range(max(0, i - CONTEXT_WINDOW), i):
                prev_en = test_texts[j]
                prev_zh = translations[j] if j < len(translations) else ""
                
                context_parts.append(f"前文段落 {j + 1}:")
                context_parts.append(f"  英文: {prev_en}")
                if prev_zh:
                    context_parts.append(f"  中文: {prev_zh}")
                context_parts.append("")
            
            # Next segments (English only)
            for j in range(i + 1, min(len(test_texts), i + CONTEXT_WINDOW + 1)):
                next_en = test_texts[j]
                context_parts.append(f"后文段落 {j + 1}:")
                context_parts.append(f"  英文: {next_en}")
                context_parts.append("")
            
            context = "\n".join(context_parts).strip() if context_parts else ""
            
            # Display context info
            prev_segments = min(i, CONTEXT_WINDOW)
            next_segments = min(len(test_texts) - i - 1, CONTEXT_WINDOW)
            total_context_segments = prev_segments + next_segments
            
            print(f"   📖 Context: {prev_segments} previous + {next_segments} next = {total_context_segments} segments")
            if prev_segments > 0:
                print(f"   🔄 Previous translations included: Yes")
            
            # Translate with improved context
            result = translator.translate_text(text, context)
            
            if result.get('translated_text'):
                translation = result['translated_text']
                translations.append(translation)
                
                print(f"   ZH: {translation}")
                print(f"   📊 Tokens used: {result.get('tokens_used', 'N/A')}")
                print(f"   ✅ Success")
                
                # Track total tokens
                if 'tokens_used' in result:
                    test_results['total_tokens_used'] += result['tokens_used']
            else:
                translations.append("")
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            
            # Store result
            segment_result = {
                'segment_id': i,
                'english_text': text,
                'chinese_text': result.get('translated_text', ''),
                'context_segments_used': total_context_segments,
                'previous_translations_included': prev_segments > 0,
                'context_content': context,
                'translation_metadata': result
            }
            
            context_results.append(segment_result)
        
        # Store context results
        test_results['context_aware_translations'] = context_results
        
        # Display final results summary
        print(f"\n\n📋 Translation Results Summary:")
        print("-" * 50)
        
        for i, segment in enumerate(context_results):
            print(f"\nSegment {i + 1}:")
            print(f"   EN: {segment['english_text']}")
            print(f"   ZH: {segment['chinese_text']}")
            print(f"   Context segments: {segment['context_segments_used']}")
            print(f"   Previous translations: {'Yes' if segment['previous_translations_included'] else 'No'}")
            
            metadata = segment['translation_metadata']
            if 'tokens_used' in metadata:
                print(f"   Tokens: {metadata['tokens_used']}")
        
        # Compare terminology usage
        print(f"\n\n📚 Terminology Usage Analysis:")
        print("-" * 50)
        
        key_terms = ['aware', 'present moment', 'moment', 'breathing', 'thoughts']
        for term in key_terms:
            print(f"\n🔍 Term: '{term}'")
            for i, segment in enumerate(context_results):
                en_text = segment['english_text'].lower()
                zh_text = segment['chinese_text']
                if term in en_text:
                    print(f"   Segment {i + 1}: {zh_text}")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = TRANSLATIONS_DIR / f"enhanced_gpt_translation_v2_test_{timestamp}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test results saved to: {output_path}")
        print(f"📊 Total tokens used in test: {test_results['total_tokens_used']}")
        
        # Calculate estimated cost
        if test_results['total_tokens_used'] > 0:
            total_tokens = test_results['total_tokens_used']
            input_tokens = total_tokens * 0.7
            output_tokens = total_tokens * 0.3
            
            if GPT_MODEL == "gpt-4.1-mini":
                cost = (input_tokens / 1000 * 0.00015) + (output_tokens / 1000 * 0.0006)
            else:  # gpt-4.1
                cost = (input_tokens / 1000 * 0.005) + (output_tokens / 1000 * 0.015)
            
            print(f"💰 Estimated cost: ${cost:.4f}")
        
        print(f"🎉 Enhanced GPT translation V2 test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main test function"""
    print("🧘 Enhanced GPT Translation V2 Testing")
    print("=" * 65)
    print("🆕 New Features:")
    print("   • Previous translations included in context")
    print("   • Better terminology consistency")
    print("   • Improved context formatting")
    print()
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    config_path = Path(__file__).parent.parent / 'config' / 'openai.json'
    
    if not api_key and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            api_key = config.get('api')
        except:
            pass
    
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("   Please set OPENAI_API_KEY environment variable")
        print("   or create config/openai.json with your API key")
        sys.exit(1)
    
    print("✅ OpenAI API key found")
    
    # Check if terminology file exists
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / TERMINOLOGY_FILE
    if not terminology_file.exists():
        print(f"⚠️  Terminology file not found: {terminology_file}")
        sys.exit(1)
    
    print(f"✅ Terminology file found: {TERMINOLOGY_FILE}")
    print()
    
    # Run test
    success = test_enhanced_gpt_translation_v2()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"\n💡 Key improvements:")
        print(f"   • Previous Chinese translations included in context")
        print(f"   • Better terminology consistency across segments")
        print(f"   • More coherent translation style")
        print(f"   • Detailed context usage analysis")
    else:
        print(f"\n💥 Test failed. Please check your API key and network connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()

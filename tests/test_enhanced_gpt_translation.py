#!/usr/bin/env python3
"""
Test script for Enhanced GPT-based translation with mindfulness content
Tests context-aware translation with configurable models and terminology files
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
TERMINOLOGY_FILE = "terminology_enhanced_simple.json"  # Options: "terminology.json", "terminology_enhanced_simple.json", "terminology_structured.json", "terminology_one2many.json"

def test_enhanced_gpt_translation():
    """Test Enhanced GPT translation with context-aware mode"""
    print("Enhanced GPT Translation Test - Context-Aware Mode")
    print("=" * 60)
    print(f"Model: {GPT_MODEL}")
    print(f"Terminology: {TERMINOLOGY_FILE}")
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
        
        print(f"📚 Simple terminology entries: {simple_terms}")
        print(f"📚 Structured terminology entries: {structured_terms}")
        print(f"📚 Total terminology entries: {total_terms}")
        test_results['terminology_loaded'] = total_terms > 0
        print()
        
        # Test context-aware translation
        print(f"🔄 Testing context-aware translation:")
        print("-" * 40)
        
        # Prepare segments for context testing
        segments = []
        for i, text in enumerate(test_texts):
            segments.append({
                'segment_id': i,
                'english_text': text,
                'start_time': i * 15.0,
                'end_time': (i + 1) * 15.0,
                'duration': 15.0,
                'file_path': f'test_segment_{i}.wav'
            })
        
        # Translate with context (using context window of 1)
        print("🤖 Translating with context awareness...")
        context_results = []
        
        for i, segment in enumerate(segments):
            english_text = segment['english_text']
            
            # Build context from surrounding segments
            context_parts = []
            
            # Previous segment
            if i > 0:
                prev_text = segments[i-1]['english_text']
                context_parts.append(f"前文：{prev_text}")
            
            # Next segment
            if i < len(segments) - 1:
                next_text = segments[i+1]['english_text']
                context_parts.append(f"后文：{next_text}")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            print(f"\n📝 Segment {i + 1}/{len(segments)}:")
            print(f"   EN: {english_text[:80]}...")
            
            if context:
                print(f"   📖 Context provided: {len(context_parts)} surrounding segments")
            else:
                print(f"   📖 No context (first/last segment)")
            
            # Translate with context
            result = translator.translate_text(english_text, context)
            
            # Store result
            segment_result = {
                'segment_id': i,
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'english_text': english_text,
                'chinese_text': result.get('translated_text', ''),
                'context_used': bool(context),
                'translation_metadata': result
            }
            
            context_results.append(segment_result)
            
            if result.get('translated_text'):
                print(f"   ZH: {result['translated_text']}")
                print(f"   📊 Tokens used: {result.get('tokens_used', 'N/A')}")
                print(f"   ✅ Success")
                
                # Track total tokens
                if 'tokens_used' in result:
                    test_results['total_tokens_used'] += result['tokens_used']
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        # Store context results
        test_results['context_aware_translations'] = context_results
        
        # Display final results summary
        print(f"\n\n📋 Translation Results Summary:")
        print("-" * 40)
        
        for i, segment in enumerate(context_results):
            print(f"\nSegment {i + 1}:")
            print(f"   EN: {segment['english_text']}")
            print(f"   ZH: {segment['chinese_text']}")
            print(f"   Context: {'Yes' if segment['context_used'] else 'No'}")
            
            metadata = segment['translation_metadata']
            if 'tokens_used' in metadata:
                print(f"   Tokens: {metadata['tokens_used']}")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = TRANSLATIONS_DIR / f"enhanced_gpt_translation_test_{timestamp}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test results saved to: {output_path}")
        print(f"📊 Total tokens used in test: {test_results['total_tokens_used']}")
        
        # Calculate estimated cost
        if test_results['total_tokens_used'] > 0:
            # GPT-4o-mini pricing: $0.00015 per 1K input tokens, $0.0006 per 1K output tokens
            # Rough estimate assuming 70% input, 30% output
            total_tokens = test_results['total_tokens_used']
            input_tokens = total_tokens * 0.7
            output_tokens = total_tokens * 0.3
            
            if GPT_MODEL == "gpt-4o-mini":
                cost = (input_tokens / 1000 * 0.00015) + (output_tokens / 1000 * 0.0006)
            else:  # gpt-4o
                cost = (input_tokens / 1000 * 0.005) + (output_tokens / 1000 * 0.015)
            
            print(f"💰 Estimated cost: ${cost:.4f}")
        
        print(f"🎉 Enhanced GPT translation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main test function"""
    print("🧘 Enhanced GPT Translation Testing for Mindfulness Content")
    print("=" * 60)
    
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
    print()
    
    # Check if terminology file exists
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / TERMINOLOGY_FILE
    if not terminology_file.exists():
        print(f"⚠️  Terminology file not found: {terminology_file}")
        print("   Available terminology files:")
        terminology_dir = terminology_file.parent
        if terminology_dir.exists():
            for f in terminology_dir.glob("*.json"):
                print(f"   - {f.name}")
        print()
        print("   Please update TERMINOLOGY_FILE variable in the script")
        sys.exit(1)
    
    print(f"✅ Terminology file found: {TERMINOLOGY_FILE}")
    print()
    
    # Run test
    success = test_enhanced_gpt_translation()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"\n💡 Configuration tips:")
        print(f"   • Modify GPT_MODEL variable to test different models")
        print(f"   • Modify TERMINOLOGY_FILE variable to test different terminology formats")
        print(f"   • Use gpt-4o-mini for cost-effective testing")
        print(f"   • Use gpt-4o for highest quality translations")
        print(f"   • Context-aware translation uses surrounding segments for better coherence")
    else:
        print(f"\n💥 Test failed. Please check your API key and network connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()

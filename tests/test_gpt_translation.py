#!/usr/bin/env python3
"""
Test script for GPT-based translation with mindfulness content
Demonstrates the enhanced translation capabilities with terminology integration
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
from scripts.audio_pipeline.gpt_translator import GPTTranslator
from scripts.audio_pipeline.config import TRANSLATIONS_DIR

# Model configuration - change this to test different models
GPT_MODEL = "gpt-4.1-mini"  # Options: "gpt-4o", "gpt-4o-mini"

def test_gpt_translation():
    """Test GPT translation with sample mindfulness content"""
    print("GPT Translation Test for Mindfulness Content")
    print("=" * 60)
    
    # Load terminology
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / 'terminology.json'
    
    ###Sample mindfulness texts for testing
    test_texts = [
        "Remind yourself. That you're here. You're awake and aware. And spend this first few moments of the meditation just settling. And sensing into being here. Sense of being awake in the midst of this moment.",
        "Take a moment to notice your breathing. Feel the natural rhythm of your breath. There's no need to change anything, just observe.",
        "Allow your attention to rest in the present moment. Notice any thoughts that arise, and gently let them pass like clouds in the sky."
    ]
    
    # Prepare results structure
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'model_used': GPT_MODEL,
        'terminology_loaded': False,
        'individual_translations': [],
        'context_aware_translations': [],
        'terminology_test': {},
        'total_tokens_used': 0
    }
    
    try:
        # Initialize GPT translator
        print(f"🤖 Initializing GPT translator with model: {GPT_MODEL}...")
        translator = GPTTranslator(
            model=GPT_MODEL,
            terminology_file=terminology_file
        )
        
        print(f"✅ GPT translator initialized successfully")
        print(f"📚 Terminology entries loaded: {len(translator.terminology)}")
        test_results['terminology_loaded'] = len(translator.terminology) > 0
        print()
        
        # Test individual translations
        print("🔄 Testing individual translations:")
        print("-" * 40)
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n{i}. Testing translation:")
            print(f"   EN: {text}")
            
            # Estimate cost first
            cost_estimate = translator.estimate_cost(text)
            print(f"   💰 Estimated cost: ${cost_estimate['estimated_cost_usd']:.4f}")
            
            # Translate
            result = translator.translate_text(text)
            
            # Store result
            translation_record = {
                'test_id': i,
                'original_text': text,
                'cost_estimate': cost_estimate,
                'translation_result': result
            }
            test_results['individual_translations'].append(translation_record)
            
            if result.get('translated_text'):
                print(f"   ZH: {result['translated_text']}")
                print(f"   📊 Tokens used: {result.get('tokens_used', 'N/A')}")
                print(f"   ✅ Success")
                # Track total tokens
                if 'tokens_used' in result:
                    test_results['total_tokens_used'] += result['tokens_used']
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        # Test context-aware translation
        print(f"\n\n🔄 Testing context-aware translation:")
        print("-" * 40)
        
        # Prepare segments for context testing
        segments = []
        for i, text in enumerate(test_texts[:3]):  # Use first 3 for context test
            segments.append({
                'segment_id': i,
                'english_text': text,
                'start_time': i * 10.0,
                'end_time': (i + 1) * 10.0,
                'duration': 10.0,
                'file_path': f'test_segment_{i}.wav'
            })
        
        # Translate with context
        context_results = translator.translate_with_context(segments, context_window=1)
        
        # Store context results
        test_results['context_aware_translations'] = context_results
        
        print("\nContext-aware translation results:")
        for segment in context_results:
            gpt_result = segment.get('gpt_translation', {})
            print(f"\nSegment {segment['segment_id'] + 1}:")
            print(f"   EN: {segment['english_text']}")
            print(f"   ZH: {gpt_result.get('translated_text', 'Error')}")
            if 'tokens_used' in gpt_result:
                print(f"   📊 Tokens: {gpt_result['tokens_used']}")
                test_results['total_tokens_used'] += gpt_result['tokens_used']
        
        # Test terminology usage
        print(f"\n\n📚 Testing terminology integration:")
        print("-" * 40)
        
        terminology_test = "Practice mindfulness meditation with awareness and presence."
        print(f"Text with terminology: {terminology_test}")
        
        result = translator.translate_text(terminology_test)
        print(f"Translation: {result.get('translated_text', 'Error')}")
        print(f"Terminology applied: {result.get('terminology_applied', False)}")
        
        # Store terminology test result
        test_results['terminology_test'] = {
            'original_text': terminology_test,
            'translation_result': result
        }
        
        if 'tokens_used' in result:
            test_results['total_tokens_used'] += result['tokens_used']
        
        # Save results to file
        output_path = TRANSLATIONS_DIR / f"gpt_translation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test results saved to: {output_path}")
        print(f"📊 Total tokens used in test: {test_results['total_tokens_used']}")
        print(f"🎉 GPT translation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_cost_estimation():
    """Test cost estimation functionality"""
    print("\n" + "=" * 60)
    print("Cost Estimation Test")
    print("=" * 60)
    
    try:
        terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / 'terminology_one2many.json'
        translator = GPTTranslator(model=GPT_MODEL, terminology_file=terminology_file)
        
        # Test with different text lengths
        test_cases = [
            "Short text.",
            "This is a medium length text that contains several sentences about mindfulness and meditation practice.",
            """This is a longer text that simulates a typical mindfulness meditation segment. 
            It includes multiple sentences with various mindfulness terms and concepts. 
            The text discusses awareness, presence, breathing, and the practice of letting go. 
            It demonstrates how the cost estimation works with more substantial content 
            that would be typical in a real meditation audio transcription."""
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\nTest case {i}:")
            print(f"Text length: {len(text)} characters")
            print(f"Text: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            estimate = translator.estimate_cost(text)
            print(f"Estimated tokens: {estimate['estimated_total_tokens']}")
            print(f"Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
        
        print(f"\n✅ Cost estimation test completed!")
        
    except Exception as e:
        print(f"❌ Cost estimation test failed: {e}")

def main():
    """Main test function"""
    print("🧘 GPT Translation Testing for Mindfulness Content")
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
    
    # Run tests
    success = test_gpt_translation()
    
    if success:
        test_cost_estimation()
        print(f"\n🎉 All tests completed successfully!")
        print(f"\n💡 Usage tips:")
        print(f"   • Set TRANSLATION_PROVIDER=gpt to use GPT in the pipeline")
        print(f"   • Set GPT_MODEL=gpt-4o-mini for lower costs during testing")
        print(f"   • Use gpt-4o for highest quality translations")
        print(f"   • The translator automatically includes terminology and context")
    else:
        print(f"\n💥 Tests failed. Please check your API key and network connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()

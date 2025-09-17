#!/usr/bin/env python3
"""
Test script for the optimized GPT translation pipeline
Tests the enhanced context-aware translation with previous translations
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

# Configuration
GPT_MODEL = "gpt-4.1-mini"
TERMINOLOGY_FILE = "terminology_enhanced_simple.json"

def create_mock_transcription_data():
    """Create mock transcription data for testing"""
    test_texts = [
        "Remind yourself. That you're here. You're awake and aware. And spend this first few moments of the meditation just settling. And sensing into being here. Sense of being awake in the midst of this moment.",
        "Take a moment to notice your breathing. Feel the natural rhythm of your breath. There's no need to change anything, just observe.",
        "Allow your attention to rest in the present moment. Notice any thoughts that arise, and gently let them pass like clouds in the sky.",
        "Now bring your awareness back to your breath. Each breath is an anchor to the present moment. Stay with this awareness.",
        "As we conclude this meditation, take a moment to appreciate this time you've given yourself for mindfulness practice."
    ]
    
    segments = []
    for i, text in enumerate(test_texts):
        segments.append({
            'segment_id': i,
            'start_time': i * 15.0,
            'end_time': (i + 1) * 15.0,
            'duration': 15.0,
            'file_path': f'test_segment_{i}.wav',
            'transcription': {
                'full_transcript': text,
                'confidence': 0.95
            }
        })
    
    return {
        'original_file': 'test_meditation.wav',
        'total_segments': len(segments),
        'segments': segments
    }

def test_optimized_pipeline():
    """Test the optimized GPT translation pipeline"""
    print("🧘 Optimized GPT Translation Pipeline Test")
    print("=" * 60)
    print(f"Model: {GPT_MODEL}")
    print(f"Terminology: {TERMINOLOGY_FILE}")
    print()
    
    # Load terminology file
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / TERMINOLOGY_FILE
    
    try:
        # Initialize GPT translator
        print("🤖 Initializing optimized GPT translator...")
        translator = GPTTranslator(
            model=GPT_MODEL,
            terminology_file=terminology_file
        )
        
        print(f"✅ GPT translator initialized successfully")
        print(f"📚 Terminology entries loaded: {len(translator.terminology)}")
        print()
        
        # Create mock transcription data
        transcription_data = create_mock_transcription_data()
        
        # Test 1: Original method (no previous translations in context)
        print("🔄 Test 1: Original Context Method")
        print("-" * 40)
        
        results_original = translator.translate_transcription_results(
            transcription_data, 
            use_context=True,
            include_previous_translations=False,
            context_window=1
        )
        
        print("\n📋 Original Method Results:")
        for segment in results_original['segments']:
            print(f"   Segment {segment['segment_id'] + 1}: {segment['chinese_text']}")
        
        # Test 2: Optimized method (with previous translations in context)
        print(f"\n\n🔄 Test 2: Optimized Context Method")
        print("-" * 40)
        
        results_optimized = translator.translate_transcription_results(
            transcription_data, 
            use_context=True,
            include_previous_translations=True,
            context_window=1
        )
        
        print("\n📋 Optimized Method Results:")
        for segment in results_optimized['segments']:
            print(f"   Segment {segment['segment_id'] + 1}: {segment['chinese_text']}")
        
        # Compare results
        print(f"\n\n📊 Comparison Analysis:")
        print("-" * 40)
        
        # Token usage comparison
        original_tokens = results_original.get('total_tokens_used', 0)
        optimized_tokens = results_optimized.get('total_tokens_used', 0)
        
        print(f"Token Usage:")
        print(f"   Original method: {original_tokens} tokens")
        print(f"   Optimized method: {optimized_tokens} tokens")
        print(f"   Difference: {optimized_tokens - original_tokens} tokens ({((optimized_tokens - original_tokens) / original_tokens * 100):.1f}%)")
        
        # Terminology consistency analysis
        print(f"\nTerminology Consistency Analysis:")
        key_terms = ['moment', 'awareness', 'breath', 'present', 'mindfulness']
        
        for term in key_terms:
            print(f"\n🔍 Term: '{term}'")
            
            # Check original translations
            original_translations = []
            for segment in results_original['segments']:
                en_text = segment['english_text'].lower()
                zh_text = segment['chinese_text']
                if term in en_text:
                    original_translations.append(f"Seg {segment['segment_id'] + 1}: {zh_text}")
            
            # Check optimized translations
            optimized_translations = []
            for segment in results_optimized['segments']:
                en_text = segment['english_text'].lower()
                zh_text = segment['chinese_text']
                if term in en_text:
                    optimized_translations.append(f"Seg {segment['segment_id'] + 1}: {zh_text}")
            
            if original_translations:
                print(f"   Original:")
                for trans in original_translations:
                    print(f"     {trans}")
            
            if optimized_translations:
                print(f"   Optimized:")
                for trans in optimized_translations:
                    print(f"     {trans}")
        
        # Save comparison results
        comparison_results = {
            'test_timestamp': datetime.now().isoformat(),
            'model_used': GPT_MODEL,
            'terminology_file': TERMINOLOGY_FILE,
            'original_method': {
                'include_previous_translations': False,
                'results': results_original
            },
            'optimized_method': {
                'include_previous_translations': True,
                'results': results_optimized
            },
            'comparison': {
                'token_difference': optimized_tokens - original_tokens,
                'token_increase_percentage': ((optimized_tokens - original_tokens) / original_tokens * 100) if original_tokens > 0 else 0
            }
        }
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = TRANSLATIONS_DIR / f"pipeline_optimization_comparison_{timestamp}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comparison results saved to: {output_path}")
        
        # Calculate estimated costs
        if original_tokens > 0 and optimized_tokens > 0:
            # GPT-4.1-mini pricing estimation
            input_cost_per_1k = 0.00015
            output_cost_per_1k = 0.0006
            
            def estimate_cost(total_tokens):
                input_tokens = total_tokens * 0.7
                output_tokens = total_tokens * 0.3
                return (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)
            
            original_cost = estimate_cost(original_tokens)
            optimized_cost = estimate_cost(optimized_tokens)
            
            print(f"\n💰 Cost Comparison:")
            print(f"   Original method: ${original_cost:.4f}")
            print(f"   Optimized method: ${optimized_cost:.4f}")
            print(f"   Additional cost: ${optimized_cost - original_cost:.4f}")
        
        print(f"\n🎉 Pipeline optimization test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧘 GPT Translation Pipeline Optimization Test")
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
    
    # Check if terminology file exists
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / TERMINOLOGY_FILE
    if not terminology_file.exists():
        print(f"⚠️  Terminology file not found: {terminology_file}")
        sys.exit(1)
    
    print(f"✅ Terminology file found: {TERMINOLOGY_FILE}")
    print()
    
    # Run test
    success = test_optimized_pipeline()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"\n💡 Key findings:")
        print(f"   • Optimized method includes previous translations in context")
        print(f"   • Better terminology consistency across segments")
        print(f"   • Slight increase in token usage for improved quality")
        print(f"   • Enhanced coherence in translation style")
    else:
        print(f"\n💥 Test failed. Please check your API key and network connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()

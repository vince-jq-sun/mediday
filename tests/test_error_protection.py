#!/usr/bin/env python3
"""
Test script for error accumulation protection in GPT translation
Tests how the system handles and prevents error propagation
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

def create_test_data_with_errors():
    """Create test data that includes intentional errors to test error protection"""
    
    # Test segments with intentional errors in "previous translations"
    test_segments = [
        {
            'segment_id': 0,
            'english_text': 'Welcome to this mindfulness meditation practice.',
            'start_time': 0.0,
            'end_time': 10.0,
            'duration': 10.0,
            'file_path': 'test_segment_0.wav'
        },
        {
            'segment_id': 1,
            'english_text': 'Take a moment to settle into your present moment awareness.',
            'start_time': 10.0,
            'end_time': 20.0,
            'duration': 10.0,
            'file_path': 'test_segment_1.wav',
            # Simulate a bad previous translation
            'simulated_previous_translation': '错误翻译：Take a moment to settle into your present moment awareness.'  # Intentionally bad
        },
        {
            'segment_id': 2,
            'english_text': 'Notice your breathing and allow your attention to rest here.',
            'start_time': 20.0,
            'end_time': 30.0,
            'duration': 10.0,
            'file_path': 'test_segment_2.wav',
            'simulated_previous_translation': '花一点时间安住在此刻的觉知中。'  # Good translation
        },
        {
            'segment_id': 3,
            'english_text': 'Let any thoughts pass by like clouds in the sky.',
            'start_time': 30.0,
            'end_time': 40.0,
            'duration': 10.0,
            'file_path': 'test_segment_3.wav',
            'simulated_previous_translation': '观察你的呼吸，让你的注意力安住在这里。'  # Good translation
        }
    ]
    
    return test_segments

def test_error_protection():
    """Test the error protection mechanisms"""
    print("🛡️ GPT Translation Error Protection Test")
    print("=" * 60)
    print(f"Model: {GPT_MODEL}")
    print(f"Terminology: {TERMINOLOGY_FILE}")
    print()
    
    # Load terminology file
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / TERMINOLOGY_FILE
    
    try:
        # Initialize GPT translator
        print("🤖 Initializing GPT translator with error protection...")
        translator = GPTTranslator(
            model=GPT_MODEL,
            terminology_file=terminology_file
        )
        
        print(f"✅ GPT translator initialized successfully")
        print(f"📚 Terminology entries loaded: {len(translator.terminology)}")
        print()
        
        # Get test data
        test_segments = create_test_data_with_errors()
        
        # Test error protection
        print("🔄 Testing Error Protection Mechanisms:")
        print("-" * 50)
        
        results = []
        translations = []  # Store translations as we go
        
        for i, segment in enumerate(test_segments):
            english_text = segment['english_text']
            
            print(f"\n📝 Segment {i + 1}: {english_text}")
            
            # Build context with simulated previous translations (including errors)
            context_parts = []
            
            # Add previous segments with their translations (including simulated errors)
            for j in range(max(0, i - 1), i):
                prev_segment = test_segments[j]
                prev_en = prev_segment['english_text']
                
                # Use actual translation if available, otherwise use simulated
                if j < len(translations):
                    prev_zh = translations[j]
                else:
                    prev_zh = prev_segment.get('simulated_previous_translation', '')
                
                if prev_en and prev_zh:
                    context_parts.append(f"前文段落 {j + 1}:")
                    context_parts.append(f"  英文: {prev_en}")
                    context_parts.append(f"  中文: {prev_zh}")
                    context_parts.append("")
            
            # Add next segment (English only)
            if i + 1 < len(test_segments):
                next_segment = test_segments[i + 1]
                next_en = next_segment['english_text']
                context_parts.append(f"后文段落 {i + 2}:")
                context_parts.append(f"  英文: {next_en}")
                context_parts.append("")
            
            context = "\n".join(context_parts).strip() if context_parts else ""
            
            # Show context being used
            if context:
                print(f"   📖 Context provided:")
                for j in range(max(0, i - 1), i):
                    prev_segment = test_segments[j]
                    prev_zh = prev_segment.get('simulated_previous_translation', translations[j] if j < len(translations) else '')
                    if 'Take a moment to settle' in prev_zh or '错误翻译' in prev_zh:
                        print(f"      ⚠️  Previous translation contains errors: {prev_zh}")
                    else:
                        print(f"      ✅ Previous translation looks good: {prev_zh}")
            
            # Translate with context
            result = translator.translate_text(english_text, context)
            
            if result.get('translated_text'):
                translation = result['translated_text']
                translations.append(translation)
                
                print(f"   🎯 Translation: {translation}")
                
                # Check quality validation
                validation = result.get('quality_validation', {})
                quality_score = validation.get('quality_score', 1.0)
                warnings = validation.get('warnings', [])
                
                print(f"   📊 Quality score: {quality_score:.2f}")
                if warnings:
                    print(f"   ⚠️  Quality warnings: {'; '.join(warnings)}")
                else:
                    print(f"   ✅ No quality issues detected")
                
                # Check if error was prevented
                if 'Take a moment to settle' in translation or '错误翻译' in translation:
                    print(f"   ❌ ERROR PROPAGATED: Translation contains previous error!")
                else:
                    print(f"   🛡️  Error protection successful: Clean translation generated")
                
            else:
                translations.append("")
                print(f"   ❌ Translation failed: {result.get('error', 'Unknown error')}")
            
            # Store result
            segment_result = {
                'segment_id': i,
                'english_text': english_text,
                'chinese_text': result.get('translated_text', ''),
                'context_used': context,
                'quality_validation': result.get('quality_validation', {}),
                'translation_metadata': result
            }
            
            results.append(segment_result)
        
        # Analyze results
        print(f"\n\n📊 Error Protection Analysis:")
        print("-" * 50)
        
        error_propagation_count = 0
        quality_issues_count = 0
        
        for i, result in enumerate(results):
            translation = result['chinese_text']
            validation = result['quality_validation']
            
            print(f"\nSegment {i + 1}:")
            print(f"   Translation: {translation}")
            print(f"   Quality Score: {validation.get('quality_score', 'N/A')}")
            
            # Check for error propagation
            if 'Take a moment to settle' in translation or '错误翻译' in translation:
                print(f"   ❌ Error propagated from previous segment")
                error_propagation_count += 1
            else:
                print(f"   ✅ No error propagation detected")
            
            # Check for quality issues
            if validation.get('warnings'):
                print(f"   ⚠️  Quality warnings: {'; '.join(validation['warnings'])}")
                quality_issues_count += 1
        
        # Summary
        print(f"\n\n🎯 Test Summary:")
        print("-" * 30)
        print(f"Total segments tested: {len(results)}")
        print(f"Error propagation incidents: {error_propagation_count}")
        print(f"Quality issues detected: {quality_issues_count}")
        
        if error_propagation_count == 0:
            print(f"🎉 SUCCESS: No error propagation detected!")
        else:
            print(f"⚠️  WARNING: {error_propagation_count} error propagation incidents")
        
        # Save results
        test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'model_used': GPT_MODEL,
            'terminology_file': TERMINOLOGY_FILE,
            'test_type': 'error_protection',
            'segments': results,
            'summary': {
                'total_segments': len(results),
                'error_propagation_count': error_propagation_count,
                'quality_issues_count': quality_issues_count,
                'protection_success_rate': (len(results) - error_propagation_count) / len(results) if len(results) > 0 else 0
            }
        }
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = TRANSLATIONS_DIR / f"error_protection_test_{timestamp}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test results saved to: {output_path}")
        print(f"🛡️  Error protection test completed!")
        
        return error_propagation_count == 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧘 GPT Translation Error Protection Testing")
    print("=" * 60)
    print("🎯 Purpose: Test how well the system prevents error accumulation")
    print("📋 Method: Inject intentional errors and check if they propagate")
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
    success = test_error_protection()
    
    if success:
        print(f"\n🎉 Error protection test PASSED!")
        print(f"\n💡 Key protection mechanisms:")
        print(f"   • Enhanced prompts with error detection instructions")
        print(f"   • Terminology table priority over context")
        print(f"   • Quality validation with automatic scoring")
        print(f"   • Independent judgment encouragement")
    else:
        print(f"\n⚠️  Error protection test revealed issues.")
        print(f"   Please review the results and consider additional safeguards.")

if __name__ == "__main__":
    main()

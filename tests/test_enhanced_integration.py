#!/usr/bin/env python3
"""
Test script for enhanced GPT translator integration
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.audio_pipeline.translator import Translator
from scripts.audio_pipeline.config import TERMINOLOGY_FILE

def test_enhanced_gpt_integration():
    """Test enhanced GPT translator integration"""
    print("🧪 Testing Enhanced GPT Translator Integration")
    print("=" * 50)
    
    # Set environment variables for enhanced GPT
    os.environ['TRANSLATION_PROVIDER'] = 'gpt'
    os.environ['GPT_MODEL'] = 'gpt-4o-mini'
    os.environ['USE_ENHANCED_GPT'] = 'true'
    
    try:
        # Initialize translator
        print("1. Initializing Enhanced GPT Translator...")
        translator = Translator(terminology_file=TERMINOLOGY_FILE, provider='gpt')
        
        # Check if enhanced translator is loaded
        if translator.enhanced_gpt_translator:
            print("✅ Enhanced GPT translator successfully loaded")
            print(f"   Model: {translator.enhanced_gpt_translator.model}")
            print(f"   Terminology entries: {len(translator.enhanced_gpt_translator.terminology) + len(translator.enhanced_gpt_translator.structured_terminology)}")
        else:
            print("❌ Enhanced GPT translator not loaded")
            return False
        
        # Test single translation
        print("\n2. Testing single translation...")
        test_text = "Focus on your breathing and be mindful of the present moment."
        context = "This is a foundational meditation instruction."
        
        result = translator.translate_text(test_text, context=context)
        
        if result.get('translated_text'):
            print("✅ Single translation successful")
            print(f"   Original: {test_text}")
            print(f"   Translation: {result['translated_text']}")
            print(f"   Provider: {result.get('provider', 'unknown')}")
            print(f"   Context used: {result.get('context_used', False)}")
            print(f"   Terminology applied: {result.get('terminology_applied', False)}")
            if 'tokens_used' in result:
                print(f"   Tokens used: {result['tokens_used']}")
        else:
            print("❌ Single translation failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
        
        # Test terminology handling
        print("\n3. Testing terminology handling...")
        mindfulness_text = "Practice mindfulness meditation with awareness."
        result2 = translator.translate_text(mindfulness_text)
        
        if result2.get('translated_text'):
            print("✅ Terminology test successful")
            print(f"   Original: {mindfulness_text}")
            print(f"   Translation: {result2['translated_text']}")
            
            # Check if key terms are properly translated
            translation = result2['translated_text']
            if '正念' in translation or '冥想' in translation:
                print("✅ Key terminology correctly applied")
            else:
                print("⚠️ Key terminology may not be applied correctly")
        else:
            print("❌ Terminology test failed")
            return False
        
        print("\n🎉 Enhanced GPT integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regular_vs_enhanced():
    """Compare regular vs enhanced GPT translator"""
    print("\n🔄 Comparing Regular vs Enhanced GPT Translators")
    print("=" * 50)
    
    test_text = "Be aware of your thoughts without judgment, returning attention to the breath."
    
    try:
        # Test regular GPT
        print("Testing Regular GPT...")
        os.environ['USE_ENHANCED_GPT'] = 'false'
        regular_translator = Translator(terminology_file=TERMINOLOGY_FILE, provider='gpt')
        regular_result = regular_translator.translate_text(test_text)
        
        # Test enhanced GPT
        print("Testing Enhanced GPT...")
        os.environ['USE_ENHANCED_GPT'] = 'true'
        enhanced_translator = Translator(terminology_file=TERMINOLOGY_FILE, provider='gpt')
        enhanced_result = enhanced_translator.translate_text(test_text)
        
        print(f"\nOriginal: {test_text}")
        print(f"Regular GPT: {regular_result.get('translated_text', 'Failed')}")
        print(f"Enhanced GPT: {enhanced_result.get('translated_text', 'Failed')}")
        
        # Compare features
        print(f"\nFeature Comparison:")
        print(f"Regular - Provider: {regular_result.get('provider', 'N/A')}")
        print(f"Enhanced - Provider: {enhanced_result.get('provider', 'N/A')}")
        print(f"Enhanced - Terminology Applied: {enhanced_result.get('terminology_applied', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Enhanced GPT Translator Integration Tests")
    print("=" * 60)
    
    # Test 1: Basic integration
    success1 = test_enhanced_gpt_integration()
    
    # Test 2: Comparison
    success2 = test_regular_vs_enhanced()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Enhanced GPT translator is ready to use.")
        print("\nUsage examples:")
        print("# Use enhanced GPT with context:")
        print("python -m scripts.audio_pipeline.pipeline translate --provider gpt --enhanced --context-window 2")
        print("\n# Use regular GPT:")
        print("python -m scripts.audio_pipeline.pipeline translate --provider gpt --context-window 2")
    else:
        print("\n❌ Some tests failed. Please check the integration.")
        sys.exit(1)

#!/usr/bin/env python3
"""
Test script to validate the improved quality score calculation
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.audio_pipeline.gpt_translator import GPTTranslator

def test_quality_score_improvements():
    """Test the improved quality score calculation"""
    print("📊 Quality Score Validation Test")
    print("=" * 50)
    
    # Load terminology file
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / 'terminology_enhanced_simple.json'
    
    # Initialize translator (without API key for validation testing)
    translator = GPTTranslator(model="gpt-4.1-mini", terminology_file=terminology_file)
    
    # Test cases with expected quality scores
    test_cases = [
        {
            'name': 'Good translation with mindfulness',
            'english': 'Welcome to this mindfulness meditation practice.',
            'chinese': '欢迎来到这次正念冥想练习。',
            'expected_score_range': (0.85, 1.0),
            'should_find_mindfulness': True
        },
        {
            'name': 'Translation with present moment',
            'english': 'Take a moment to settle into your present moment awareness.',
            'chinese': '花一点时间，安住下来，进入你此刻的觉知。',
            'expected_score_range': (0.85, 1.0),
            'should_find_present': True
        },
        {
            'name': 'Translation missing critical term',
            'english': 'Practice mindfulness meditation daily.',
            'chinese': '每天练习冥想。',  # Missing "正念"
            'expected_score_range': (0.7, 0.9),
            'should_warn_missing': True
        },
        {
            'name': 'Very short translation',
            'english': 'This is a very long sentence about mindfulness meditation practice with many words.',
            'chinese': '正念。',  # Too short
            'expected_score_range': (0.6, 0.8),
            'should_warn_short': True
        },
        {
            'name': 'Translation with English words',
            'english': 'Focus on your breathing.',
            'chinese': '专注于你的 breathing。',  # Contains English
            'expected_score_range': (0.5, 0.8),
            'should_warn_english': True
        },
        {
            'name': 'Perfect translation',
            'english': 'Notice your thoughts and let them pass.',
            'chinese': '觉察你的念头，让它们自然流过。',
            'expected_score_range': (0.95, 1.0),
            'should_be_perfect': True
        }
    ]
    
    print(f"Testing {len(test_cases)} cases...\n")
    
    results = []
    for i, case in enumerate(test_cases, 1):
        print(f"Test {i}: {case['name']}")
        print(f"  EN: {case['english']}")
        print(f"  ZH: {case['chinese']}")
        
        # Run validation
        validation = translator._validate_translation_quality(case['english'], case['chinese'])
        score = validation['quality_score']
        warnings = validation['warnings']
        
        print(f"  Score: {score:.3f}")
        if warnings:
            print(f"  Warnings: {'; '.join(warnings)}")
        else:
            print(f"  Warnings: None")
        
        # Check if score is in expected range
        min_score, max_score = case['expected_score_range']
        score_ok = min_score <= score <= max_score
        
        print(f"  Expected: {min_score}-{max_score} → {'✅' if score_ok else '❌'}")
        
        # Check specific expectations
        checks_passed = 0
        total_checks = 0
        
        if 'should_find_mindfulness' in case:
            total_checks += 1
            # Should find "正念" in translation
            found = '正念' in case['chinese']
            if found:
                checks_passed += 1
                print(f"  ✅ Found mindfulness term")
            else:
                print(f"  ❌ Missing mindfulness term")
        
        if 'should_find_present' in case:
            total_checks += 1
            # Should find "此刻" or "当下" in translation
            found = '此刻' in case['chinese'] or '当下' in case['chinese']
            if found:
                checks_passed += 1
                print(f"  ✅ Found present moment term")
            else:
                print(f"  ❌ Missing present moment term")
        
        if 'should_warn_missing' in case:
            total_checks += 1
            # Should have terminology warning
            has_term_warning = any('terminology' in w.lower() for w in warnings)
            if has_term_warning:
                checks_passed += 1
                print(f"  ✅ Correctly detected missing terminology")
            else:
                print(f"  ❌ Failed to detect missing terminology")
        
        if 'should_warn_short' in case:
            total_checks += 1
            # Should have length warning
            has_length_warning = any('short' in w.lower() for w in warnings)
            if has_length_warning:
                checks_passed += 1
                print(f"  ✅ Correctly detected short translation")
            else:
                print(f"  ❌ Failed to detect short translation")
        
        if 'should_warn_english' in case:
            total_checks += 1
            # Should have English words warning
            has_english_warning = any('english' in w.lower() for w in warnings)
            if has_english_warning:
                checks_passed += 1
                print(f"  ✅ Correctly detected English words")
            else:
                print(f"  ❌ Failed to detect English words")
        
        if 'should_be_perfect' in case:
            total_checks += 1
            # Should have no warnings and high score
            if not warnings and score >= 0.95:
                checks_passed += 1
                print(f"  ✅ Perfect translation detected")
            else:
                print(f"  ❌ Not detected as perfect (warnings: {len(warnings)}, score: {score})")
        
        # Overall result
        overall_pass = score_ok and (checks_passed == total_checks)
        results.append({
            'name': case['name'],
            'score': score,
            'expected_range': case['expected_score_range'],
            'score_ok': score_ok,
            'checks_passed': checks_passed,
            'total_checks': total_checks,
            'overall_pass': overall_pass,
            'warnings': warnings
        })
        
        print(f"  Result: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        print()
    
    # Summary
    passed = sum(1 for r in results if r['overall_pass'])
    total = len(results)
    
    print(f"📊 Test Summary:")
    print(f"  Passed: {passed}/{total}")
    print(f"  Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print(f"🎉 All quality score tests PASSED!")
    else:
        print(f"⚠️  Some tests failed. Quality score needs further tuning.")
        
        print(f"\nFailed tests:")
        for r in results:
            if not r['overall_pass']:
                print(f"  - {r['name']}: score={r['score']:.3f}, expected={r['expected_range']}")
    
    return passed == total

def main():
    """Main test function"""
    print("🧘 Quality Score Validation Testing")
    print("=" * 50)
    
    # Check if terminology file exists
    terminology_file = Path(__file__).parent.parent / 'data' / 'terminology' / 'terminology_enhanced_simple.json'
    if not terminology_file.exists():
        print(f"⚠️  Terminology file not found: {terminology_file}")
        sys.exit(1)
    
    print(f"✅ Terminology file found")
    print()
    
    # Run test
    success = test_quality_score_improvements()
    
    if success:
        print(f"\n💡 Quality score improvements:")
        print(f"   • More flexible terminology detection")
        print(f"   • Adjusted length thresholds for Chinese")
        print(f"   • Critical vs non-critical term penalties")
        print(f"   • Better compound term handling")
    else:
        print(f"\n🔧 Quality score needs further refinement")

if __name__ == "__main__":
    main()

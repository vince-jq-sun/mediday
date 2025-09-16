#!/usr/bin/env python3
"""
Create manual translations for TTS testing since Google Translate API is not enabled
"""
import json
from pathlib import Path

def create_manual_translations():
    """Create translation file with manual Chinese translations"""
    
    # Manual translations for the transcribed English text
    translations = {
        "original_file": "temp/test_input/test_sample.mp3",
        "total_segments": 3,
        "translation_provider": "manual",
        "segments": [
            {
                "segment_id": 0,
                "start_time": 0.0,
                "end_time": 7.75,
                "duration": 7.75,
                "file_path": "/Users/vince/Documents/mediday/temp/segments/test_sample/test_sample_segment_000.wav",
                "english_text": "Remind yourself. That you're here. You're awake and aware.",
                "chinese_text": "提醒自己。你在这里。你是清醒和觉知的。",
                "translation_metadata": {
                    "original_text": "Remind yourself. That you're here. You're awake and aware.",
                    "translated_text": "提醒自己。你在这里。你是清醒和觉知的。",
                    "confidence": 1.0,
                    "provider": "manual"
                }
            },
            {
                "segment_id": 1,
                "start_time": 12.31,
                "end_time": 21.1,
                "duration": 8.79,
                "file_path": "/Users/vince/Documents/mediday/temp/segments/test_sample/test_sample_segment_001.wav",
                "english_text": "And spend his first few moments of the meditation just settling. And sensing into being here.",
                "chinese_text": "花前几分钟的冥想时间来安定下来。感受存在于此刻。",
                "translation_metadata": {
                    "original_text": "And spend his first few moments of the meditation just settling. And sensing into being here.",
                    "translated_text": "花前几分钟的冥想时间来安定下来。感受存在于此刻。",
                    "confidence": 1.0,
                    "provider": "manual"
                }
            },
            {
                "segment_id": 2,
                "start_time": 24.83,
                "end_time": 30.0,
                "duration": 5.17,
                "file_path": "/Users/vince/Documents/mediday/temp/segments/test_sample/test_sample_segment_002.wav",
                "english_text": "Sense of being awake in the midst of this moment.",
                "chinese_text": "感受在这一刻中保持清醒的状态。",
                "translation_metadata": {
                    "original_text": "Sense of being awake in the midst of this moment.",
                    "translated_text": "感受在这一刻中保持清醒的状态。",
                    "confidence": 1.0,
                    "provider": "manual"
                }
            }
        ]
    }
    
    # Save manual translations
    output_file = Path("temp/translations/test_sample_translations_manual.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Manual translations saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    create_manual_translations()

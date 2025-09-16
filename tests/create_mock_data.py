#!/usr/bin/env python3
"""
Create mock data to test the pipeline flow without Google Cloud APIs
"""
import json
from pathlib import Path

def create_mock_transcription():
    """Create mock transcription data"""
    print("Creating mock transcription data...")
    
    # Create transcripts directory
    transcripts_dir = Path("temp/transcripts")
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock transcription data based on our test audio segments
    mock_transcription = {
        "original_file": "test_sample.mp3",
        "segments": [
            {
                "segment_id": 0,
                "start_time": 0.0,
                "end_time": 15.5,
                "duration": 15.5,
                "file_path": "temp/segments/test_sample/test_sample_segment_000.wav",
                "transcription": {
                    "file_path": "temp/segments/test_sample/test_sample_segment_000.wav",
                    "language_code": "en-US",
                    "transcripts": [
                        {
                            "transcript": "Take a moment to notice your breath. Feel the air flowing in and out of your lungs naturally.",
                            "confidence": 0.95
                        }
                    ],
                    "full_transcript": "Take a moment to notice your breath. Feel the air flowing in and out of your lungs naturally.",
                    "word_details": []
                }
            },
            {
                "segment_id": 1,
                "start_time": 18.5,
                "end_time": 35.2,
                "duration": 16.7,
                "file_path": "temp/segments/test_sample/test_sample_segment_001.wav",
                "transcription": {
                    "file_path": "temp/segments/test_sample/test_sample_segment_001.wav",
                    "language_code": "en-US",
                    "transcripts": [
                        {
                            "transcript": "Allow yourself to be present in this moment. Notice any thoughts that arise without judgment.",
                            "confidence": 0.92
                        }
                    ],
                    "full_transcript": "Allow yourself to be present in this moment. Notice any thoughts that arise without judgment.",
                    "word_details": []
                }
            },
            {
                "segment_id": 2,
                "start_time": 38.2,
                "end_time": 50.0,
                "duration": 11.8,
                "file_path": "temp/segments/test_sample/test_sample_segment_002.wav",
                "transcription": {
                    "file_path": "temp/segments/test_sample/test_sample_segment_002.wav",
                    "language_code": "en-US",
                    "transcripts": [
                        {
                            "transcript": "Simply return your attention to your breath whenever your mind wanders.",
                            "confidence": 0.89
                        }
                    ],
                    "full_transcript": "Simply return your attention to your breath whenever your mind wanders.",
                    "word_details": []
                }
            }
        ],
        "total_segments": 3
    }
    
    # Save mock transcription
    output_file = transcripts_dir / "test_sample_transcriptions.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mock_transcription, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Mock transcription saved to: {output_file}")
    return output_file

def create_mock_translation():
    """Create mock translation data"""
    print("Creating mock translation data...")
    
    # Create translations directory
    translations_dir = Path("temp/translations")
    translations_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock translation data
    mock_translation = {
        "original_file": "test_sample.mp3",
        "source_language": "en",
        "target_language": "zh-CN",
        "segments": [
            {
                "segment_id": 0,
                "start_time": 0.0,
                "end_time": 15.5,
                "duration": 15.5,
                "file_path": "temp/segments/test_sample/test_sample_segment_000.wav",
                "original_text": "Take a moment to notice your breath. Feel the air flowing in and out of your lungs naturally.",
                "translated_text": "花一点时间注意你的呼吸。感受空气自然地流入和流出你的肺部。",
                "confidence": 0.95,
                "manual_review": False,
                "manual_recording": None
            },
            {
                "segment_id": 1,
                "start_time": 18.5,
                "end_time": 35.2,
                "duration": 16.7,
                "file_path": "temp/segments/test_sample/test_sample_segment_001.wav",
                "original_text": "Allow yourself to be present in this moment. Notice any thoughts that arise without judgment.",
                "translated_text": "允许自己活在当下。不加判断地注意任何出现的想法。",
                "confidence": 0.92,
                "manual_review": False,
                "manual_recording": None
            },
            {
                "segment_id": 2,
                "start_time": 38.2,
                "end_time": 50.0,
                "duration": 11.8,
                "file_path": "temp/segments/test_sample/test_sample_segment_002.wav",
                "original_text": "Simply return your attention to your breath whenever your mind wanders.",
                "translated_text": "每当你的心思游离时，只需将注意力回到呼吸上。",
                "confidence": 0.89,
                "manual_review": False,
                "manual_recording": None
            }
        ],
        "total_segments": 3,
        "terminology_applied": True
    }
    
    # Save mock translation
    output_file = translations_dir / "test_sample_translations.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mock_translation, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Mock translation saved to: {output_file}")
    return output_file

def create_mock_synthesis():
    """Create mock synthesis data"""
    print("Creating mock synthesis data...")
    
    # Create synthesis directory
    synthesis_dir = Path("temp/synthesis")
    synthesis_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock synthesis data
    mock_synthesis = {
        "original_file": "test_sample.mp3",
        "voice_settings": {
            "voice_name": "zh-CN-Wavenet-A",
            "speaking_rate": 1.0,
            "pitch": 0.0
        },
        "segments": [
            {
                "segment_id": 0,
                "text": "花一点时间注意你的呼吸。感受空气自然地流入和流出你的肺部。",
                "audio_file": "temp/synthesis/test_sample_segment_000_synthesized.mp3",
                "duration": 8.5,
                "success": True
            },
            {
                "segment_id": 1,
                "text": "允许自己活在当下。不加判断地注意任何出现的想法。",
                "audio_file": "temp/synthesis/test_sample_segment_001_synthesized.mp3",
                "duration": 9.2,
                "success": True
            },
            {
                "segment_id": 2,
                "text": "每当你的心思游离时，只需将注意力回到呼吸上。",
                "audio_file": "temp/synthesis/test_sample_segment_002_synthesized.mp3",
                "duration": 7.8,
                "success": True
            }
        ],
        "total_segments": 3,
        "total_duration": 25.5
    }
    
    # Save mock synthesis
    output_file = synthesis_dir / "test_sample_synthesis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mock_synthesis, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Mock synthesis saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    print("Creating mock data for pipeline testing...\n")
    
    transcription_file = create_mock_transcription()
    translation_file = create_mock_translation()
    synthesis_file = create_mock_synthesis()
    
    print(f"\n=== Mock Data Created Successfully ===")
    print(f"Transcription: {transcription_file}")
    print(f"Translation: {translation_file}")
    print(f"Synthesis: {synthesis_file}")
    print(f"\nYou can now test the GUI with:")
    print(f"python -m scripts.audio_pipeline.pipeline gui --translation-file {translation_file}")

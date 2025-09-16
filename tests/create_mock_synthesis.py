#!/usr/bin/env python3
"""
Create mock synthesized audio files and metadata for testing
"""
import json
from pathlib import Path
import shutil

def create_mock_synthesis_files():
    """Create mock synthesis results with actual audio files"""
    
    # Create synthesis directory
    synthesis_dir = Path("temp/synthesis")
    synthesis_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy original segments as mock synthesized audio (for testing purposes)
    segments_dir = Path("temp/segments/test_sample")
    
    mock_synthesis_data = {
        "original_file": "temp/test_input/test_sample.mp3",
        "total_segments": 3,
        "voice_settings": {
            "voice_name": "zh-CN-Wavenet-A",
            "speaking_rate": 1.0,
            "pitch": 0.0
        },
        "segments": []
    }
    
    chinese_texts = [
        "提醒自己。你在这里。你是清醒和觉知的。",
        "花前几分钟的冥想时间来安定下来。感受存在于此刻。", 
        "感受在这一刻中保持清醒的状态。"
    ]
    
    for i in range(3):
        # Copy original segment as mock synthesized audio
        source_file = segments_dir / f"test_sample_segment_{i:03d}.wav"
        target_file = synthesis_dir / f"test_sample_segment_{i:03d}_synthesized.mp3"
        
        if source_file.exists():
            # Convert WAV to MP3 using ffmpeg (mock synthesis)
            import subprocess
            try:
                subprocess.run([
                    'ffmpeg', '-i', str(source_file), 
                    '-acodec', 'mp3', '-y', str(target_file)
                ], check=True, capture_output=True)
                
                duration = 7.5 + i * 1.2  # Mock durations
                
                segment_data = {
                    "segment_id": i,
                    "chinese_text": chinese_texts[i],
                    "synthesis_result": {
                        "text": chinese_texts[i],
                        "output_path": str(target_file),
                        "duration": duration,
                        "success": True
                    }
                }
                
                print(f"✓ Created mock synthesized audio: {target_file}")
                
            except subprocess.CalledProcessError as e:
                segment_data = {
                    "segment_id": i,
                    "chinese_text": chinese_texts[i],
                    "synthesis_result": {
                        "text": chinese_texts[i],
                        "output_path": "",
                        "error": f"ffmpeg error: {e}",
                        "success": False
                    }
                }
                print(f"✗ Failed to create mock audio for segment {i}")
        else:
            segment_data = {
                "segment_id": i,
                "chinese_text": chinese_texts[i],
                "synthesis_result": {
                    "text": chinese_texts[i],
                    "output_path": "",
                    "error": "Source segment not found",
                    "success": False
                }
            }
            print(f"✗ Source segment not found: {source_file}")
        
        mock_synthesis_data["segments"].append(segment_data)
    
    # Save synthesis results
    output_file = synthesis_dir / "test_sample_synthesis_mock.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mock_synthesis_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Mock synthesis metadata saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    create_mock_synthesis_files()

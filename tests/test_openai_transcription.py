#!/usr/bin/env python3
"""
Test script for OpenAI Whisper transcription API.
Tests transcription on audio files in temp/segments/test_sample/ directory.
"""

import json
import os
import sys
from openai import OpenAI

def load_openai_config():
    """Load OpenAI API key from config file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'openai.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('api')
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file {config_path}")
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def get_audio_files():
    """Get list of audio files in test_sample directory."""
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'temp', 'segments', 'test_sample')
    
    if not os.path.exists(test_dir):
        print(f"Error: Test directory not found at {test_dir}")
        return []
    
    audio_files = []
    for file in os.listdir(test_dir):
        if file.endswith('.wav'):
            audio_files.append(os.path.join(test_dir, file))
    
    return sorted(audio_files)

def transcribe_audio(client, audio_file_path):
    """Transcribe a single audio file using OpenAI Whisper."""
    try:
        print(f"Transcribing: {os.path.basename(audio_file_path)}")
        
        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"  # Assuming English audio based on the project context
            )
        
        return transcript.text
        
    except Exception as e:
        print(f"Error transcribing {audio_file_path}: {e}")
        return None

def test_openai_transcription():
    """Test OpenAI Whisper transcription on test audio files."""
    # Load API key
    api_key = load_openai_config()
    if not api_key:
        print("Failed to load OpenAI API key")
        return False
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return False
    
    # Get audio files
    audio_files = get_audio_files()
    if not audio_files:
        print("No audio files found in test_sample directory")
        return False
    
    print(f"Found {len(audio_files)} audio files to transcribe")
    print("=" * 60)
    
    results = []
    success_count = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {os.path.basename(audio_file)}")
        print("-" * 40)
        
        # Get file size for reference
        file_size = os.path.getsize(audio_file)
        print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Transcribe
        transcript = transcribe_audio(client, audio_file)
        
        if transcript:
            print(f"✅ Transcription successful!")
            print(f"Text: \"{transcript}\"")
            print(f"Length: {len(transcript)} characters")
            
            results.append({
                'file': os.path.basename(audio_file),
                'transcript': transcript,
                'success': True
            })
            success_count += 1
        else:
            print(f"❌ Transcription failed!")
            results.append({
                'file': os.path.basename(audio_file),
                'transcript': None,
                'success': False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("TRANSCRIPTION SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(audio_files)}")
    print(f"Successful transcriptions: {success_count}")
    print(f"Failed transcriptions: {len(audio_files) - success_count}")
    
    if success_count > 0:
        print("\nAll transcriptions:")
        for i, result in enumerate(results, 1):
            if result['success']:
                print(f"{i}. {result['file']}: \"{result['transcript']}\"")
    
    return success_count == len(audio_files)

def main():
    """Main function to run the transcription test."""
    print("OpenAI Whisper Transcription API Test")
    print("=" * 60)
    
    success = test_openai_transcription()
    
    if success:
        print("\n🎉 All transcriptions completed successfully!")
    else:
        print("\n💥 Some transcriptions failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

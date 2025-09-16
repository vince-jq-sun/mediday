#!/usr/bin/env python3
"""
Simple test for Google Speech-to-Text API
"""
import os
from google.cloud import speech
from pathlib import Path

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json'

def test_stt_with_segment():
    """Test STT with one of our audio segments"""
    client = speech.SpeechClient()
    
    # Use one of the generated segments
    audio_file = Path('temp/segments/test_sample/test_sample_segment_000.wav')
    
    if not audio_file.exists():
        print(f"Audio file not found: {audio_file}")
        return
    
    print(f"Testing with audio file: {audio_file}")
    print(f"File size: {audio_file.stat().st_size} bytes")
    
    # Read audio content
    with open(audio_file, 'rb') as f:
        content = f.read()
    
    # Configure for WAV format
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,  # Match our audio format
        language_code="en-US",
        enable_automatic_punctuation=True,
    )
    
    print("Sending request to Google Speech-to-Text API...")
    
    try:
        response = client.recognize(config=config, audio=audio)
        
        print("Response received!")
        
        if response.results:
            for i, result in enumerate(response.results):
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence
                print(f"Segment {i+1}: {transcript}")
                print(f"Confidence: {confidence:.2f}")
        else:
            print("No speech detected in audio")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_stt_with_segment()

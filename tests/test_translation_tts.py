#!/usr/bin/env python3
"""
Test translation and TTS without waiting for STT
"""
import os
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from pathlib import Path

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json'

def test_translation():
    """Test Google Translate API with sample text"""
    print("=== Testing Translation API ===")
    
    try:
        client = translate.Client()
        
        # Sample English mindfulness text
        sample_text = "Take a moment to notice your breath. Feel the air flowing in and out of your lungs naturally."
        
        print(f"Original text: {sample_text}")
        
        result = client.translate(
            sample_text,
            source_language='en',
            target_language='zh-CN'
        )
        
        translated_text = result['translatedText']
        print(f"Translated text: {translated_text}")
        
        return translated_text
        
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def test_text_to_speech(text):
    """Test Google Text-to-Speech API"""
    print("\n=== Testing Text-to-Speech API ===")
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="zh-CN",
            name="zh-CN-Wavenet-A"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        print("Synthesizing speech...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save the audio
        output_file = Path("temp/test_tts_output.mp3")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, "wb") as f:
            f.write(response.audio_content)
        
        print(f"✓ Audio saved to: {output_file}")
        print(f"File size: {output_file.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"TTS error: {e}")
        return False

def list_available_voices():
    """List available Chinese voices"""
    print("\n=== Available Chinese Voices ===")
    
    try:
        client = texttospeech.TextToSpeechClient()
        voices = client.list_voices()
        
        chinese_voices = []
        for voice in voices.voices:
            if any('zh' in lang for lang in voice.language_codes):
                chinese_voices.append({
                    'name': voice.name,
                    'gender': voice.ssml_gender.name,
                    'rate': voice.natural_sample_rate_hertz
                })
        
        for voice in chinese_voices[:5]:  # Show first 5
            print(f"  {voice['name']} ({voice['gender']}) - {voice['rate']}Hz")
            
        return chinese_voices
        
    except Exception as e:
        print(f"Voice listing error: {e}")
        return []

if __name__ == "__main__":
    print("Testing Google Cloud Translation and TTS APIs...\n")
    
    # Test translation
    translated_text = test_translation()
    
    if translated_text:
        # Test TTS with translated text
        test_text_to_speech(translated_text)
    else:
        # Test TTS with sample Chinese text
        sample_chinese = "花一点时间注意你的呼吸。感受空气自然地流入和流出你的肺部。"
        test_text_to_speech(sample_chinese)
    
    # List available voices
    list_available_voices()
    
    print("\n=== Test Complete ===")

"""
Google Speech-to-Text integration for audio transcription
"""
from google.cloud import speech
from pathlib import Path
import json
from typing import Dict, List
import io
import wave
import time
import os
from .config import (
    STT_LANGUAGE_CODE, 
    STT_ENCODING, 
    TRANSCRIPTS_DIR,
    GOOGLE_CLOUD_PROJECT_ID
)

class SpeechRecognizer:
    def __init__(self):
        # Use REST transport to avoid gRPC network issues
        self.client = speech.SpeechClient(transport="rest")
        
    def get_wav_metadata(self, audio_path: Path) -> tuple:
        """Get WAV file metadata (sample_rate, channels, sample_width, duration)"""
        with wave.open(str(audio_path), 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth() * 8  # Convert to bits
            duration = wf.getnframes() / sample_rate
        return sample_rate, channels, sample_width, duration
        
    def transcribe_audio_file(self, audio_path: Path) -> Dict:
        """
        Transcribe a single audio file using Google Speech-to-Text
        """
        try:
            # Get audio metadata
            sample_rate, channels, sample_width, duration = self.get_wav_metadata(audio_path)
            file_size = audio_path.stat().st_size
            
            print(f"  Audio info: {duration:.2f}s, {sample_rate}Hz, {channels}ch, {sample_width}bit, {file_size} bytes")
            
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            # Configure recognition based on actual audio properties
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=STT_LANGUAGE_CODE,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                audio_channel_count=channels,
                enable_separate_recognition_per_channel=False,
            )
            
            # Choose sync vs async based on duration and file size
            use_long_running = duration > 58 or file_size > 9_000_000
            
            print(f"  Using {'long-running' if use_long_running else 'synchronous'} recognition...")
            
            # Perform recognition with timeout
            start_time = time.time()
            if use_long_running:
                operation = self.client.long_running_recognize(config=config, audio=audio)
                response = operation.result(timeout=180)
            else:
                response = self.client.recognize(config=config, audio=audio, timeout=30)
            
            elapsed_time = time.time() - start_time
            print(f"  Recognition completed in {elapsed_time:.1f}s")
            
            # Process results
            transcription_data = {
                'file_path': str(audio_path),
                'language_code': STT_LANGUAGE_CODE,
                'transcripts': [],
                'word_details': [],
                'processing_time': elapsed_time,
                'audio_duration': duration
            }
            
            if not response.results:
                print(f"  No speech detected in {audio_path.name}")
                transcription_data['full_transcript'] = ''
                return transcription_data
            
            for i, result in enumerate(response.results, 1):
                # Get the most confident alternative
                alternative = result.alternatives[0]
                
                transcript_info = {
                    'transcript': alternative.transcript,
                    'confidence': alternative.confidence
                }
                transcription_data['transcripts'].append(transcript_info)
                
                print(f"  [{i}] {alternative.transcript} (confidence: {alternative.confidence:.2f})")
                
                # Extract word-level timing if available
                if hasattr(alternative, 'words'):
                    for word_info in alternative.words:
                        word_detail = {
                            'word': word_info.word,
                            'start_time': word_info.start_time.total_seconds(),
                            'end_time': word_info.end_time.total_seconds()
                        }
                        transcription_data['word_details'].append(word_detail)
            
            # Combine all transcripts
            full_transcript = ' '.join([t['transcript'] for t in transcription_data['transcripts']])
            transcription_data['full_transcript'] = full_transcript
            
            return transcription_data
            
        except Exception as e:
            print(f"  Error transcribing {audio_path.name}: {e}")
            print(f"  Troubleshooting tips:")
            print(f"    - Network timeout: Check internet connection or use VPN")
            print(f"    - Audio format: Ensure WAV is 16-bit PCM")
            print(f"    - API access: Verify Google Cloud credentials and billing")
            return {
                'file_path': str(audio_path),
                'error': str(e),
                'full_transcript': ''
            }
    
    def transcribe_segments(self, metadata: Dict) -> Dict:
        """
        Transcribe all segments from audio preprocessing metadata
        """
        results = {
            'original_file': metadata['original_file'],
            'segments': [],
            'total_segments': metadata['total_segments']
        }
        
        for segment in metadata['audio_segments']:
            segment_path = Path(segment['file_path'])
            
            print(f"Transcribing segment {segment['segment_id'] + 1}/{metadata['total_segments']}: {segment_path.name}")
            
            transcription = self.transcribe_audio_file(segment_path)
            
            segment_result = {
                'segment_id': segment['segment_id'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'transcription': transcription
            }
            
            results['segments'].append(segment_result)
            
            if transcription.get('full_transcript'):
                print(f"  → Transcribed: {transcription['full_transcript'][:100]}...")
            else:
                print(f"  → Error: {transcription.get('error', 'Unknown error')}")
        
        # Save transcription results
        output_path = TRANSCRIPTS_DIR / f"{Path(metadata['original_file']).stem}_transcriptions.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def batch_transcribe_directory(self, segments_dir: Path) -> List[Dict]:
        """
        Batch transcribe all segmented audio files in a directory
        """
        results = []
        
        # Find all metadata files (including in subdirectories)
        metadata_files = list(segments_dir.rglob("*_metadata.json"))
        
        if not metadata_files:
            print(f"No metadata files found in {segments_dir}")
            return results
        
        for metadata_file in metadata_files:
            print(f"\nProcessing metadata: {metadata_file}")
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            transcription_results = self.transcribe_segments(metadata)
            results.append(transcription_results)
        
        return results

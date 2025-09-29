"""Speech-to-Text integration supporting Google STT, OpenAI Whisper, and Local Whisper"""
from pathlib import Path
import json
from typing import Dict, List
import io
import wave
import time
import os
import subprocess
import tempfile
import shutil
from openai import OpenAI

# Optional Google Cloud import
try:
    from google.cloud import speech
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    speech = None
from .config import (
    STT_LANGUAGE_CODE, 
    STT_ENCODING, 
    TRANSCRIPTS_DIR,
    GOOGLE_CLOUD_PROJECT_ID,
    OPENAI_CONFIG_PATH
)

class SpeechRecognizer:
    def __init__(self, provider="localwhisper"):
        """
        Initialize speech recognizer with specified provider
        Args:
            provider (str): "google" for Google STT, "openai" for OpenAI Whisper, or "localwhisper" for Local Whisper
        """
        self.provider = provider.lower()
        
        if self.provider == "google":
            if not GOOGLE_AVAILABLE:
                raise ValueError("Google Cloud Speech library not available. Install with: pip install google-cloud-speech")
            # Use REST transport to avoid gRPC network issues
            self.client = speech.SpeechClient(transport="rest")
        elif self.provider == "openai":
            # Load OpenAI API key
            api_key = self._load_openai_config()
            if not api_key:
                raise ValueError("OpenAI API key not found. Please check config/openai.json")
            self.client = OpenAI(api_key=api_key)
        elif self.provider == "localwhisper":
            # Initialize local whisper settings
            self._init_local_whisper()
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'google', 'openai', or 'localwhisper'")
    
    def _load_openai_config(self):
        """Load OpenAI API key from config file."""
        try:
            with open(OPENAI_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            return config.get('api')
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    def _init_local_whisper(self):
        """Initialize local whisper settings"""
        # Default paths based on test_whisper_local.sh
        self.model_path = os.path.expanduser("~/.cache/huggingface/hub/models--ggerganov--whisper.cpp/snapshots/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-large-v3.bin")
        self.whisper_bin = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
        self.lang_opt = "en"
        self.nthread = 4
        self.disable_gpu = False
        self.pause_threshold = 1.0
        
        # Check if model and binary exist
        if not os.path.exists(self.model_path):
            raise ValueError(f"Local Whisper model not found: {self.model_path}")
        if not os.path.exists(self.whisper_bin):
            raise ValueError(f"Local Whisper binary not found: {self.whisper_bin}. Please compile whisper.cpp with GGML_METAL=1")
        
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
        Transcribe a single audio file using the configured provider
        """
        if self.provider == "google":
            return self._transcribe_with_google(audio_path)
        elif self.provider == "openai":
            return self._transcribe_with_openai(audio_path)
        elif self.provider == "localwhisper":
            return self._transcribe_with_local_whisper(audio_path)
    
    def _transcribe_with_openai(self, audio_path: Path) -> Dict:
        """
        Transcribe a single audio file using OpenAI Whisper
        """
        try:
            # Get audio metadata for info
            sample_rate, channels, sample_width, duration = self.get_wav_metadata(audio_path)
            file_size = audio_path.stat().st_size
            
            print(f"  Audio info: {duration:.2f}s, {sample_rate}Hz, {channels}ch, {sample_width}bit, {file_size} bytes")
            print(f"  Using OpenAI Whisper...")
            
            start_time = time.time()
            
            # Transcribe with OpenAI Whisper
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # Based on project context
                )
            
            elapsed_time = time.time() - start_time
            print(f"  Recognition completed in {elapsed_time:.1f}s")
            
            # Format results to match Google STT structure
            transcription_data = {
                'file_path': str(audio_path),
                'language_code': 'en-US',
                'provider': 'openai',
                'transcripts': [{
                    'transcript': transcript.text,
                    'confidence': 1.0  # OpenAI doesn't provide confidence scores
                }],
                'word_details': [],  # OpenAI basic API doesn't provide word-level timing
                'processing_time': elapsed_time,
                'audio_duration': duration,
                'full_transcript': transcript.text
            }
            
            if transcript.text:
                print(f"  Transcribed: {transcript.text}")
            else:
                print(f"  No speech detected in {audio_path.name}")
            
            return transcription_data
            
        except Exception as e:
            print(f"  Error transcribing {audio_path.name} with OpenAI: {e}")
            print(f"  Troubleshooting tips:")
            print(f"    - Check OpenAI API key in config/openai.json")
            print(f"    - Verify internet connection")
            print(f"    - Ensure audio file is valid")
            return {
                'file_path': str(audio_path),
                'provider': 'openai',
                'error': str(e),
                'full_transcript': ''
            }
    
    def _transcribe_with_google(self, audio_path: Path) -> Dict:
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
                'provider': 'google',
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
                'provider': 'google',
                'error': str(e),
                'full_transcript': ''
            }
    
    def _transcribe_with_local_whisper(self, audio_path: Path) -> Dict:
        """
        Transcribe a single audio file using Local Whisper (whisper.cpp)
        """
        try:
            # Get audio metadata for info
            sample_rate, channels, sample_width, duration = self.get_wav_metadata(audio_path)
            file_size = audio_path.stat().st_size
            
            print(f"  Audio info: {duration:.2f}s, {sample_rate}Hz, {channels}ch, {sample_width}bit, {file_size} bytes")
            print(f"  Using Local Whisper (whisper.cpp)...")
            
            start_time = time.time()
            
            # Create temporary directory for whisper outputs
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Normalize audio to 16kHz mono PCM16 (required by whisper.cpp)
                normalized_wav = temp_path / f"{audio_path.stem}.wav"
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", str(audio_path),
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                    str(normalized_wav)
                ]
                
                subprocess.run(ffmpeg_cmd, check=True)
                
                # Prepare whisper command
                output_stem = temp_path / audio_path.stem
                whisper_cmd = [
                    self.whisper_bin,
                    "-m", self.model_path,
                    "-f", str(normalized_wav),
                    "-l", self.lang_opt,
                    "-t", str(self.nthread),
                    "-otxt", "-osrt", "-ojf",
                    "--output-words",
                    "-of", str(output_stem),
                    "-bs", "5",
                    "-tp", "0.2",
                    "--max-context", "256",
                    "--suppress-nst", "0",
                    "--prompt", " "
                ]
                
                # Add GPU flag if disabled
                if self.disable_gpu:
                    whisper_cmd.append("--no-gpu")
                
                # Run whisper
                result = subprocess.run(whisper_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise RuntimeError(f"Whisper failed with exit code {result.returncode}: {result.stderr}")
                
                elapsed_time = time.time() - start_time
                print(f"  Recognition completed in {elapsed_time:.1f}s")
                
                # Read generated files
                json_file = temp_path / f"{audio_path.stem}.json"
                srt_file = temp_path / f"{audio_path.stem}.srt"
                txt_file = temp_path / f"{audio_path.stem}.txt"
                
                # Read transcript text
                full_transcript = ""
                if txt_file.exists():
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        full_transcript = f.read().strip()
                
                # Use whisper_output_integrator to process JSON and SRT
                integrated_json = temp_path / f"{audio_path.stem}_integrated.json"
                if json_file.exists() and srt_file.exists():
                    # Import and use the integrator
                    from ..whisper_output_integrator import integrate_whisper_outputs
                    integrate_whisper_outputs(
                        str(json_file), 
                        str(srt_file), 
                        str(integrated_json), 
                        self.pause_threshold
                    )
                
                # Read integrated data if available
                integrated_data = None
                if integrated_json.exists():
                    with open(integrated_json, 'r', encoding='utf-8') as f:
                        integrated_data = json.load(f)
                
                # Format results to match other providers
                transcription_data = {
                    'file_path': str(audio_path),
                    'language_code': 'en-US',
                    'provider': 'localwhisper',
                    'transcripts': [{
                        'transcript': full_transcript,
                        'confidence': 1.0  # Local whisper doesn't provide confidence scores
                    }],
                    'word_details': integrated_data.get('words', []) if integrated_data else [],
                    'processing_time': elapsed_time,
                    'audio_duration': duration,
                    'full_transcript': full_transcript,
                    'integrated_data': integrated_data  # Store full integrated data
                }
                
                if full_transcript:
                    print(f"  Transcribed: {full_transcript}")
                else:
                    print(f"  No speech detected in {audio_path.name}")
                
                return transcription_data
                
        except Exception as e:
            print(f"  Error transcribing {audio_path.name} with Local Whisper: {e}")
            print(f"  Troubleshooting tips:")
            print(f"    - Check whisper.cpp binary: {self.whisper_bin}")
            print(f"    - Check model file: {self.model_path}")
            print(f"    - Ensure ffmpeg is installed")
            return {
                'file_path': str(audio_path),
                'provider': 'localwhisper',
                'error': str(e),
                'full_transcript': ''
            }
    
    def transcribe_segments(self, metadata: Dict, output_dir: Path = None) -> Dict:
        """
        Transcribe all segments from audio preprocessing metadata
        """
        results = {
            'original_file': metadata['original_file'],
            'segments': [],
            'total_segments': metadata['total_segments']
        }
        
        # Create individual_segments directory for storing integrated JSONs
        if output_dir is None:
            output_dir = TRANSCRIPTS_DIR
        individual_segments_dir = output_dir / "individual_segments"
        individual_segments_dir.mkdir(parents=True, exist_ok=True)
        
        for segment in metadata['audio_segments']:
            segment_path = Path(segment['file_path'])
            
            print(f"Transcribing segment {segment['segment_id'] + 1}/{metadata['total_segments']}: {segment_path.name}")
            
            transcription = self.transcribe_audio_file(segment_path)
            
            # For localwhisper, save individual integrated JSON and clean up temp files
            if self.provider == "localwhisper" and transcription.get('integrated_data'):
                # Save individual integrated JSON
                integrated_json_path = individual_segments_dir / f"{segment_path.stem}_integrated.json"
                with open(integrated_json_path, 'w', encoding='utf-8') as f:
                    json.dump(transcription['integrated_data'], f, indent=2, ensure_ascii=False)
                print(f"  → Saved integrated JSON: {integrated_json_path}")
            
            # Create segment result with full_transcript as text_wt_pause version
            text_wt_pause = transcription.get('integrated_data', {}).get('sentence_wt_pause', transcription.get('full_transcript', '')) if transcription.get('integrated_data') else transcription.get('full_transcript', '')
            original_transcript = transcription.get('full_transcript', '')
            
            segment_result = {
                'segment_id': segment['segment_id'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'file_path': segment['file_path'],
                'transcription': {
                    'provider': transcription.get('provider'),
                    'full_transcript': text_wt_pause,  # 带停顿标记的版本
                    'transcript': original_transcript,  # 原始版本（不带停顿）
                    'processing_time': transcription.get('processing_time', 0),
                    'audio_duration': transcription.get('audio_duration', 0)
                }
            }
            
            results['segments'].append(segment_result)
            
            if transcription.get('full_transcript'):
                print(f"  → Transcribed: {transcription['full_transcript'][:100]}...")
            else:
                print(f"  → Error: {transcription.get('error', 'Unknown error')}")
        
        # Save transcription results (without word details, using text_wt_pause)
        output_path = output_dir / f"{Path(metadata['original_file']).stem}_transcriptions.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Transcription completed. Results saved to: {output_path}")
        print(f"   Individual integrated JSONs saved to: {individual_segments_dir}")
        
        return results
    
    def batch_transcribe_directory(self, segments_dir: Path, output_dir: Path = None) -> List[Dict]:
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
            
            transcription_results = self.transcribe_segments(metadata, output_dir)
            results.append(transcription_results)
        
        return results

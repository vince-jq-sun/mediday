"""
Main pipeline script for the complete audio processing workflow
"""
import argparse
from pathlib import Path
import json
import os
from .config import ensure_directories, AWAKE_WHERE_YOU_ARE_DIR, TERMINOLOGY_FILE, STT_PROVIDER
from .audio_preprocessor import AudioPreprocessor
from .speech_recognition import SpeechRecognizer
from .translator import Translator
from .text_to_speech import TextToSpeechSynthesizer
from .audio_assembler import AudioAssembler
from .translation_gui import launch_translation_gui

class AudioProcessingPipeline:
    def __init__(self, terminology_file: Path = None, stt_provider: str = None, translation_provider: str = None):
        ensure_directories()
        
        # Use default STT provider from config if not specified
        if stt_provider is None:
            stt_provider = STT_PROVIDER
        
        self.preprocessor = AudioPreprocessor()
        self.speech_recognizer = SpeechRecognizer(provider=stt_provider)
        self.translator = Translator(terminology_file, provider=translation_provider)
        self.tts_synthesizer = TextToSpeechSynthesizer()
        self.assembler = AudioAssembler()
        self.stt_provider = stt_provider
        self.translation_provider = translation_provider
    
    def run_preprocessing(self, input_dir: Path, output_dir: Path = None, silence_threshold: float = None, min_segment_duration: float = None, sec_len_approx: float = 0.0, boundary_search: float = 3.0, normalize_padding: bool = True, target_padding: float = 1.0):
        """Step 1: Preprocess audio files (silence detection and segmentation)"""
        print("=== Step 1: Audio Preprocessing ===")
        if (silence_threshold is not None or min_segment_duration is not None) or (sec_len_approx is not None or boundary_search is not None) or (normalize_padding is not None or target_padding is not None):
            # Create a new preprocessor with the specified parameters
            kwargs = {}
            if silence_threshold is not None:
                kwargs['silence_threshold_seconds'] = silence_threshold
                print(f"Using silence threshold: {silence_threshold}s")
            if min_segment_duration is not None:
                kwargs['min_segment_duration'] = min_segment_duration
                print(f"Using minimum segment duration: {min_segment_duration}s")
            if sec_len_approx is not None:
                kwargs['sec_len_approx'] = sec_len_approx
                print(f"Approx section length: {sec_len_approx}s (0 disables)")
            if boundary_search is not None:
                kwargs['boundary_search'] = boundary_search
                print(f"Boundary search window: ±{boundary_search}s")
            if normalize_padding is not None:
                kwargs['normalize_padding'] = normalize_padding
                print(f"Audio padding normalization: {'enabled' if normalize_padding else 'disabled'}")
            if target_padding is not None:
                kwargs['target_padding'] = target_padding
                print(f"Target padding duration: {target_padding}s")
            preprocessor = AudioPreprocessor(**kwargs)
            results = preprocessor.process_directory(input_dir, output_dir)
        else:
            results = self.preprocessor.process_directory(input_dir, output_dir)
        print(f"Processed {len(results)} audio files")
        return results
    
    def run_transcription(self, segments_dir: Path, output_dir: Path = None):
        """Step 2: Transcribe audio segments to text"""
        print(f"\n=== Step 2: Speech Recognition ({self.stt_provider.upper()}) ===")
        results = self.speech_recognizer.batch_transcribe_directory(segments_dir, output_dir)
        print(f"Transcribed {len(results)} files using {self.stt_provider}")
        return results
    
    def run_translation(self, transcripts_dir: Path, output_dir: Path = None, context_window: int = 1, include_previous_translations: bool = True):
        """Step 3: Translate English text to Chinese"""
        provider_name = self.translation_provider or 'google'
        print(f"\n=== Step 3: Translation ({provider_name.upper()}) ===")
        
        if provider_name == 'gpt':
            print(f"   Context window: {context_window}")
            print(f"   Previous translations in context: {'Yes' if include_previous_translations else 'No'}")
            results = self.translator.batch_translate_directory(
                transcripts_dir, 
                output_dir=output_dir,
                use_context=True,
                include_previous_translations=include_previous_translations,
                context_window=context_window
            )
        else:
            results = self.translator.batch_translate_directory(transcripts_dir, output_dir=output_dir)
        
        print(f"Translated {len(results)} files using {provider_name}")
        return results
    
    def run_synthesis(self, translations_dir: Path, output_dir: Path = None, voice_settings: dict = None, use_pause_aware: bool = True):
        """Step 4: Synthesize Chinese text to speech"""
        print("\n=== Step 4: Speech Synthesis ===")
        if use_pause_aware:
            print("Using pause-aware synthesis for texts with pause markers")
        results = self.tts_synthesizer.batch_synthesize_directory(translations_dir, output_dir, voice_settings, use_pause_aware)
        print(f"Synthesized {len(results)} files")
        return results
    
    def run_assembly(self, translation_file: Path, synthesis_file: Path = None, 
                    output_path: Path = None, prefer_manual: bool = True, 
                    manual_recordings_dir: Path = None, enable_volume_scaling: bool = True):
        """Step 5: Assemble final audio"""
        print("\n=== Step 5: Audio Assembly ===")
        
        if enable_volume_scaling:
            print("Volume scaling enabled: matching original segment volumes")
        else:
            print("Volume scaling disabled: using original audio levels")
        
        with open(translation_file, 'r', encoding='utf-8') as f:
            translation_data = json.load(f)
        
        if synthesis_file and synthesis_file.exists():
            with open(synthesis_file, 'r', encoding='utf-8') as f:
                synthesis_data = json.load(f)
            
            result = self.assembler.create_mixed_assembly(
                translation_data, synthesis_data, output_path, prefer_manual,
                manual_recordings_dir=manual_recordings_dir,
                enable_volume_scaling=enable_volume_scaling
            )
        else:
            result = self.assembler.assemble_from_manual_recordings(
                translation_data, output_path, manual_recordings_dir=manual_recordings_dir,
                enable_volume_scaling=enable_volume_scaling
            )
        
        if result['success']:
            print(f"Final audio saved to: {result['output_path']}")
            print(f"Duration: {result['total_duration']:.1f}s")
            print(f"File size: {result['file_size'] / 1024 / 1024:.1f} MB")
            
            if 'source_breakdown' in result:
                breakdown = result['source_breakdown']
                print(f"Manual recordings: {breakdown['manual_recordings']}")
                print(f"Synthesized audio: {breakdown['synthesized_audio']}")
        else:
            print(f"Assembly failed: {result['error']}")
        
        return result
    
    def run_full_pipeline(self, input_dir: Path, terminology_file: Path = None, voice_settings: dict = None):
        """Run the complete pipeline"""
        provider_name = self.translation_provider or 'google'
        print(f"Starting complete audio processing pipeline (STT: {self.stt_provider}, Translation: {provider_name})...")
        
        # Step 1: Preprocessing
        preprocessing_results = self.run_preprocessing(input_dir)
        
        if not preprocessing_results:
            print("No audio files processed. Exiting.")
            return
        
        # Step 2: Transcription
        from .config import SEGMENTS_DIR
        transcription_results = self.run_transcription(SEGMENTS_DIR)
        
        # Step 3: Translation
        from .config import TRANSCRIPTS_DIR
        translation_results = self.run_translation(TRANSCRIPTS_DIR)
        
        # Step 4: Synthesis
        from .config import TRANSLATIONS_DIR
        synthesis_results = self.run_synthesis(TRANSLATIONS_DIR, voice_settings)
        
        print("\n=== Pipeline Complete ===")
        print("Next steps:")
        print("1. Run the GUI for manual review and recording:")
        print("   python -m scripts.audio_pipeline.pipeline gui")
        print("2. Assemble final audio:")
        print("   python -m scripts.audio_pipeline.pipeline assemble")

def main():
    parser = argparse.ArgumentParser(description="Audio Processing Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Run complete pipeline')
    full_parser.add_argument('--input-dir', type=Path, default=AWAKE_WHERE_YOU_ARE_DIR,
                           help='Input directory with audio files')
    full_parser.add_argument('--terminology', type=Path,
                           help='Terminology file for translation')
    full_parser.add_argument('--stt-provider', choices=['google', 'openai', 'localwhisper'], default='localwhisper',
                           help='Speech-to-text provider (google, openai, or localwhisper)')
    full_parser.add_argument('--translation-provider', choices=['google', 'gpt', 'llm', 'gemini', 'anthropic', 'local'], default='google',
                           help='Translation provider (google or gpt)')
    full_parser.add_argument('--voice', default='cmn-CN-Chirp3-HD-Achird',
                           help='TTS voice name')
    full_parser.add_argument('--speaking-rate', type=float, default=1.0,
                           help='TTS speaking rate')
    full_parser.add_argument('--pitch', type=float, default=0.0,
                           help='TTS pitch adjustment')
    
    # Individual step commands
    preprocess_parser = subparsers.add_parser('preprocess', help='Audio preprocessing only')
    preprocess_parser.add_argument('--input-dir', type=Path, required=True,
                                 help='Input directory with audio files')
    preprocess_parser.add_argument('--output-dir', type=Path,
                                 help='Output directory for segmented audio files')
    preprocess_parser.add_argument('--silence-threshold', type=float, default=3.0,
                                 help='Silence threshold in seconds for segmentation (default: 3.0)')
    preprocess_parser.add_argument('--min-segment-duration', type=float, default=0.5,
                                 help='Minimum segment duration in seconds (default: 0.5)')
    preprocess_parser.add_argument('--sec-len-approx', type=float, default=0.0,
                                 help='Approximate section length in seconds. If >= 10, ignore silence-threshold mode and cut near multiples of this length by searching for longest silence within the boundary window (default: 0 = disabled)')
    preprocess_parser.add_argument('--boundary-search', type=float, default=3.0,
                                 help='Search window (±seconds) around target cut time to find the longest silence when --sec-len-approx >= 10 (default: 3.0)')
    preprocess_parser.add_argument('--no-normalize-padding', action='store_true',
                                 help='Disable audio padding normalization (keep original front/back silence)')
    preprocess_parser.add_argument('--target-padding', type=float, default=1.0,
                                 help='Target padding duration in seconds for front and back of audio (default: 1.0)')
    
    transcribe_parser = subparsers.add_parser('transcribe', help='Speech recognition only')
    transcribe_parser.add_argument('--segments-dir', type=Path,
                                 help='Directory with segmented audio files')
    transcribe_parser.add_argument('--output-dir', type=Path,
                                 help='Output directory for transcription files')
    transcribe_parser.add_argument('--stt-provider', choices=['google', 'openai', 'localwhisper'], default='localwhisper',
                                 help='Speech-to-text provider (google, openai, or localwhisper)')
    
    translate_parser = subparsers.add_parser('translate', help='Translation only')
    translate_parser.add_argument('--transcripts-dir', type=Path,
                                help='Directory with transcription files')
    translate_parser.add_argument('--output-dir', type=Path,
                                help='Output directory for translation files')
    translate_parser.add_argument('--terminology', type=Path,
                                help='Terminology file for translation')
    translate_parser.add_argument('--provider', choices=['google', 'gpt', 'llm', 'gemini', 'anthropic', 'local'], default='google',
                                help='Translation provider (google or gpt)')
    translate_parser.add_argument('--context-window', type=int, default=1,
                                help='Context window size for GPT translation (number of surrounding segments)')
    translate_parser.add_argument('--no-previous-translations', action='store_true',
                                help='Disable including previous translations in context for GPT')
    translate_parser.add_argument('--model', default='gpt-4o-mini',
                                help='GPT model to use (gpt-4o, gpt-4o-mini, etc.)')
    translate_parser.add_argument('--enhanced', action='store_true',
                                help='Use enhanced GPT translator with better terminology handling')
    
    synthesize_parser = subparsers.add_parser('synthesize', help='Speech synthesis only')
    synthesize_parser.add_argument('--translations-dir', type=Path,
                                 help='Directory with translation files')
    synthesize_parser.add_argument('--output-dir', type=Path,
                                 help='Output directory for synthesis files')
    synthesize_parser.add_argument('--voice', default='cmn-CN-Chirp3-HD-Achird',
                                 help='TTS voice name')
    synthesize_parser.add_argument('--speaking-rate', type=float, default=1.0,
                                 help='TTS speaking rate')
    synthesize_parser.add_argument('--pitch', type=float, default=0.0,
                                 help='TTS pitch adjustment')
    synthesize_parser.add_argument('--no-pause-aware', action='store_true',
                                 help='Disable pause-aware synthesis (treat pause markers as regular text)')
    
    # GUI command
    gui_parser = subparsers.add_parser('gui', help='Launch translation review GUI')
    gui_parser.add_argument('--translation-file', type=Path,
                          help='Translation file to review')
    
    # Assembly command
    assemble_parser = subparsers.add_parser('assemble', help='Assemble final audio')
    assemble_parser.add_argument('--translation-file', type=Path, required=True,
                               help='Translation file')
    assemble_parser.add_argument('--synthesis-file', type=Path,
                               help='Synthesis results file')
    assemble_parser.add_argument('--manual-recordings-dir', type=Path,
                               help='Directory containing manual recordings')
    assemble_parser.add_argument('--output', type=Path,
                               help='Output audio file path')
    assemble_parser.add_argument('--prefer-synthesis', action='store_true',
                               help='Prefer synthesized audio over manual recordings')
    assemble_parser.add_argument('--no-volume-scaling', action='store_true',
                               help='Disable volume scaling to match original segments')
    
    # List voices command
    voices_parser = subparsers.add_parser('voices', help='List available TTS voices')
    voices_parser.add_argument('--language', default='zh-CN',
                             help='Language code for voices')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'full':
            voice_settings = {
                'voice_name': args.voice,
                'speaking_rate': args.speaking_rate,
                'pitch': args.pitch
            }
            pipeline = AudioProcessingPipeline(args.terminology, args.stt_provider, args.translation_provider)
            pipeline.run_full_pipeline(args.input_dir, args.terminology, voice_settings)
        
        elif args.command == 'preprocess':
            pipeline = AudioProcessingPipeline()
            pipeline.run_preprocessing(
                args.input_dir,
                args.output_dir,
                args.silence_threshold,
                args.min_segment_duration,
                args.sec_len_approx,
                args.boundary_search,
                not args.no_normalize_padding,  # normalize_padding
                args.target_padding,
            )
        
        elif args.command == 'transcribe':
            from .config import SEGMENTS_DIR
            segments_dir = args.segments_dir or SEGMENTS_DIR
            pipeline = AudioProcessingPipeline(stt_provider=args.stt_provider)
            pipeline.run_transcription(segments_dir, args.output_dir)
        
        elif args.command == 'translate':
            from .config import TRANSCRIPTS_DIR
            transcripts_dir = args.transcripts_dir or TRANSCRIPTS_DIR
            terminology_file = args.terminology or TERMINOLOGY_FILE
            
            # Set environment variables for GPT configuration
            if args.provider == 'gpt':
                os.environ['GPT_MODEL'] = args.model
                os.environ['USE_ENHANCED_GPT'] = 'true' if args.enhanced else 'false'
            
            # GPT-specific parameters
            context_window = args.context_window
            include_previous_translations = not args.no_previous_translations
            pipeline = AudioProcessingPipeline(terminology_file, translation_provider=args.provider)
            pipeline.run_translation(transcripts_dir, args.output_dir, context_window, include_previous_translations)
        
        elif args.command == 'synthesize':
            from .config import TRANSLATIONS_DIR
            translations_dir = args.translations_dir or TRANSLATIONS_DIR
            voice_settings = {
                'voice_name': args.voice,
                'speaking_rate': args.speaking_rate,
                'pitch': args.pitch
            }
            use_pause_aware = not args.no_pause_aware
            pipeline = AudioProcessingPipeline()
            pipeline.run_synthesis(translations_dir, args.output_dir, voice_settings, use_pause_aware)
        
        elif args.command == 'gui':
            launch_translation_gui(args.translation_file)
        
        elif args.command == 'assemble':
            pipeline = AudioProcessingPipeline()
            prefer_manual = not args.prefer_synthesis
            enable_volume_scaling = not args.no_volume_scaling
            pipeline.run_assembly(args.translation_file, args.synthesis_file,
                                args.output, prefer_manual, args.manual_recordings_dir,
                                enable_volume_scaling)
        
        elif args.command == 'voices':
            from .text_to_speech import TextToSpeechSynthesizer
            tts = TextToSpeechSynthesizer()
            voices = tts.get_available_voices(args.language)
            
            print(f"Available voices for {args.language}:")
            for voice in voices:
                print(f"  {voice['name']} ({voice['ssml_gender']}) - {voice['natural_sample_rate_hertz']}Hz")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

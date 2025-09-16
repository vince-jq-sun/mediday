"""
Main pipeline script for the complete audio processing workflow
"""
import argparse
from pathlib import Path
import json
from .config import ensure_directories, AWAKE_WHERE_YOU_ARE_DIR
from .audio_preprocessor import AudioPreprocessor
from .speech_recognition import SpeechRecognizer
from .translator import Translator
from .text_to_speech import TextToSpeechSynthesizer
from .audio_assembler import AudioAssembler
from .translation_gui import launch_translation_gui

class AudioProcessingPipeline:
    def __init__(self, terminology_file: Path = None):
        ensure_directories()
        
        self.preprocessor = AudioPreprocessor()
        self.speech_recognizer = SpeechRecognizer()
        self.translator = Translator(terminology_file)
        self.tts_synthesizer = TextToSpeechSynthesizer()
        self.assembler = AudioAssembler()
    
    def run_preprocessing(self, input_dir: Path, output_dir: Path = None):
        """Step 1: Preprocess audio files (silence detection and segmentation)"""
        print("=== Step 1: Audio Preprocessing ===")
        results = self.preprocessor.process_directory(input_dir, output_dir)
        print(f"Processed {len(results)} audio files")
        return results
    
    def run_transcription(self, segments_dir: Path):
        """Step 2: Transcribe audio segments to text"""
        print("\n=== Step 2: Speech Recognition ===")
        results = self.speech_recognizer.batch_transcribe_directory(segments_dir)
        print(f"Transcribed {len(results)} files")
        return results
    
    def run_translation(self, transcripts_dir: Path):
        """Step 3: Translate English text to Chinese"""
        print("\n=== Step 3: Translation ===")
        results = self.translator.batch_translate_directory(transcripts_dir)
        print(f"Translated {len(results)} files")
        return results
    
    def run_synthesis(self, translations_dir: Path, voice_settings: dict = None):
        """Step 4: Synthesize Chinese text to speech"""
        print("\n=== Step 4: Speech Synthesis ===")
        results = self.tts_synthesizer.batch_synthesize_directory(translations_dir, voice_settings)
        print(f"Synthesized {len(results)} files")
        return results
    
    def run_assembly(self, translation_file: Path, synthesis_file: Path = None, 
                    output_path: Path = None, prefer_manual: bool = True):
        """Step 5: Assemble final audio"""
        print("\n=== Step 5: Audio Assembly ===")
        
        with open(translation_file, 'r', encoding='utf-8') as f:
            translation_data = json.load(f)
        
        if synthesis_file and synthesis_file.exists():
            with open(synthesis_file, 'r', encoding='utf-8') as f:
                synthesis_data = json.load(f)
            
            result = self.assembler.create_mixed_assembly(
                translation_data, synthesis_data, output_path, prefer_manual
            )
        else:
            result = self.assembler.assemble_from_manual_recordings(
                translation_data, output_path
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
    
    def run_full_pipeline(self, input_dir: Path, terminology_file: Path = None,
                         voice_settings: dict = None):
        """Run the complete pipeline"""
        print("Starting complete audio processing pipeline...")
        
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
    full_parser.add_argument('--voice', default='zh-CN-Wavenet-A',
                           help='TTS voice name')
    full_parser.add_argument('--speaking-rate', type=float, default=1.0,
                           help='TTS speaking rate')
    full_parser.add_argument('--pitch', type=float, default=0.0,
                           help='TTS pitch adjustment')
    
    # Individual step commands
    preprocess_parser = subparsers.add_parser('preprocess', help='Audio preprocessing only')
    preprocess_parser.add_argument('--input-dir', type=Path, required=True,
                                 help='Input directory with audio files')
    
    transcribe_parser = subparsers.add_parser('transcribe', help='Speech recognition only')
    transcribe_parser.add_argument('--segments-dir', type=Path,
                                 help='Directory with segmented audio files')
    
    translate_parser = subparsers.add_parser('translate', help='Translation only')
    translate_parser.add_argument('--transcripts-dir', type=Path,
                                help='Directory with transcription files')
    translate_parser.add_argument('--terminology', type=Path,
                                help='Terminology file for translation')
    
    synthesize_parser = subparsers.add_parser('synthesize', help='Speech synthesis only')
    synthesize_parser.add_argument('--translations-dir', type=Path,
                                 help='Directory with translation files')
    synthesize_parser.add_argument('--voice', default='zh-CN-Wavenet-A',
                                 help='TTS voice name')
    synthesize_parser.add_argument('--speaking-rate', type=float, default=1.0,
                                 help='TTS speaking rate')
    synthesize_parser.add_argument('--pitch', type=float, default=0.0,
                                 help='TTS pitch adjustment')
    
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
    assemble_parser.add_argument('--output', type=Path,
                               help='Output audio file path')
    assemble_parser.add_argument('--prefer-synthesis', action='store_true',
                               help='Prefer synthesized audio over manual recordings')
    
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
            pipeline = AudioProcessingPipeline(args.terminology)
            pipeline.run_full_pipeline(args.input_dir, args.terminology, voice_settings)
        
        elif args.command == 'preprocess':
            pipeline = AudioProcessingPipeline()
            pipeline.run_preprocessing(args.input_dir)
        
        elif args.command == 'transcribe':
            from .config import SEGMENTS_DIR
            segments_dir = args.segments_dir or SEGMENTS_DIR
            pipeline = AudioProcessingPipeline()
            pipeline.run_transcription(segments_dir)
        
        elif args.command == 'translate':
            from .config import TRANSCRIPTS_DIR
            transcripts_dir = args.transcripts_dir or TRANSCRIPTS_DIR
            pipeline = AudioProcessingPipeline(args.terminology)
            pipeline.run_translation(transcripts_dir)
        
        elif args.command == 'synthesize':
            from .config import TRANSLATIONS_DIR
            translations_dir = args.translations_dir or TRANSLATIONS_DIR
            voice_settings = {
                'voice_name': args.voice,
                'speaking_rate': args.speaking_rate,
                'pitch': args.pitch
            }
            pipeline = AudioProcessingPipeline()
            pipeline.run_synthesis(translations_dir, voice_settings)
        
        elif args.command == 'gui':
            launch_translation_gui(args.translation_file)
        
        elif args.command == 'assemble':
            pipeline = AudioProcessingPipeline()
            prefer_manual = not args.prefer_synthesis
            pipeline.run_assembly(args.translation_file, args.synthesis_file,
                                args.output, prefer_manual)
        
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

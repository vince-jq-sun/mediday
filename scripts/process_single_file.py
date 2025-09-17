#!/usr/bin/env python3
"""
Simple script to process a single audio file through the complete pipeline
"""
import sys
import argparse
from pathlib import Path
import shutil
import tempfile
import json

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from audio_pipeline.pipeline import AudioProcessingPipeline
from audio_pipeline.config import ensure_directories

def process_single_file(input_file: Path, output_dir: Path = None, 
                       translation_provider: str = "gpt", 
                       stt_provider: str = "google",
                       terminology_file: Path = None,
                       context_window: int = 1,
                       voice_name: str = "zh-CN-Wavenet-A"):
    """
    Process a single audio file through the complete pipeline
    
    Args:
        input_file: Path to the input audio file
        output_dir: Directory to save results (default: same as input file)
        translation_provider: Translation provider (gpt, google, etc.)
        stt_provider: Speech-to-text provider (google, openai)
        terminology_file: Custom terminology file
        context_window: Context window for GPT translation
        voice_name: TTS voice name
    """
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    if not input_file.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac']:
        raise ValueError(f"Unsupported audio format: {input_file.suffix}")
    
    # Set up output directory
    if output_dir is None:
        output_dir = input_file.parent / f"{input_file.stem}_processed"
    
    output_dir.mkdir(exist_ok=True)
    
    print(f"🎵 Processing single file: {input_file.name}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🔤 Translation: {translation_provider}")
    print(f"🎙️  STT: {stt_provider}")
    print("=" * 50)
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy input file to temp directory
        temp_input_dir = temp_path / "input"
        temp_input_dir.mkdir()
        temp_input_file = temp_input_dir / input_file.name
        shutil.copy2(input_file, temp_input_file)
        
        # Initialize pipeline
        ensure_directories()
        pipeline = AudioProcessingPipeline(
            terminology_file=terminology_file,
            stt_provider=stt_provider,
            translation_provider=translation_provider
        )
        
        try:
            # Step 1: Preprocessing
            print("\n🔧 Step 1: Audio Preprocessing...")
            preprocessing_results = pipeline.run_preprocessing(temp_input_dir)
            
            if not preprocessing_results:
                print("❌ No segments created during preprocessing")
                return False
            
            # Step 2: Transcription
            print("\n🎤 Step 2: Speech Recognition...")
            from audio_pipeline.config import SEGMENTS_DIR
            transcription_results = pipeline.run_transcription(SEGMENTS_DIR)
            
            # Step 3: Translation
            print(f"\n🌐 Step 3: Translation ({translation_provider})...")
            from audio_pipeline.config import TRANSCRIPTS_DIR
            if translation_provider == 'gpt':
                translation_results = pipeline.run_translation(
                    TRANSCRIPTS_DIR, 
                    context_window=context_window,
                    include_previous_translations=True
                )
            else:
                translation_results = pipeline.run_translation(TRANSCRIPTS_DIR)
            
            # Step 4: Synthesis
            print("\n🔊 Step 4: Speech Synthesis...")
            from audio_pipeline.config import TRANSLATIONS_DIR
            voice_settings = {'voice_name': voice_name}
            synthesis_results = pipeline.run_synthesis(TRANSLATIONS_DIR, voice_settings)
            
            # Copy results to output directory
            print(f"\n📋 Copying results to {output_dir}...")
            
            # Copy all result files
            from audio_pipeline.config import (SEGMENTS_DIR, TRANSCRIPTS_DIR, 
                                             TRANSLATIONS_DIR, SYNTHESIS_DIR)
            
            result_dirs = {
                'segments': SEGMENTS_DIR,
                'transcripts': TRANSCRIPTS_DIR, 
                'translations': TRANSLATIONS_DIR,
                'synthesis': SYNTHESIS_DIR
            }
            
            for name, source_dir in result_dirs.items():
                if source_dir.exists():
                    target_dir = output_dir / name
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(source_dir, target_dir)
                    print(f"  ✅ {name}: {len(list(target_dir.glob('*')))} files")
            
            # Create summary file
            summary = {
                'input_file': str(input_file),
                'processing_date': str(Path().cwd()),
                'settings': {
                    'translation_provider': translation_provider,
                    'stt_provider': stt_provider,
                    'context_window': context_window if translation_provider == 'gpt' else None,
                    'voice_name': voice_name
                },
                'results': {
                    'segments_count': len(preprocessing_results) if preprocessing_results else 0,
                    'transcripts_count': len(transcription_results) if transcription_results else 0,
                    'translations_count': len(translation_results) if translation_results else 0,
                    'synthesis_count': len(synthesis_results) if synthesis_results else 0
                }
            }
            
            summary_file = output_dir / 'processing_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"\n🎉 Processing complete!")
            print(f"📊 Summary saved to: {summary_file}")
            print(f"\n📝 Next steps:")
            print(f"   1. Review translations: python run_pipeline.py gui --translation-file {output_dir}/translations/*.json")
            print(f"   2. Assemble final audio: python run_pipeline.py assemble --translation-file {output_dir}/translations/*.json")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Process a single audio file through the complete pipeline")
    
    parser.add_argument('input_file', type=Path, help='Input audio file to process')
    parser.add_argument('--output-dir', type=Path, help='Output directory (default: input_file_processed)')
    parser.add_argument('--translation-provider', choices=['google', 'gpt', 'llm'], default='gpt',
                       help='Translation provider (default: gpt)')
    parser.add_argument('--stt-provider', choices=['google', 'openai'], default='google',
                       help='Speech-to-text provider (default: google)')
    parser.add_argument('--terminology', type=Path, help='Custom terminology file')
    parser.add_argument('--context-window', type=int, default=1,
                       help='Context window for GPT translation (default: 1)')
    parser.add_argument('--voice', default='zh-CN-Wavenet-A',
                       help='TTS voice name (default: zh-CN-Wavenet-A)')
    
    args = parser.parse_args()
    
    try:
        success = process_single_file(
            input_file=args.input_file,
            output_dir=args.output_dir,
            translation_provider=args.translation_provider,
            stt_provider=args.stt_provider,
            terminology_file=args.terminology,
            context_window=args.context_window,
            voice_name=args.voice
        )
        
        if success:
            print("\n✅ Single file processing completed successfully!")
        else:
            print("\n❌ Single file processing failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

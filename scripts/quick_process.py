#!/usr/bin/env python3
"""
Quick and easy audio processing script with smart file detection
"""
import sys
import argparse
from pathlib import Path
import glob

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from process_single_file import process_single_file

def find_audio_files(path_pattern: str) -> list:
    """
    Smart audio file detection from various input patterns
    
    Args:
        path_pattern: File path, directory, or glob pattern
        
    Returns:
        List of audio file paths
    """
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
    files = []
    
    # Convert to Path object
    path = Path(path_pattern)
    
    # Case 1: Exact file path
    if path.is_file() and path.suffix.lower() in audio_extensions:
        files.append(path)
    
    # Case 2: Directory - find all audio files
    elif path.is_dir():
        for ext in audio_extensions:
            files.extend(path.glob(f"*{ext}"))
            files.extend(path.glob(f"*{ext.upper()}"))
    
    # Case 3: Glob pattern
    else:
        glob_files = glob.glob(path_pattern)
        for file_path in glob_files:
            file_obj = Path(file_path)
            if file_obj.is_file() and file_obj.suffix.lower() in audio_extensions:
                files.append(file_obj)
    
    # Remove duplicates and sort
    files = sorted(list(set(files)))
    return files

def main():
    """Main entry point with smart file detection"""
    parser = argparse.ArgumentParser(
        description="Quick audio processing with smart file detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python quick_process.py audio.mp3
  
  # Process all audio files in directory
  python quick_process.py /path/to/audio/
  
  # Process specific files with pattern
  python quick_process.py "*.mp3"
  python quick_process.py "day*.wav"
  
  # Use GPT translation with custom settings
  python quick_process.py audio.mp3 --gpt --context 2
  
  # Batch process with custom output
  python quick_process.py /audio/dir/ --output /results/ --voice zh-CN-Wavenet-B
        """
    )
    
    parser.add_argument('input', help='Audio file, directory, or glob pattern')
    parser.add_argument('--output', type=Path, help='Output base directory')
    
    # Quick preset options
    parser.add_argument('--gpt', action='store_true', help='Use GPT translation (shortcut)')
    parser.add_argument('--google', action='store_true', help='Use Google translation (shortcut)')
    
    # Detailed options
    parser.add_argument('--translation-provider', choices=['google', 'gpt', 'llm'], 
                       help='Translation provider')
    parser.add_argument('--stt-provider', choices=['google', 'openai'], default='openai',
                       help='Speech-to-text provider (default: openai)')
    parser.add_argument('--context', type=int, default=1,
                       help='Context window for GPT translation (default: 1)')
    parser.add_argument('--voice', default='zh-CN-Wavenet-A',
                       help='TTS voice name')
    parser.add_argument('--terminology', type=Path, help='Custom terminology file')
    
    # Processing options
    parser.add_argument('--dry-run', action='store_true', help='Show files to process without processing')
    parser.add_argument('--continue-on-error', action='store_true', help='Continue processing other files if one fails')
    
    args = parser.parse_args()
    
    # Determine translation provider
    if args.gpt:
        translation_provider = 'gpt'
    elif args.google:
        translation_provider = 'google'
    elif args.translation_provider:
        translation_provider = args.translation_provider
    else:
        translation_provider = 'gpt'  # Default to GPT
    
    print(f"🔍 Searching for audio files: {args.input}")
    
    # Find audio files
    try:
        audio_files = find_audio_files(args.input)
    except Exception as e:
        print(f"❌ Error finding files: {e}")
        sys.exit(1)
    
    if not audio_files:
        print(f"❌ No audio files found matching: {args.input}")
        print(f"   Supported formats: .mp3, .wav, .m4a, .flac, .aac, .ogg")
        sys.exit(1)
    
    print(f"📁 Found {len(audio_files)} audio file(s):")
    for i, file_path in enumerate(audio_files, 1):
        size_mb = file_path.stat().st_size / 1024 / 1024
        print(f"   {i}. {file_path.name} ({size_mb:.1f} MB)")
    
    if args.dry_run:
        print(f"\n🏃 Dry run mode - no processing performed")
        print(f"   Translation provider: {translation_provider}")
        print(f"   STT provider: {args.stt_provider}")
        if translation_provider == 'gpt':
            print(f"   Context window: {args.context}")
        print(f"   Voice: {args.voice}")
        return
    
    print(f"\n🚀 Starting batch processing...")
    print(f"   Translation: {translation_provider}")
    print(f"   STT: {args.stt_provider}")
    if translation_provider == 'gpt':
        print(f"   Context window: {args.context}")
    print(f"   Voice: {args.voice}")
    print("=" * 50)
    
    # Process files
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(audio_files, 1):
        print(f"\n📂 Processing file {i}/{len(audio_files)}: {file_path.name}")
        
        # Determine output directory
        if args.output:
            output_dir = args.output / f"{file_path.stem}_processed"
        else:
            output_dir = file_path.parent / f"{file_path.stem}_processed"
        
        try:
            success = process_single_file(
                input_file=file_path,
                output_dir=output_dir,
                translation_provider=translation_provider,
                stt_provider=args.stt_provider,
                terminology_file=args.terminology,
                context_window=args.context,
                voice_name=args.voice
            )
            
            if success:
                successful += 1
                print(f"✅ {file_path.name} processed successfully")
            else:
                failed += 1
                print(f"❌ {file_path.name} processing failed")
                if not args.continue_on_error:
                    break
                    
        except Exception as e:
            failed += 1
            print(f"❌ Error processing {file_path.name}: {e}")
            if not args.continue_on_error:
                break
    
    # Summary
    print(f"\n📊 Batch Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total files: {len(audio_files)}")
    
    if successful > 0:
        print(f"\n🎉 Processing completed!")
        print(f"   Results saved in respective *_processed directories")
        print(f"\n📝 Next steps for each file:")
        print(f"   1. Review: python run_pipeline.py gui --translation-file <file>_processed/translations/*.json")
        print(f"   2. Assemble: python run_pipeline.py assemble --translation-file <file>_processed/translations/*.json")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()

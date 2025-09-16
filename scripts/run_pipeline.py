#!/usr/bin/env python3
"""
Simple runner script for the audio processing pipeline
"""
import sys
from pathlib import Path
import argparse

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from audio_pipeline.pipeline import main as pipeline_main

def main():
    """Main entry point"""
    print("🎵 Mediday Audio Processing Pipeline")
    print("=" * 40)
    
    # Override sys.argv to pass arguments to pipeline
    if len(sys.argv) == 1:
        # No arguments provided, show help
        sys.argv.append('--help')
    
    # Run the pipeline
    pipeline_main()

if __name__ == "__main__":
    main()

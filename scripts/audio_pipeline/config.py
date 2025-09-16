"""
Configuration settings for the audio processing pipeline
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
AUDIO_PIPELINE_DIR = SCRIPTS_DIR / "audio_pipeline"

# Input directories
AWAKE_WHERE_YOU_ARE_DIR = PROJECT_ROOT / "awake_where_you_are"
WAKING_UP_DIR = PROJECT_ROOT / "waking-up_intro-50_chinese"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"
SEGMENTS_DIR = TEMP_DIR / "segments"
TRANSCRIPTS_DIR = TEMP_DIR / "transcripts"
TRANSLATIONS_DIR = TEMP_DIR / "translations"
AUDIO_SYNTHESIS_DIR = TEMP_DIR / "synthesis"
MANUAL_RECORDINGS_DIR = TEMP_DIR / "manual_recordings"

# Audio processing settings
SILENCE_THRESHOLD_SECONDS = 3.0
AUDIO_FORMAT = "mp3"
SAMPLE_RATE = 44100

# Google Cloud settings
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

# Speech-to-Text settings
STT_LANGUAGE_CODE = "en-US"
STT_ENCODING = "MP3"

# Translation settings
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "zh-CN"

# Text-to-Speech settings
TTS_LANGUAGE_CODE = "zh-CN"
TTS_VOICE_NAME = "zh-CN-Wavenet-A"  # High quality voice
TTS_AUDIO_ENCODING = "MP3"

# GUI settings
GUI_SEGMENTS_PER_PAGE = 1
GUI_WINDOW_WIDTH = 1000
GUI_WINDOW_HEIGHT = 700

def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        OUTPUT_DIR,
        TEMP_DIR,
        SEGMENTS_DIR,
        TRANSCRIPTS_DIR,
        TRANSLATIONS_DIR,
        AUDIO_SYNTHESIS_DIR,
        MANUAL_RECORDINGS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

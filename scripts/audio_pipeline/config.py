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
DATA_DIR = PROJECT_ROOT / "data"
AWAKE_WHERE_YOU_ARE_DIR = PROJECT_ROOT / "awake_where_you_are"
WAKING_UP_DIR = DATA_DIR / "waking-up_intro-50_chinese"
TERMINOLOGY_DIR = DATA_DIR / "terminology"
TERMINOLOGY_FILE = TERMINOLOGY_DIR / "terminology_enhanced_simple.json"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"

# Legacy directories (kept for backward compatibility)
SEGMENTS_DIR = TEMP_DIR / "segments"
TRANSCRIPTS_DIR = TEMP_DIR / "transcripts"
TRANSLATIONS_DIR = TEMP_DIR / "translations"
AUDIO_SYNTHESIS_DIR = TEMP_DIR / "synthesis"
MANUAL_RECORDINGS_DIR = TEMP_DIR / "manual_recordings"

def get_project_paths(collection: str, project: str):
    """Get hierarchical project paths for new structure"""
    project_base = TEMP_DIR / collection / project
    return {
        'base': project_base,
        'segments': project_base / "segments",
        'transcripts': project_base / "transcripts",
        'translations': project_base / "translations",
        'recordings': project_base / "recordings",
        'syntheses': project_base / "syntheses",
        'outputs': project_base / "outputs"
    }

# Audio processing settings
SILENCE_THRESHOLD_SECONDS = 3.0
AUDIO_FORMAT = "mp3"
SAMPLE_RATE = 44100

# Google Cloud settings
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

# OpenAI settings
OPENAI_CONFIG_PATH = PROJECT_ROOT / "config" / "openai.json"

# Speech-to-Text settings
STT_PROVIDER = "openai"  # Default provider: "openai" or "google"
STT_LANGUAGE_CODE = "en-US"
STT_ENCODING = "MP3"

# Translation settings
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "zh-CN"
TRANSLATION_PROVIDER = os.getenv("TRANSLATION_PROVIDER", "gpt")  # Default to GPT
USE_ENHANCED_GPT = os.getenv("USE_ENHANCED_GPT", "true").lower() == "true"  # Default to enhanced GPT
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4.1-mini")  # Default model

# Text-to-Speech settings
TTS_LANGUAGE_CODE = "cmn-CN"
TTS_VOICE_NAME = "cmn-CN-Chirp3-HD-Achird"  # High quality voice that works
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

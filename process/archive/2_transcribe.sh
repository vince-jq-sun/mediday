#!/bin/bash
# Step 2: Speech Recognition (OpenAI Whisper or Google STT)
# Requires: Step 1 completed (segments in project segments directory)
# Usage: ./2_transcribe.sh [openai|google]

# Load project configuration
source process/project_config.sh

# Set default STT provider to OpenAI if not specified
# STT_PROVIDER=${1:-openai}
STT_PROVIDER=openai

# Validate provider choice
if [[ "$STT_PROVIDER" != "openai" && "$STT_PROVIDER" != "google" ]]; then
    echo "❌ Error: Invalid STT provider '$STT_PROVIDER'"
    echo "Usage: $0 [openai|google]"
    echo "  openai  - Use OpenAI Whisper (default, recommended)"
    echo "  google  - Use Google Speech-to-Text"
    exit 1
fi

echo "🎤 Step 2: Speech Recognition ($STT_PROVIDER)"
echo "====================================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"
echo "STT Provider: $STT_PROVIDER"

# Create transcripts directory
mkdir -p "$PROJECT_TRANSCRIPTS_DIR"

python -m scripts.audio_pipeline.pipeline transcribe \
    --segments-dir "$PROJECT_SEGMENTS_DIR" \
    --output-dir "$PROJECT_TRANSCRIPTS_DIR" \
    --stt-provider "$STT_PROVIDER"

echo "✅ Transcription completed using $STT_PROVIDER. Check $PROJECT_TRANSCRIPTS_FILE for results."

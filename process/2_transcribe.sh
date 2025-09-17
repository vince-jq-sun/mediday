#!/bin/bash
# Step 2: Speech Recognition (OpenAI Whisper)
# Requires: Step 1 completed (segments in project segments directory)

# Load project configuration
source process/project_config.sh

echo "🎤 Step 2: Speech Recognition (OpenAI)"
echo "====================================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"

# Create transcripts directory
mkdir -p "$PROJECT_TRANSCRIPTS_DIR"

python -m scripts.audio_pipeline.pipeline transcribe --segments-dir "$PROJECT_SEGMENTS_DIR" --output-dir "$PROJECT_TRANSCRIPTS_DIR"

echo "✅ Transcription completed. Check $PROJECT_TRANSCRIPTS_FILE for results."

#!/bin/bash
# Step 3: Translation (GPT)
# Requires: Step 2 completed (transcripts in project transcripts directory)

# Load project configuration
source process/project_config.sh

echo "🌐 Step 3: Translation (GPT)"
echo "============================"
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"

# Create translations directory
mkdir -p "$PROJECT_TRANSLATIONS_DIR"

# Clean variables to remove any newlines
CLEAN_TRANSCRIPTS_DIR=$(echo "$PROJECT_TRANSCRIPTS_DIR" | tr -d '\n\r')
CLEAN_TRANSLATIONS_DIR=$(echo "$PROJECT_TRANSLATIONS_DIR" | tr -d '\n\r')

python -m scripts.audio_pipeline.pipeline translate \
    --transcripts-dir "$CLEAN_TRANSCRIPTS_DIR" \
    --output-dir "$CLEAN_TRANSLATIONS_DIR" \
    --provider gpt \
    --enhanced \
    --context-window 1 \
    --model gpt-4.1-mini

echo "✅ Translation completed. Check $PROJECT_TRANSLATIONS_FILE for results."

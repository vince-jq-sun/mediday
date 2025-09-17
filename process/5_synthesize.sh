#!/bin/bash
# Step 5: Text-to-Speech Synthesis
# Requires: Step 3 completed (translations in project translations directory)

# Load project configuration
source process/project_config.sh

echo "🎵 Step 5: Text-to-Speech Synthesis"
echo "==================================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"

# Create syntheses directory
mkdir -p "$PROJECT_SYNTHESES_DIR"

# Clean variables to remove any newlines
CLEAN_TRANSLATIONS_DIR=$(echo "$PROJECT_TRANSLATIONS_DIR" | tr -d '\n\r')
CLEAN_SYNTHESES_DIR=$(echo "$PROJECT_SYNTHESES_DIR" | tr -d '\n\r')

python -m scripts.audio_pipeline.pipeline synthesize --translations-dir "$CLEAN_TRANSLATIONS_DIR" --output-dir "$CLEAN_SYNTHESES_DIR"

echo "✅ Synthesis completed. Check $PROJECT_SYNTHESIS_FILE for results."

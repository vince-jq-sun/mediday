#!/bin/bash
# Step 1: Audio Preprocessing (Silence Detection & Segmentation)

# Configurable silence threshold (in seconds)
# Adjust this value to control how long silence periods need to be before creating a segment break
SILENCE_THRESHOLD=3.0

# Load project configuration
source process/project_config.sh

echo "🔧 Step 1: Audio Preprocessing"
echo "=============================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"
echo "Silence Threshold: ${SILENCE_THRESHOLD}s"

# Create project-specific temp directories
mkdir -p "$PROJECT_BASE_DIR"
mkdir -p "$PROJECT_SEGMENTS_DIR"

# Clean and recreate single_file temp directory to ensure only current project file is processed
rm -rf temp/single_file
mkdir -p temp/single_file

# Copy source file to temp for processing
cp "$PROJECT_FILE" temp/single_file/

python -m scripts.audio_pipeline.pipeline preprocess --input-dir temp/single_file --output-dir "$PROJECT_SEGMENTS_DIR" --silence-threshold "$SILENCE_THRESHOLD"

echo "✅ Preprocessing completed. Check $PROJECT_SEGMENTS_DIR for results."

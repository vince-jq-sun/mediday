#!/bin/bash
# Step 1: Audio Preprocessing (Silence Detection & Segmentation)

# Load project configuration
source process/project_config.sh

echo "🔧 Step 1: Audio Preprocessing"
echo "=============================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"

# Create project-specific temp directories
mkdir -p "$PROJECT_BASE_DIR"
mkdir -p "$PROJECT_SEGMENTS_DIR"
mkdir -p temp/single_file

# Copy source file to temp for processing
cp "$PROJECT_FILE" temp/single_file/

python -m scripts.audio_pipeline.pipeline preprocess --input-dir temp/single_file --output-dir "$PROJECT_SEGMENTS_DIR"

echo "✅ Preprocessing completed. Check $PROJECT_SEGMENTS_DIR for results."

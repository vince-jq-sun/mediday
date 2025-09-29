#!/bin/bash
# Step 1: Audio Preprocessing (Silence Detection & Segmentation)

# Configurable silence threshold (in seconds)
# Adjust this value to control how long silence periods need to be before creating a segment break
SILENCE_THRESHOLD=0.5

# Minimum segment duration (in seconds)
# Segments shorter than this will be skipped to avoid extremely short/empty segments
MIN_SEGMENT_DURATION=0.5

# Approximate sectioning mode
# If SEC_LEN_APPROX >= 10, ignore silence-threshold-based segmentation and instead
# cut roughly every SEC_LEN_APPROX seconds by searching within ±BOUNDARY_SEARCH seconds
# for the longest silence to place the boundary.
SEC_LEN_APPROX=40
BOUNDARY_SEARCH=15

# Audio padding normalization settings
# NORMALIZE_PADDING: whether to standardize front/back silence to TARGET_PADDING seconds
# TARGET_PADDING: target duration for front and back silence (in seconds)
NORMALIZE_PADDING=true
TARGET_PADDING=1.0

# Load project configuration
source process/project_config.sh

echo "🔧 Step 1: Audio Preprocessing"
echo "=============================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"
echo "Silence Threshold: ${SILENCE_THRESHOLD}s"
echo "Min Segment Duration: ${MIN_SEGMENT_DURATION}s"
echo "Sec Len Approx: ${SEC_LEN_APPROX}s (>=10 enables approx-length mode; 0 disables)"
echo "Boundary Search: ±${BOUNDARY_SEARCH}s"
echo "Padding Normalization: ${NORMALIZE_PADDING}"
echo "Target Padding: ${TARGET_PADDING}s"

# Create project-specific temp directories
mkdir -p "$PROJECT_BASE_DIR"
mkdir -p "$PROJECT_SEGMENTS_DIR"

# Clean and recreate single_file temp directory to ensure only current project file is processed
rm -rf temp/single_file
mkdir -p temp/single_file

# Copy source file to temp for processing
cp "$PROJECT_FILE" temp/single_file/

# Build command with conditional padding parameters
PREPROCESS_CMD="python -m scripts.audio_pipeline.pipeline preprocess \
  --input-dir temp/single_file \
  --output-dir \"$PROJECT_SEGMENTS_DIR\" \
  --silence-threshold \"$SILENCE_THRESHOLD\" \
  --min-segment-duration \"$MIN_SEGMENT_DURATION\" \
  --sec-len-approx \"$SEC_LEN_APPROX\" \
  --boundary-search \"$BOUNDARY_SEARCH\""

# Add padding normalization parameters
if [ "$NORMALIZE_PADDING" = "false" ]; then
  PREPROCESS_CMD="$PREPROCESS_CMD --no-normalize-padding"
fi
PREPROCESS_CMD="$PREPROCESS_CMD --target-padding \"$TARGET_PADDING\""

# Execute the command
eval $PREPROCESS_CMD

echo "✅ Preprocessing completed. Check $PROJECT_SEGMENTS_DIR for results."

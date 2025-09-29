#!/bin/bash
# Step 6: Final Audio Assembly
# Requires: Step 5 completed (synthesis) and/or Step 4 completed (manual recordings)

# Load project configuration
source process/project_config.sh

# Volume scaling control (default: enabled)
ENABLE_VOLUME_SCALING=${ENABLE_VOLUME_SCALING:-true}

echo "🔧 Step 6: Final Audio Assembly with Volume Scaling"
echo "===================================================="
echo "Project: $CURRENT_PROJECT"
echo "Collection: $PROJECT_COLLECTION"
echo ""
if [[ "$ENABLE_VOLUME_SCALING" == "true" ]]; then
    echo "📊 Volume Scaling: Enabled (matching original segment volumes)"
    echo "   Each segment will be scaled to match its original volume"
    echo "   To disable: set ENABLE_VOLUME_SCALING=false"
    VOLUME_SCALING_ARG=""  # No argument needed when enabled (default behavior)
else
    echo "📊 Volume Scaling: Disabled"
    echo "   Using original audio levels without scaling"
    VOLUME_SCALING_ARG="--no-volume-scaling"
fi

# Check if required files exist
if [[ ! -f "$PROJECT_TRANSLATIONS_FILE" ]]; then
    echo "❌ Translation file not found: $PROJECT_TRANSLATIONS_FILE"
    exit 1
fi

# Create output directories
mkdir -p output
mkdir -p "$PROJECT_OUTPUTS_DIR"

# Check what audio sources are available
SYNTHESIZED_AVAILABLE=false
RECORDED_AVAILABLE=false

if [[ -f "$PROJECT_SYNTHESIS_FILE" ]]; then
    SYNTHESIZED_AVAILABLE=true
    echo "✅ Synthesized audio available: $PROJECT_SYNTHESIS_FILE"
fi

if [[ -d "$PROJECT_MANUAL_RECORDINGS_DIR" ]] && [[ -n "$(ls -A "$PROJECT_MANUAL_RECORDINGS_DIR" 2>/dev/null)" ]]; then
    RECORDED_AVAILABLE=true
    echo "✅ Manual recordings available: $PROJECT_MANUAL_RECORDINGS_DIR"
fi

if [[ "$SYNTHESIZED_AVAILABLE" == false ]] && [[ "$RECORDED_AVAILABLE" == false ]]; then
    echo "❌ No audio sources available. Run step 5 (synthesis) or step 4 (review-record) first."
    exit 1
fi

# Assemble synthesized version if available
if [[ "$SYNTHESIZED_AVAILABLE" == true ]]; then
    echo ""
    echo "🎵 Assembling synthesized version..."
    python -m scripts.audio_pipeline.pipeline assemble \
        --translation-file "$PROJECT_TRANSLATIONS_FILE" \
        --synthesis-file "$PROJECT_SYNTHESIS_FILE" \
        --output "$PROJECT_OUTPUT_SYNTHESIZED" \
        $VOLUME_SCALING_ARG
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Synthesized assembly completed: $PROJECT_OUTPUT_SYNTHESIZED"
        # Copy to global output directory
        cp "$PROJECT_OUTPUT_SYNTHESIZED" "$GLOBAL_OUTPUT_SYNTHESIZED"
        echo "   Also saved to: $GLOBAL_OUTPUT_SYNTHESIZED"
    else
        echo "❌ Synthesized assembly failed"
    fi
fi

# Assemble recorded version if available
if [[ "$RECORDED_AVAILABLE" == true ]]; then
    echo ""
    echo "🎙️ Assembling recorded version..."
    python -m scripts.audio_pipeline.pipeline assemble \
        --translation-file "$PROJECT_TRANSLATIONS_FILE" \
        --manual-recordings-dir "$PROJECT_MANUAL_RECORDINGS_DIR" \
        --output "$PROJECT_OUTPUT_RECORDED" \
        $VOLUME_SCALING_ARG
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Recorded assembly completed: $PROJECT_OUTPUT_RECORDED"
        # Copy to global output directory
        cp "$PROJECT_OUTPUT_RECORDED" "$GLOBAL_OUTPUT_RECORDED"
        echo "   Also saved to: $GLOBAL_OUTPUT_RECORDED"
    else
        echo "❌ Recorded assembly failed"
    fi
fi

echo ""
echo "🎯 Assembly Summary:"
echo "==================="
if [[ "$SYNTHESIZED_AVAILABLE" == true ]] && [[ -f "$PROJECT_OUTPUT_SYNTHESIZED" ]]; then
    echo "✅ Synthesized version: $PROJECT_OUTPUT_SYNTHESIZED"
    echo "   Global copy: $GLOBAL_OUTPUT_SYNTHESIZED"
fi
if [[ "$RECORDED_AVAILABLE" == true ]] && [[ -f "$PROJECT_OUTPUT_RECORDED" ]]; then
    echo "✅ Recorded version: $PROJECT_OUTPUT_RECORDED"
    echo "   Global copy: $GLOBAL_OUTPUT_RECORDED"
fi

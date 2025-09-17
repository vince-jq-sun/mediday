#!/bin/bash
# Step 4: Manual Review and Recording GUI
# Reads from a project folder structure with segments, transcripts, and translations

# Function to display usage
show_usage() {
    echo "Usage: $0 [PROJECT_FOLDER]"
    echo ""
    echo "PROJECT_FOLDER should contain:"
    echo "  - segments/     (audio segment files)"
    echo "  - transcripts/  (transcription JSON files)"
    echo "  - translations/ (translation JSON files)"
    echo ""
    echo "Example: $0 temp/awake_where_you_are_english/1-2_foundational_meditation_sample-1"
    echo ""
    echo "If no PROJECT_FOLDER is provided, will use project configuration."
}

# Check if project folder is provided as argument
if [[ $# -eq 1 ]]; then
    PROJECT_FOLDER="$1"
    # Extract project name from folder path
    CURRENT_PROJECT=$(basename "$PROJECT_FOLDER")
    echo "🎙️ Step 4: Manual Review and Recording"
    echo "======================================"
    echo "Project Folder: $PROJECT_FOLDER"
    echo "Project Name: $CURRENT_PROJECT"
elif [[ $# -eq 0 ]]; then
    # Load project configuration if no arguments provided
    source process/project_config.sh
    PROJECT_FOLDER="$PROJECT_BASE_DIR"
    echo "🎙️ Step 4: Manual Review and Recording"
    echo "======================================"
    echo "Project: $CURRENT_PROJECT"
    echo "Collection: $PROJECT_COLLECTION"
    echo "Project Folder: $PROJECT_FOLDER"
else
    show_usage
    exit 1
fi

# Define subfolder paths
SEGMENTS_DIR="$PROJECT_FOLDER/segments"
TRANSCRIPTS_DIR="$PROJECT_FOLDER/transcripts"
TRANSLATIONS_DIR="$PROJECT_FOLDER/translations"

echo ""
echo "📁 Checking folder structure..."
echo "   - Segments: $SEGMENTS_DIR"
echo "   - Transcripts: $TRANSCRIPTS_DIR"
echo "   - Translations: $TRANSLATIONS_DIR"

# Validate required folders exist
missing_folders=()
if [[ ! -d "$SEGMENTS_DIR" ]]; then
    missing_folders+=("segments")
fi
if [[ ! -d "$TRANSCRIPTS_DIR" ]]; then
    missing_folders+=("transcripts")
fi
if [[ ! -d "$TRANSLATIONS_DIR" ]]; then
    missing_folders+=("translations")
fi

if [[ ${#missing_folders[@]} -gt 0 ]]; then
    echo "❌ Missing required folders: ${missing_folders[*]}"
    echo "   Please ensure the project folder contains segments/, transcripts/, and translations/ subfolders."
    exit 1
fi

# Find translation file (look for JSON files in translations directory)
TRANSLATION_FILES=($(find "$TRANSLATIONS_DIR" -name "*.json" -type f 2>/dev/null))
if [[ ${#TRANSLATION_FILES[@]} -eq 0 ]]; then
    echo "❌ No translation JSON files found in $TRANSLATIONS_DIR"
    exit 1
elif [[ ${#TRANSLATION_FILES[@]} -eq 1 ]]; then
    TRANSLATION_FILE="${TRANSLATION_FILES[0]}"
else
    echo "📋 Multiple translation files found:"
    for i in "${!TRANSLATION_FILES[@]}"; do
        echo "   $((i+1)). $(basename "${TRANSLATION_FILES[$i]}")"
    done
    echo -n "Select translation file (1-${#TRANSLATION_FILES[@]}): "
    read -r selection
    if [[ "$selection" =~ ^[0-9]+$ ]] && [[ "$selection" -ge 1 ]] && [[ "$selection" -le ${#TRANSLATION_FILES[@]} ]]; then
        TRANSLATION_FILE="${TRANSLATION_FILES[$((selection-1))]}"
    else
        echo "❌ Invalid selection"
        exit 1
    fi
fi

# Note: recordings directory creation removed as it's not needed

echo ""
echo "✅ Found translation file: $(basename "$TRANSLATION_FILE")"
echo ""
echo "📝 Launching GUI for manual review and recording..."
echo "   - Translation file: $TRANSLATION_FILE"
echo "   - Segments directory: $SEGMENTS_DIR"
echo "   - Manual recordings will be saved to: $PROJECT_FOLDER/manual_recording/"
echo ""
echo "💡 In the GUI, you can:"
echo "   - Review and edit translations"
echo "   - Play original audio segments"
echo "   - Record manual Chinese audio for segments"
echo "   - Save recordings with proper naming"
echo ""

# Launch the translation GUI with recording capabilities
python -m scripts.audio_pipeline.translation_gui "$TRANSLATION_FILE"

echo "✅ Manual review and recording session completed."
echo "   Check $PROJECT_FOLDER/manual_recording/ for recorded audio files."

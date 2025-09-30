#!/bin/bash
# Test script to verify the project selector GUI feature

echo "🧪 Testing Project Selector GUI"
echo "================================"
echo ""
echo "This will launch the translation GUI with the current project."
echo "You should see:"
echo "  1. A new '📁 Project Selector' section at the top"
echo "  2. Two dropdown lists: Collection and Project"
echo "  3. A '✓ Switch Project' button"
echo "  4. Current project label showing: awake_where_you_are_english/1-1_introduction_sample-1"
echo ""
echo "Test steps:"
echo "  1. Try selecting a different collection from the first dropdown"
echo "  2. The second dropdown should update with projects from that collection"
echo "  3. Select a different project and click 'Switch Project'"
echo "  4. The GUI should reload with the new project's data"
echo ""

# Source project config
source process/project_config.sh

TRANSLATION_FILE="${PROJECT_TRANSLATIONS_DIR}/${CURRENT_PROJECT}_translations.json"

if [[ ! -f "$TRANSLATION_FILE" ]]; then
    echo "❌ Translation file not found: $TRANSLATION_FILE"
    echo "Please run the translation step first."
    exit 1
fi

echo "🚀 Launching GUI with:"
echo "   Collection: $PROJECT_COLLECTION"
echo "   Project: $CURRENT_PROJECT"
echo "   Translation file: $TRANSLATION_FILE"
echo ""

# Launch GUI
python -m scripts.audio_pipeline.translation_gui "$TRANSLATION_FILE"

echo ""
echo "✅ GUI closed"

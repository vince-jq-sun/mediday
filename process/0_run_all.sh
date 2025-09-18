#!/bin/bash
# Run all pipeline steps in sequence
# Usage: ./0_run_all.sh [openai|google]

# Load project configuration
source process/project_config.sh

# Set default STT provider to OpenAI if not specified
STT_PROVIDER=${1:-openai}

echo "🚀 Running Complete Pipeline"
echo "============================"
echo "Project: $CURRENT_PROJECT"
echo "File: $PROJECT_FILE"
echo "STT Provider: $STT_PROVIDER"
echo ""

# Clean previous results for this project
rm -rf temp/single_file "$PROJECT_BASE_DIR" output

echo "Step 1: Preprocessing..."
bash process/1_preprocess.sh

echo -e "\nStep 2: Transcription..."
bash process/2_transcribe.sh "$STT_PROVIDER"

echo -e "\nStep 3: Translation..."
bash process/3_translate.sh

echo -e "\nStep 4: [optional] Manual Review & Recording..."
echo "   Skipping GUI step in automated run. Use 'bash process/4_review-record.sh' manually if needed."

echo -e "\nStep 5: [optional] Synthesis..."
bash process/5_synthesize.sh

echo -e "\nStep 6: Assembly..."
bash process/6_assemble.sh

echo -e "\n🎉 Complete pipeline finished!"

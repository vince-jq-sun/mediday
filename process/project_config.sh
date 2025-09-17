#!/bin/bash
# Project Configuration - Centralized project settings
# Change CURRENT_PROJECT here to switch between different audio files

export CURRENT_PROJECT="1-2_foundational_meditation_sample-1"
export PROJECT_COLLECTION="awake_where_you_are_english"
export PROJECT_FILE="data/${PROJECT_COLLECTION}/${CURRENT_PROJECT}.mp3"

# New hierarchical temp structure: temp/{collection}/{project}/{type}/
export PROJECT_BASE_DIR="temp/${PROJECT_COLLECTION}/${CURRENT_PROJECT}"
export PROJECT_SEGMENTS_DIR="${PROJECT_BASE_DIR}/segments"
export PROJECT_TRANSCRIPTS_DIR="${PROJECT_BASE_DIR}/transcripts"
export PROJECT_TRANSLATIONS_DIR="${PROJECT_BASE_DIR}/translations"
export PROJECT_RECORDINGS_DIR="${PROJECT_BASE_DIR}/recordings"
export PROJECT_MANUAL_RECORDINGS_DIR="${PROJECT_BASE_DIR}/manual_recording"
export PROJECT_SYNTHESES_DIR="${PROJECT_BASE_DIR}/syntheses"
export PROJECT_OUTPUTS_DIR="${PROJECT_BASE_DIR}/outputs"

# Specific file paths
export PROJECT_TRANSCRIPTS_FILE="${PROJECT_TRANSCRIPTS_DIR}/${CURRENT_PROJECT}_transcriptions.json"
export PROJECT_TRANSLATIONS_FILE="${PROJECT_TRANSLATIONS_DIR}/${CURRENT_PROJECT}_translations.json"
export PROJECT_SYNTHESIS_FILE="${PROJECT_SYNTHESES_DIR}/${CURRENT_PROJECT}_synthesis_results.json"

# Legacy compatibility (for scripts that still reference these)
# PROJECT_MANUAL_RECORDINGS_DIR is now defined above to point to manual_recording folder

# Output files with different suffixes (now in project outputs directory)
export PROJECT_OUTPUT_SYNTHESIZED="${PROJECT_OUTPUTS_DIR}/${CURRENT_PROJECT}_synthesized.mp3"
export PROJECT_OUTPUT_RECORDED="${PROJECT_OUTPUTS_DIR}/${CURRENT_PROJECT}_recorded.mp3"
export PROJECT_OUTPUT_FINAL="${PROJECT_OUTPUTS_DIR}/${CURRENT_PROJECT}_final.mp3"

# Global output directory (for final deliverables)
export GLOBAL_OUTPUT_SYNTHESIZED="output/${CURRENT_PROJECT}_synthesized.mp3"
export GLOBAL_OUTPUT_RECORDED="output/${CURRENT_PROJECT}_recorded.mp3"
export GLOBAL_OUTPUT_FINAL="output/${CURRENT_PROJECT}_final.mp3"

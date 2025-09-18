# STT Provider Selection Guide

## Overview
The transcription step (Step 2) now supports choosing between two speech-to-text providers:
- **OpenAI Whisper** (default, recommended)
- **Google Speech-to-Text**

## Usage

### Individual Transcription Step
```bash
# Use OpenAI Whisper (default)
bash process/2_transcribe.sh
bash process/2_transcribe.sh openai

# Use Google Speech-to-Text
bash process/2_transcribe.sh google
```

### Complete Pipeline
```bash
# Use OpenAI Whisper (default)
bash process/0_run_all.sh
bash process/0_run_all.sh openai

# Use Google Speech-to-Text
bash process/0_run_all.sh google
```

## Provider Comparison

### OpenAI Whisper (Recommended)
- **Pros**: 
  - Higher accuracy, especially for meditation/mindfulness content
  - Better handling of pauses and natural speech patterns
  - No Google Cloud setup required
- **Cons**: 
  - Requires OpenAI API key
  - Slightly higher cost per minute

### Google Speech-to-Text
- **Pros**: 
  - Fast processing
  - Good integration with other Google services
- **Cons**: 
  - Requires Google Cloud setup and authentication
  - May be less accurate for specialized content

## Configuration Requirements

### For OpenAI Whisper
- Ensure `config/openai.json` contains your OpenAI API key
- Default model: `whisper-1`

### For Google Speech-to-Text
- Set up Google Cloud credentials
- Enable Speech-to-Text API
- Configure authentication (service account key)

## Error Handling
If an invalid provider is specified, the script will show usage information and exit:
```
❌ Error: Invalid STT provider 'invalid'
Usage: ./2_transcribe.sh [openai|google]
  openai  - Use OpenAI Whisper (default, recommended)
  google  - Use Google Speech-to-Text
```

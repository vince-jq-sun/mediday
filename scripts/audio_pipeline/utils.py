"""
Utility functions for the audio processing pipeline
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None):
    """Set up logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def load_json_file(file_path: Path) -> Dict:
    """Load JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def save_json_file(data: Dict, file_path: Path, indent: int = 2):
    """Save data to JSON file with error handling"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Failed to save {file_path}: {e}")

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"

def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

def estimate_processing_time(audio_duration: float, step: str) -> float:
    """Estimate processing time for different pipeline steps"""
    # Rough estimates based on typical processing times
    multipliers = {
        'preprocessing': 0.1,    # Very fast
        'transcription': 0.5,    # Depends on API speed
        'translation': 0.05,     # Very fast
        'synthesis': 0.3,        # Moderate
        'assembly': 0.2          # Fast
    }
    
    return audio_duration * multipliers.get(step, 0.5)

def create_progress_tracker(total_items: int, description: str = "Processing"):
    """Create a simple progress tracker"""
    class ProgressTracker:
        def __init__(self, total: int, desc: str):
            self.total = total
            self.current = 0
            self.description = desc
            self.start_time = time.time()
        
        def update(self, increment: int = 1):
            self.current += increment
            percentage = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time
            
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                eta_str = format_duration(eta)
            else:
                eta_str = "Unknown"
            
            print(f"\r{self.description}: {self.current}/{self.total} "
                  f"({percentage:.1f}%) - ETA: {eta_str}", end="", flush=True)
            
            if self.current >= self.total:
                print()  # New line when complete
        
        def finish(self):
            elapsed = time.time() - self.start_time
            print(f"\n✅ {self.description} completed in {format_duration(elapsed)}")
    
    return ProgressTracker(total_items, description)

def validate_audio_file(file_path: Path) -> Dict:
    """Validate audio file and return metadata"""
    import librosa
    
    if not file_path.exists():
        return {'valid': False, 'error': 'File not found'}
    
    try:
        # Try to load audio file
        y, sr = librosa.load(file_path, sr=None, duration=1.0)  # Load first second only
        duration = librosa.get_duration(path=file_path)
        
        return {
            'valid': True,
            'duration': duration,
            'sample_rate': sr,
            'file_size': file_path.stat().st_size,
            'format': file_path.suffix.lower()
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def check_disk_space(path: Path, required_gb: float = 1.0) -> bool:
    """Check if there's enough disk space"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        return free_gb >= required_gb
    except Exception:
        return True  # Assume OK if can't check

def cleanup_temp_files(temp_dir: Path, keep_recent: bool = True, hours: int = 24):
    """Clean up temporary files"""
    if not temp_dir.exists():
        return
    
    current_time = time.time()
    cutoff_time = current_time - (hours * 3600) if keep_recent else 0
    
    cleaned_count = 0
    for file_path in temp_dir.rglob('*'):
        if file_path.is_file():
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            except Exception:
                pass  # Skip files that can't be deleted
    
    if cleaned_count > 0:
        print(f"🧹 Cleaned up {cleaned_count} temporary files")

def get_pipeline_status(temp_dir: Path) -> Dict:
    """Get current pipeline processing status"""
    status = {
        'preprocessing': False,
        'transcription': False,
        'translation': False,
        'synthesis': False,
        'files_processed': 0
    }
    
    # Check for preprocessing results
    segments_dir = temp_dir / "segments"
    if segments_dir.exists():
        metadata_files = list(segments_dir.glob("*_metadata.json"))
        if metadata_files:
            status['preprocessing'] = True
            status['files_processed'] = len(metadata_files)
    
    # Check for transcription results
    transcripts_dir = temp_dir / "transcripts"
    if transcripts_dir.exists():
        transcript_files = list(transcripts_dir.glob("*_transcriptions.json"))
        if transcript_files:
            status['transcription'] = True
    
    # Check for translation results
    translations_dir = temp_dir / "translations"
    if translations_dir.exists():
        translation_files = list(translations_dir.glob("*_translations.json"))
        if translation_files:
            status['translation'] = True
    
    # Check for synthesis results
    synthesis_dir = temp_dir / "synthesis"
    if synthesis_dir.exists():
        synthesis_files = list(synthesis_dir.glob("*_synthesis_results.json"))
        if synthesis_files:
            status['synthesis'] = True
    
    return status

def find_latest_file(directory: Path, pattern: str) -> Optional[Path]:
    """Find the most recently modified file matching pattern"""
    try:
        files = list(directory.glob(pattern))
        if not files:
            return None
        
        return max(files, key=lambda f: f.stat().st_mtime)
    except Exception:
        return None

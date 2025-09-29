"""
GUI for manual translation review and editing with audio playback and recording
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import sys
from pathlib import Path
import pygame
import threading
import pyaudio
import wave
import time
from pydub import AudioSegment
try:
    import simpleaudio as sa
    HAS_SIMPLEAUDIO = True
except ImportError:
    HAS_SIMPLEAUDIO = False
import io
from typing import Dict, List, Optional
from .config import GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT, TERMINOLOGY_FILE
from .translator import Translator

class TranslationReviewGUI:
    def __init__(self, translation_file: Path):
        self.translation_file = translation_file
        self.translation_data = self.load_translation_data()
        self.current_segment_index = 0
        self.translator = Translator(terminology_file=TERMINOLOGY_FILE)
        
        # Set up manual recording directory based on project path
        self.manual_recordings_dir = self.get_manual_recordings_dir()
        
        # Audio recording setup
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.recording = False
        self.recorded_frames = []
        self.audio = pyaudio.PyAudio()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Audio playback state tracking
        self.original_audio_playing = False
        self.recording_audio_playing = False
        self.original_audio_paused = False
        self.recording_audio_paused = False
        
        # Audio progress tracking
        self.audio_duration = 0.0
        self.audio_start_time = 0.0
        self.progress_updating = False
        self.user_seeking = False
        
        # Audio segment for seeking support
        self.current_audio_segment = None
        self.audio_thread = None
        self.audio_stop_event = threading.Event()
        self.current_playback = None
        self.playback_paused = False
        self.pause_position = 0.0
        
        # Content change tracking
        self.original_english_text = ""
        self.original_chinese_text = ""
        self.content_changed = False
        
        self.setup_gui()
        self.load_current_segment()
    
    def load_translation_data(self) -> Dict:
        """Load translation data from JSON file"""
        with open(self.translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_manual_recordings_dir(self) -> Path:
        """Get the manual recordings directory for the current project"""
        # Get the project root directory (parent of translations folder)
        project_dir = self.translation_file.parent.parent
        # Create manual_recording directory parallel to translations
        manual_recordings_dir = project_dir / "manual_recording"
        manual_recordings_dir.mkdir(parents=True, exist_ok=True)
        return manual_recordings_dir
    
    def save_translation_data(self):
        """Save current translation data to file"""
        with open(self.translation_file, 'w', encoding='utf-8') as f:
            json.dump(self.translation_data, f, indent=2, ensure_ascii=False)
    
    def setup_gui(self):
        """Set up the main GUI window"""
        self.root = tk.Tk()
        self.root.title("Translation Review & Recording")
        self.root.geometry(f"{GUI_WINDOW_WIDTH}x{GUI_WINDOW_HEIGHT}")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Progress info
        self.progress_label = ttk.Label(main_frame, text="", font=('Arial', 12, 'bold'))
        self.progress_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Audio playback section
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Playback", padding="10")
        audio_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        audio_frame.columnconfigure(1, weight=1)
        
        self.play_button = ttk.Button(audio_frame, text="▶ Play Original", command=self.play_original_audio)
        self.play_button.grid(row=0, column=0, padx=(0, 10))
        
        self.audio_info_label = ttk.Label(audio_frame, text="")
        self.audio_info_label.grid(row=0, column=1, sticky=tk.W)
        
        # Progress bar frame
        progress_frame = ttk.Frame(audio_frame)
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(1, weight=1)
        
        # Time labels
        self.current_time_label = ttk.Label(progress_frame, text="0:00")
        self.current_time_label.grid(row=0, column=0, padx=(0, 5))
        
        # Progress bar (scale widget for seeking)
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(progress_frame, from_=0, to=100, 
                                      variable=self.progress_var, orient=tk.HORIZONTAL,
                                      command=self.on_progress_change)
        self.progress_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        # Bind mouse events for seeking
        self.progress_scale.bind("<Button-1>", self.on_seek_start)
        self.progress_scale.bind("<ButtonRelease-1>", self.on_seek_end)
        
        self.total_time_label = ttk.Label(progress_frame, text="0:00")
        self.total_time_label.grid(row=0, column=2, padx=(5, 0))
        
        # Text editing section
        text_frame = ttk.LabelFrame(main_frame, text="Text Editing", padding="10")
        text_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(1, weight=1)
        text_frame.rowconfigure(3, weight=1)
        
        # English text
        ttk.Label(text_frame, text="English Text:").grid(row=0, column=0, sticky=tk.W)
        self.english_text = tk.Text(text_frame, height=4, wrap=tk.WORD)
        self.english_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))
        
        # Remove retranslate button from here - will be moved to retranslation frame
        
        # Chinese text
        ttk.Label(text_frame, text="Chinese Translation:").grid(row=3, column=0, sticky=tk.W)
        self.chinese_text = tk.Text(text_frame, height=4, wrap=tk.WORD)
        self.chinese_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Bind text change events
        self.english_text.bind('<KeyRelease>', self.on_text_change)
        self.english_text.bind('<Button-1>', self.on_text_change)
        self.chinese_text.bind('<KeyRelease>', self.on_text_change)
        self.chinese_text.bind('<Button-1>', self.on_text_change)
        
        # Retranslation results display
        self.retranslation_frame = ttk.LabelFrame(main_frame, text="🔄 Retranslation Results", padding="10")
        self.retranslation_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.retranslation_frame.columnconfigure(0, weight=1)
        
        # Button frame for all retranslation controls (top row)
        retrans_control_frame = ttk.Frame(self.retranslation_frame)
        retrans_control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Re-translate button
        self.retranslate_button = ttk.Button(retrans_control_frame, text="🔄 Re-translate", command=self.retranslate_text)
        self.retranslate_button.grid(row=0, column=0, padx=(0, 10))
        
        # Use terminology checkbox
        self.use_terminology_var = tk.BooleanVar(value=True)
        self.terminology_checkbox = ttk.Checkbutton(retrans_control_frame, text="Use Terminology", variable=self.use_terminology_var)
        self.terminology_checkbox.grid(row=0, column=1, padx=(0, 20))
        
        # Copy button
        self.copy_retranslation_button = ttk.Button(retrans_control_frame, text="📋 复制到中文文本框", 
                                                   command=self.copy_retranslation, state=tk.DISABLED)
        self.copy_retranslation_button.grid(row=0, column=2, padx=(0, 10))
        
        # Clear button
        self.clear_retranslation_button = ttk.Button(retrans_control_frame, text="🗑️ 清空", 
                                                    command=self.clear_retranslation)
        self.clear_retranslation_button.grid(row=0, column=3)
        
        # Retranslation text area
        self.retranslation_text = tk.Text(self.retranslation_frame, height=4, wrap=tk.WORD, 
                                         bg="#f8f9fa", relief="sunken", bd=1)
        self.retranslation_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 0))
        
        # Recording section
        recording_frame = ttk.LabelFrame(main_frame, text="Manual Recording", padding="10")
        recording_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        recording_frame.columnconfigure(2, weight=1)
        
        self.record_button = ttk.Button(recording_frame, text="🎤 Record", command=self.toggle_recording)
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        self.play_recording_button = ttk.Button(recording_frame, text="▶ Play Recording", 
                                              command=self.play_recording, state=tk.DISABLED)
        self.play_recording_button.grid(row=0, column=1, padx=(0, 10))
        
        self.recording_status_label = ttk.Label(recording_frame, text="No recording")
        self.recording_status_label.grid(row=0, column=2, sticky=tk.W)
        
        # Navigation section
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        self.prev_button = ttk.Button(nav_frame, text="◀ Previous", command=self.previous_segment)
        self.prev_button.grid(row=0, column=0, padx=(0, 10))
        
        self.save_button = ttk.Button(nav_frame, text="💾 Save", command=self.save_current_segment)
        self.save_button.grid(row=0, column=1, padx=(0, 10))
        
        self.next_button = ttk.Button(nav_frame, text="Next ▶", command=self.next_segment)
        self.next_button.grid(row=0, column=2)
        
        # Retranslation frame is always visible
    
    def load_current_segment(self):
        """Load current segment data into the GUI"""
        if not self.translation_data['segments']:
            return
        
        # Stop any currently playing audio when switching segments
        self.stop_audio_playback()
        
        if self.recording_audio_playing or self.recording_audio_paused:
            pygame.mixer.music.stop()
            self.recording_audio_playing = False
            self.recording_audio_paused = False
            self.play_recording_button.config(text="▶ Play Recording")
        
        segment = self.translation_data['segments'][self.current_segment_index]
        total_segments = len(self.translation_data['segments'])
        
        # Update progress
        self.progress_label.config(text=f"Segment {self.current_segment_index + 1} / {total_segments}")
        
        # Update audio info and progress bar
        duration = segment.get('duration', 0)
        self.audio_duration = duration
        self.audio_info_label.config(text=f"Duration: {duration:.1f}s")
        
        # Reset progress bar
        self.progress_var.set(0)
        self.current_time_label.config(text="0:00")
        self.total_time_label.config(text=self.format_time(duration))
        
        # Load audio segment for seeking support
        self.load_audio_segment()
        
        # Load text
        self.english_text.delete(1.0, tk.END)
        self.english_text.insert(1.0, segment.get('original_text', ''))
        
        self.chinese_text.delete(1.0, tk.END)
        self.chinese_text.insert(1.0, segment.get('translated_text', ''))
        
        # Store original text for change detection
        self.original_english_text = segment.get('original_text', '')
        self.original_chinese_text = segment.get('translated_text', '')
        self.content_changed = False
        
        # Clear retranslation results
        self.retranslation_text.delete(1.0, tk.END)
        self.copy_retranslation_button.config(state=tk.DISABLED)
        
        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_segment_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_segment_index < total_segments - 1 else tk.DISABLED)
        
        # Check for existing recording
        self.check_existing_recording()
    
    def load_audio_segment(self):
        """Load audio segment for seeking support"""
        segment = self.translation_data['segments'][self.current_segment_index]
        audio_path = Path(segment['file_path'])
        
        if audio_path.exists():
            try:
                self.current_audio_segment = AudioSegment.from_file(str(audio_path))
                # Update duration from actual audio file
                actual_duration = len(self.current_audio_segment) / 1000.0  # Convert to seconds
                self.audio_duration = actual_duration
                self.total_time_label.config(text=self.format_time(actual_duration))
            except Exception as e:
                print(f"Error loading audio segment: {e}")
                self.current_audio_segment = None
        else:
            self.current_audio_segment = None
    
    def stop_audio_playback(self):
        """Stop current audio playback using pygame"""
        try:
            print("Stopping audio playback...")
            
            # Stop pygame music safely
            pygame.mixer.music.stop()
            print("Pygame music stopped")
            
        except Exception as e:
            print(f"Error stopping pygame music: {e}")
        
        # Reset all states
        self.original_audio_playing = False
        self.original_audio_paused = False
        self.playback_paused = False
        self.pause_position = 0.0
        self.play_button.config(text="▶ Play Original")
        print("Audio playback state reset")
    
    def format_time(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def on_progress_change(self, value):
        """Handle progress bar change (when user drags)"""
        try:
            if not self.user_seeking:
                return
            
            # Update current time display
            current_time = (float(value) / 100.0) * self.audio_duration
            self.current_time_label.config(text=self.format_time(current_time))
        except Exception as e:
            print(f"Error in progress change: {e}")
    
    def on_seek_start(self, event):
        """Handle start of seeking (mouse press on progress bar)"""
        self.user_seeking = True
    
    def on_seek_end(self, event):
        """Handle end of seeking (mouse release on progress bar)"""
        try:
            if not self.user_seeking:
                return
            
            self.user_seeking = False
            
            # If audio is playing or paused, seek to new position
            if (self.original_audio_playing or self.original_audio_paused) and self.current_audio_segment:
                seek_percentage = self.progress_var.get()
                seek_time = (seek_percentage / 100.0) * self.audio_duration
                
                print(f"Seeking to {seek_time:.2f}s ({seek_percentage:.1f}%)")
                
                # Stop current playback
                self.stop_audio_playback()
                
                # Start playback from new position
                self.play_audio_from_position(seek_time)
        except Exception as e:
            print(f"Error in seek end: {e}")
            # Reset seeking state
            self.user_seeking = False
    
    def update_progress(self):
        """Update progress bar during playback"""
        if self.original_audio_playing and not self.user_seeking:
            elapsed_time = time.time() - self.audio_start_time
            
            if elapsed_time <= self.audio_duration:
                progress_percentage = (elapsed_time / self.audio_duration) * 100
                self.progress_var.set(progress_percentage)
                self.current_time_label.config(text=self.format_time(elapsed_time))
                
                # Schedule next update
                self.root.after(100, self.update_progress)
            else:
                # Playback finished
                self.progress_var.set(100)
                self.current_time_label.config(text=self.format_time(self.audio_duration))
    
    def play_audio_from_position(self, start_time=0.0):
        """Play audio from specified position - using pygame for stability"""
        if not self.current_audio_segment:
            print("No audio segment loaded")
            return
        
        # Always use pygame for now to avoid simpleaudio crashes
        print(f"Using pygame for audio playback from {start_time:.2f}s")
        self.play_audio_pygame_enhanced(start_time)
        return
        
        def audio_playback_thread():
            try:
                print(f"Starting playback from {start_time:.2f}s")
                
                # Extract segment from start_time to end
                start_ms = int(start_time * 1000)
                audio_to_play = self.current_audio_segment[start_ms:]
                
                if len(audio_to_play) == 0:
                    print("No audio to play from this position")
                    return
                
                # Convert to raw audio data
                raw_data = audio_to_play.raw_data
                sample_rate = audio_to_play.frame_rate
                num_channels = audio_to_play.channels
                bytes_per_sample = audio_to_play.sample_width
                
                print(f"Audio format: {sample_rate}Hz, {num_channels}ch, {bytes_per_sample}B")
                
                # Set playback state
                self.original_audio_playing = True
                self.original_audio_paused = False
                self.playback_paused = False
                self.root.after(0, lambda: self.play_button.config(text="⏸ Pause"))
                
                # Start progress tracking
                self.audio_start_time = time.time() - start_time
                self.root.after(0, self.update_progress)
                
                # Play audio using simpleaudio
                self.current_playback = sa.play_buffer(
                    raw_data, num_channels, bytes_per_sample, sample_rate
                )
                
                # Wait for playback to finish or be stopped
                while not self.audio_stop_event.is_set():
                    try:
                        if not self.current_playback.is_playing():
                            break
                    except:
                        break
                    time.sleep(0.1)
                
                # Clean up playback object
                try:
                    if self.current_playback and self.current_playback.is_playing():
                        self.current_playback.stop()
                except:
                    pass
                self.current_playback = None
                
                # Update UI state
                if not self.audio_stop_event.is_set():
                    # Finished naturally
                    print("Playback finished naturally")
                    self.original_audio_playing = False
                    self.playback_paused = False
                    self.root.after(0, lambda: self.play_button.config(text="▶ Play Original"))
                else:
                    print("Playback was stopped")
                    
            except Exception as e:
                print(f"Audio playback error: {e}")
                import traceback
                traceback.print_exc()
                self.original_audio_playing = False
                self.root.after(0, lambda: self.play_button.config(text="▶ Play Original"))
        
        # Stop any existing playback
        self.stop_audio_playback()
        
        # Clear stop event before starting new playback
        self.audio_stop_event.clear()
        
        # Start new playback thread
        self.audio_thread = threading.Thread(target=audio_playback_thread, daemon=True)
        self.audio_thread.start()
    
    def play_audio_pygame_enhanced(self, start_time=0.0):
        """Enhanced pygame audio playback with pause support"""
        try:
            # Create a temporary audio file from the desired position if needed
            if start_time > 0 and self.current_audio_segment:
                # Extract audio from start_time position
                start_ms = int(start_time * 1000)
                audio_to_play = self.current_audio_segment[start_ms:]
                
                # Save to temporary file
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                audio_to_play.export(temp_file.name, format='wav')
                audio_path = temp_file.name
                print(f"Created temp audio file from {start_time:.2f}s: {audio_path}")
            else:
                # Use original file
                segment = self.translation_data['segments'][self.current_segment_index]
                audio_path = str(Path(segment['file_path']))
            
            # Load and play with pygame
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Set state
            self.original_audio_playing = True
            self.original_audio_paused = False
            self.playback_paused = False
            self.play_button.config(text="⏸ Pause")
            
            # Set timing for progress tracking
            self.audio_start_time = time.time() - start_time
            self.update_progress()
            
            # Start monitoring playback status
            self.check_pygame_playback_status()
            
            print(f"Started pygame playback from {start_time:.2f}s")
                
        except Exception as e:
            print(f"Pygame enhanced error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Playback Error", f"Could not play audio: {e}")
    
    def check_pygame_playback_status(self):
        """Monitor pygame playback status"""
        if self.original_audio_playing:
            if not pygame.mixer.music.get_busy():
                # Playback finished
                print("Pygame playback finished")
                self.original_audio_playing = False
                self.playback_paused = False
                self.play_button.config(text="▶ Play Original")
                self.progress_var.set(100)
                self.current_time_label.config(text=self.format_time(self.audio_duration))
            else:
                # Still playing, check again
                self.root.after(100, self.check_pygame_playback_status)
    
    def check_existing_recording(self):
        """Check if there's an existing manual recording for this segment"""
        segment = self.translation_data['segments'][self.current_segment_index]
        segment_id = segment['segment_id']
        
        base_filename = Path(self.translation_data['original_file']).stem
        recording_filename = f"{base_filename}_segment_{segment_id:03d}_manual.wav"
        recording_path = self.manual_recordings_dir / recording_filename
        
        if recording_path.exists():
            self.recording_status_label.config(text=f"Recording exists: {recording_path.name}")
            self.play_recording_button.config(state=tk.NORMAL)
            self.record_button.config(text="🎤 Re-record")
        else:
            self.recording_status_label.config(text="No recording")
            self.play_recording_button.config(state=tk.DISABLED)
            self.record_button.config(text="🎤 Record")
    
    def play_original_audio(self):
        """Play or pause the original audio segment"""
        print(f"Play button clicked. State - playing: {self.original_audio_playing}, paused: {self.playback_paused}")
        
        if self.original_audio_playing:
            # Currently playing, so pause
            print("Calling pause_audio()")
            self.pause_audio()
        elif self.playback_paused:
            # Currently paused, so resume
            print("Calling resume_audio()")
            self.resume_audio()
        else:
            # Not playing, so start playback from beginning
            print("Starting new playback")
            if self.current_audio_segment:
                self.play_audio_from_position(0.0)
            else:
                messagebox.showerror("Audio Error", "Audio file could not be loaded")
    
    def pause_audio(self):
        """Pause current audio playback using pygame"""
        if self.original_audio_playing:
            print("Attempting to pause audio with pygame...")
            
            # Calculate current position
            elapsed_time = time.time() - self.audio_start_time
            self.pause_position = min(elapsed_time, self.audio_duration)
            
            print(f"Calculated pause position: {self.pause_position:.2f}s")
            
            # Use pygame's pause function (much safer)
            try:
                pygame.mixer.music.pause()
                print("Pygame music paused")
            except Exception as e:
                print(f"Error pausing pygame music: {e}")
            
            # Set paused state
            self.original_audio_playing = False
            self.playback_paused = True
            self.play_button.config(text="▶ Resume")
            
            print(f"Paused at {self.pause_position:.2f}s")
    
    def resume_audio(self):
        """Resume audio playback from paused position"""
        if self.playback_paused:
            print("Attempting to resume pygame audio...")
            
            try:
                # Use pygame's unpause function
                pygame.mixer.music.unpause()
                print("Pygame music resumed")
                
                # Set playing state
                self.original_audio_playing = True
                self.playback_paused = False
                self.play_button.config(text="⏸ Pause")
                
                # Resume progress tracking and status monitoring
                self.update_progress()
                self.check_pygame_playback_status()
                
                print(f"Resumed from {self.pause_position:.2f}s")
                
            except Exception as e:
                print(f"Error resuming pygame music: {e}")
                # Fallback: restart from pause position
                self.playback_paused = False
                self.play_audio_from_position(self.pause_position)
    
    
    def retranslate_text(self):
        """Re-translate the English text"""
        english_text = self.english_text.get(1.0, tk.END).strip()
        
        if not english_text:
            messagebox.showwarning("No Text", "Please enter English text to translate.")
            return
        
        self.retranslate_button.config(text="🔄 Translating...", state=tk.DISABLED)
        
        def translate_thread():
            try:
                use_terminology = self.use_terminology_var.get()
                result = self.translator.retranslate_segment(english_text, use_terminology)
                
                # Update GUI in main thread
                self.root.after(0, lambda: self.show_new_translation(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Translation Error", f"Translation failed: {e}"))
            finally:
                self.root.after(0, lambda: self.retranslate_button.config(text="🔄 Re-translate", state=tk.NORMAL))
        
        threading.Thread(target=translate_thread, daemon=True).start()
    
    def show_new_translation(self, translation_result: Dict):
        """Show the new translation result in the retranslation text box"""
        if translation_result.get('translated_text'):
            # Display the new translation in the retranslation text box
            self.retranslation_text.delete(1.0, tk.END)
            self.retranslation_text.insert(1.0, translation_result['translated_text'])
            
            # Enable the copy button
            self.copy_retranslation_button.config(state=tk.NORMAL)
            
            # Add some metadata if available
            metadata_info = []
            if translation_result.get('model'):
                metadata_info.append(f"Model: {translation_result['model']}")
            if translation_result.get('tokens_used'):
                metadata_info.append(f"Tokens: {translation_result['tokens_used']}")
            if translation_result.get('terminology_applied'):
                metadata_info.append("✅ 术语表已应用")
            
            if metadata_info:
                self.retranslation_text.insert(tk.END, f"\n\n[{', '.join(metadata_info)}]")
        else:
            error_msg = translation_result.get('error', 'Unknown error')
            self.retranslation_text.delete(1.0, tk.END)
            self.retranslation_text.insert(1.0, f"❌ 翻译失败: {error_msg}")
            self.copy_retranslation_button.config(state=tk.DISABLED)
    
    def copy_retranslation(self):
        """Copy retranslation result to the Chinese text field"""
        retrans_text = self.retranslation_text.get(1.0, tk.END).strip()
        
        # Remove metadata if present (text after the last newline that starts with [)
        lines = retrans_text.split('\n')
        clean_lines = []
        for line in lines:
            if line.strip().startswith('[') and line.strip().endswith(']'):
                break
            clean_lines.append(line)
        
        clean_text = '\n'.join(clean_lines).strip()
        
        if clean_text:
            self.chinese_text.delete(1.0, tk.END)
            self.chinese_text.insert(1.0, clean_text)
            
            # Trigger change detection
            self.on_text_change()
    
    def clear_retranslation(self):
        """Clear the retranslation text box"""
        self.retranslation_text.delete(1.0, tk.END)
        self.copy_retranslation_button.config(state=tk.DISABLED)
    
    def toggle_recording(self):
        """Toggle audio recording"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start audio recording"""
        self.recording = True
        self.recorded_frames = []
        self.record_button.config(text="⏹ Stop Recording", style="Accent.TButton")
        self.recording_status_label.config(text="Recording...")
        
        def record_thread():
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            while self.recording:
                data = stream.read(self.chunk)
                self.recorded_frames.append(data)
            
            stream.stop_stream()
            stream.close()
        
        threading.Thread(target=record_thread, daemon=True).start()
    
    def stop_recording(self):
        """Stop audio recording and save file"""
        self.recording = False
        self.record_button.config(text="🎤 Record")
        
        if self.recorded_frames:
            # Save recording
            segment = self.translation_data['segments'][self.current_segment_index]
            segment_id = segment['segment_id']
            
            base_filename = Path(self.translation_data['original_file']).stem
            recording_filename = f"{base_filename}_segment_{segment_id:03d}_manual.wav"
            recording_path = self.manual_recordings_dir / recording_filename
            
            recording_path.parent.mkdir(parents=True, exist_ok=True)
            
            wf = wave.open(str(recording_path), 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.recorded_frames))
            wf.close()
            
            self.recording_status_label.config(text=f"Saved: {recording_filename}")
            self.play_recording_button.config(state=tk.NORMAL)
            self.record_button.config(text="🎤 Re-record")
        else:
            self.recording_status_label.config(text="No recording data")
    
    def play_recording(self):
        """Play or pause the manual recording"""
        if self.recording_audio_playing:
            # Currently playing, so pause
            pygame.mixer.music.pause()
            self.recording_audio_playing = False
            self.recording_audio_paused = True
            self.play_recording_button.config(text="▶ Play Recording")
        elif self.recording_audio_paused:
            # Currently paused, so resume
            pygame.mixer.music.unpause()
            self.recording_audio_playing = True
            self.recording_audio_paused = False
            self.play_recording_button.config(text="⏸ Pause")
            self.check_recording_playback_status()
        else:
            # Not playing, so start playback
            segment = self.translation_data['segments'][self.current_segment_index]
            segment_id = segment['segment_id']
            
            base_filename = Path(self.translation_data['original_file']).stem
            recording_filename = f"{base_filename}_segment_{segment_id:03d}_manual.wav"
            recording_path = self.manual_recordings_dir / recording_filename
            
            if recording_path.exists():
                try:
                    pygame.mixer.music.load(str(recording_path))
                    pygame.mixer.music.play()
                    self.recording_audio_playing = True
                    self.recording_audio_paused = False
                    self.play_recording_button.config(text="⏸ Pause")
                    self.check_recording_playback_status()
                except Exception as e:
                    messagebox.showerror("Playback Error", f"Could not play recording: {e}")
    
    def check_recording_playback_status(self):
        """Check if recording audio is still playing and update button state"""
        if self.recording_audio_playing and not pygame.mixer.music.get_busy():
            # Playback finished
            self.recording_audio_playing = False
            self.recording_audio_paused = False
            self.play_recording_button.config(text="▶ Play Recording")
        elif self.recording_audio_playing:
            # Still playing, check again in 100ms
            self.root.after(100, self.check_recording_playback_status)
    
    def on_text_change(self, event=None):
        """Handle text change events to track if content has been modified"""
        current_english = self.english_text.get(1.0, tk.END).strip()
        current_chinese = self.chinese_text.get(1.0, tk.END).strip()
        
        self.content_changed = (current_english != self.original_english_text or 
                               current_chinese != self.original_chinese_text)
    
    def has_unsaved_changes(self):
        """Check if there are unsaved changes in the current segment"""
        return self.content_changed
    
    def save_current_segment(self, show_message=True):
        """Save current segment changes"""
        segment = self.translation_data['segments'][self.current_segment_index]
        
        # Update segment data
        segment['original_text'] = self.english_text.get(1.0, tk.END).strip()
        segment['translated_text'] = self.chinese_text.get(1.0, tk.END).strip()
        
        # Save to file
        self.save_translation_data()
        
        # Reset change tracking
        self.original_english_text = segment['original_text']
        self.original_chinese_text = segment['translated_text']
        self.content_changed = False
        
        if show_message:
            messagebox.showinfo("Saved", "Segment saved successfully!")
    
    def previous_segment(self):
        """Go to previous segment"""
        if self.current_segment_index > 0:
            # Check if there are unsaved changes
            if self.has_unsaved_changes():
                result = messagebox.askyesnocancel(
                    "Unsaved Changes", 
                    "You have unsaved changes. Do you want to save them before moving to the previous segment?"
                )
                if result is True:  # Yes, save
                    self.save_current_segment(show_message=False)
                elif result is None:  # Cancel
                    return
                # If No (False), continue without saving
            
            self.current_segment_index -= 1
            self.load_current_segment()
    
    def next_segment(self):
        """Go to next segment"""
        if self.current_segment_index < len(self.translation_data['segments']) - 1:
            # Check if there are unsaved changes
            if self.has_unsaved_changes():
                result = messagebox.askyesnocancel(
                    "Unsaved Changes", 
                    "You have unsaved changes. Do you want to save them before moving to the next segment?"
                )
                if result is True:  # Yes, save
                    self.save_current_segment(show_message=False)
                elif result is None:  # Cancel
                    return
                # If No (False), continue without saving
            
            self.current_segment_index += 1
            self.load_current_segment()
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        finally:
            # Cleanup
            pygame.mixer.quit()
            self.audio.terminate()

def launch_translation_gui(translation_file: Path = None):
    """Launch the translation review GUI"""
    if translation_file is None:
        # File dialog to select translation file
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        translation_file = filedialog.askopenfilename(
            title="Select Translation File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(Path(__file__).parent.parent.parent / "temp" / "translations")
        )
        
        root.destroy()
        
        if not translation_file:
            print("No file selected")
            return
        
        translation_file = Path(translation_file)
    
    if not translation_file.exists():
        print(f"Translation file not found: {translation_file}")
        return
    
    app = TranslationReviewGUI(translation_file)
    app.run()

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        translation_file = Path(sys.argv[1])
        launch_translation_gui(translation_file)
    else:
        launch_translation_gui()

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
        if self.original_audio_playing or self.original_audio_paused:
            pygame.mixer.music.stop()
            self.original_audio_playing = False
            self.original_audio_paused = False
            self.play_button.config(text="▶ Play Original")
        
        if self.recording_audio_playing or self.recording_audio_paused:
            pygame.mixer.music.stop()
            self.recording_audio_playing = False
            self.recording_audio_paused = False
            self.play_recording_button.config(text="▶ Play Recording")
        
        segment = self.translation_data['segments'][self.current_segment_index]
        total_segments = len(self.translation_data['segments'])
        
        # Update progress
        self.progress_label.config(text=f"Segment {self.current_segment_index + 1} / {total_segments}")
        
        # Update audio info
        duration = segment.get('duration', 0)
        self.audio_info_label.config(text=f"Duration: {duration:.1f}s")
        
        # Load text
        self.english_text.delete(1.0, tk.END)
        self.english_text.insert(1.0, segment.get('english_text', ''))
        
        self.chinese_text.delete(1.0, tk.END)
        self.chinese_text.insert(1.0, segment.get('chinese_text', ''))
        
        # Store original text for change detection
        self.original_english_text = segment.get('english_text', '')
        self.original_chinese_text = segment.get('chinese_text', '')
        self.content_changed = False
        
        # Clear retranslation results
        self.retranslation_text.delete(1.0, tk.END)
        self.copy_retranslation_button.config(state=tk.DISABLED)
        
        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_segment_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_segment_index < total_segments - 1 else tk.DISABLED)
        
        # Check for existing recording
        self.check_existing_recording()
    
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
        if self.original_audio_playing:
            # Currently playing, so pause
            pygame.mixer.music.pause()
            self.original_audio_playing = False
            self.original_audio_paused = True
            self.play_button.config(text="▶ Play Original")
        elif self.original_audio_paused:
            # Currently paused, so resume
            pygame.mixer.music.unpause()
            self.original_audio_playing = True
            self.original_audio_paused = False
            self.play_button.config(text="⏸ Pause")
            self.check_original_playback_status()
        else:
            # Not playing, so start playback
            segment = self.translation_data['segments'][self.current_segment_index]
            audio_path = Path(segment['file_path'])
            
            if audio_path.exists():
                try:
                    pygame.mixer.music.load(str(audio_path))
                    pygame.mixer.music.play()
                    self.original_audio_playing = True
                    self.original_audio_paused = False
                    self.play_button.config(text="⏸ Pause")
                    self.check_original_playback_status()
                except Exception as e:
                    messagebox.showerror("Playback Error", f"Could not play audio: {e}")
            else:
                messagebox.showerror("File Not Found", f"Audio file not found: {audio_path}")
    
    def check_original_playback_status(self):
        """Check if original audio is still playing and update button state"""
        if self.original_audio_playing and not pygame.mixer.music.get_busy():
            # Playback finished
            self.original_audio_playing = False
            self.original_audio_paused = False
            self.play_button.config(text="▶ Play Original")
        elif self.original_audio_playing:
            # Still playing, check again in 100ms
            self.root.after(100, self.check_original_playback_status)
    
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
        segment['english_text'] = self.english_text.get(1.0, tk.END).strip()
        segment['chinese_text'] = self.chinese_text.get(1.0, tk.END).strip()
        
        # Save to file
        self.save_translation_data()
        
        # Reset change tracking
        self.original_english_text = segment['english_text']
        self.original_chinese_text = segment['chinese_text']
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

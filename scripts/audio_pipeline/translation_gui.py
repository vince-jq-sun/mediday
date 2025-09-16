"""
GUI for manual translation review and editing with audio playback and recording
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
import pygame
import threading
import pyaudio
import wave
import time
from typing import Dict, List, Optional
from .config import GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT, MANUAL_RECORDINGS_DIR
from .translator import Translator

class TranslationReviewGUI:
    def __init__(self, translation_file: Path):
        self.translation_file = translation_file
        self.translation_data = self.load_translation_data()
        self.current_segment_index = 0
        self.translator = Translator()
        
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
        
        self.setup_gui()
        self.load_current_segment()
    
    def load_translation_data(self) -> Dict:
        """Load translation data from JSON file"""
        with open(self.translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
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
        
        # Retranslate button
        retranslate_frame = ttk.Frame(text_frame)
        retranslate_frame.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        self.retranslate_button = ttk.Button(retranslate_frame, text="🔄 Re-translate", command=self.retranslate_text)
        self.retranslate_button.grid(row=0, column=0, padx=(0, 10))
        
        self.use_terminology_var = tk.BooleanVar(value=True)
        self.terminology_checkbox = ttk.Checkbutton(retranslate_frame, text="Use Terminology", variable=self.use_terminology_var)
        self.terminology_checkbox.grid(row=0, column=1)
        
        # Chinese text
        ttk.Label(text_frame, text="Chinese Translation:").grid(row=3, column=0, sticky=tk.W)
        self.chinese_text = tk.Text(text_frame, height=4, wrap=tk.WORD)
        self.chinese_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # New translation display (for retranslation results)
        self.new_translation_frame = ttk.LabelFrame(main_frame, text="New Translation (Optional)", padding="10")
        self.new_translation_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.new_translation_frame.columnconfigure(0, weight=1)
        
        self.new_translation_text = tk.Text(self.new_translation_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.new_translation_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.copy_translation_button = ttk.Button(self.new_translation_frame, text="📋 Copy to Chinese Text", 
                                                command=self.copy_new_translation, state=tk.DISABLED)
        self.copy_translation_button.grid(row=1, column=0)
        
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
        
        # Hide new translation frame initially
        self.new_translation_frame.grid_remove()
    
    def load_current_segment(self):
        """Load current segment data into the GUI"""
        if not self.translation_data['segments']:
            return
        
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
        
        # Clear new translation
        self.new_translation_text.config(state=tk.NORMAL)
        self.new_translation_text.delete(1.0, tk.END)
        self.new_translation_text.config(state=tk.DISABLED)
        self.copy_translation_button.config(state=tk.DISABLED)
        self.new_translation_frame.grid_remove()
        
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
        recording_path = MANUAL_RECORDINGS_DIR / recording_filename
        
        if recording_path.exists():
            self.recording_status_label.config(text=f"Recording exists: {recording_path.name}")
            self.play_recording_button.config(state=tk.NORMAL)
            self.record_button.config(text="🎤 Re-record")
        else:
            self.recording_status_label.config(text="No recording")
            self.play_recording_button.config(state=tk.DISABLED)
            self.record_button.config(text="🎤 Record")
    
    def play_original_audio(self):
        """Play the original audio segment"""
        segment = self.translation_data['segments'][self.current_segment_index]
        audio_path = Path(segment['file_path'])
        
        if audio_path.exists():
            try:
                pygame.mixer.music.load(str(audio_path))
                pygame.mixer.music.play()
                self.play_button.config(text="⏸ Playing...", state=tk.DISABLED)
                
                # Re-enable button after playback (approximate)
                duration = segment.get('duration', 3) * 1000  # Convert to milliseconds
                self.root.after(int(duration), lambda: self.play_button.config(text="▶ Play Original", state=tk.NORMAL))
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play audio: {e}")
        else:
            messagebox.showerror("File Not Found", f"Audio file not found: {audio_path}")
    
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
        """Show the new translation result"""
        if translation_result.get('translated_text'):
            self.new_translation_frame.grid()
            
            self.new_translation_text.config(state=tk.NORMAL)
            self.new_translation_text.delete(1.0, tk.END)
            self.new_translation_text.insert(1.0, translation_result['translated_text'])
            self.new_translation_text.config(state=tk.DISABLED)
            
            self.copy_translation_button.config(state=tk.NORMAL)
        else:
            error_msg = translation_result.get('error', 'Unknown error')
            messagebox.showerror("Translation Error", f"Translation failed: {error_msg}")
    
    def copy_new_translation(self):
        """Copy new translation to the Chinese text field"""
        new_text = self.new_translation_text.get(1.0, tk.END).strip()
        
        self.chinese_text.delete(1.0, tk.END)
        self.chinese_text.insert(1.0, new_text)
        
        self.new_translation_frame.grid_remove()
    
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
            recording_path = MANUAL_RECORDINGS_DIR / recording_filename
            
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
        """Play the manual recording"""
        segment = self.translation_data['segments'][self.current_segment_index]
        segment_id = segment['segment_id']
        
        base_filename = Path(self.translation_data['original_file']).stem
        recording_filename = f"{base_filename}_segment_{segment_id:03d}_manual.wav"
        recording_path = MANUAL_RECORDINGS_DIR / recording_filename
        
        if recording_path.exists():
            try:
                pygame.mixer.music.load(str(recording_path))
                pygame.mixer.music.play()
                self.play_recording_button.config(text="⏸ Playing...", state=tk.DISABLED)
                
                # Re-enable button after playback (estimate 3 seconds)
                self.root.after(3000, lambda: self.play_recording_button.config(text="▶ Play Recording", state=tk.NORMAL))
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play recording: {e}")
    
    def save_current_segment(self):
        """Save current segment changes"""
        segment = self.translation_data['segments'][self.current_segment_index]
        
        # Update segment data
        segment['english_text'] = self.english_text.get(1.0, tk.END).strip()
        segment['chinese_text'] = self.chinese_text.get(1.0, tk.END).strip()
        
        # Save to file
        self.save_translation_data()
        
        messagebox.showinfo("Saved", "Segment saved successfully!")
    
    def previous_segment(self):
        """Go to previous segment"""
        if self.current_segment_index > 0:
            self.save_current_segment()
            self.current_segment_index -= 1
            self.load_current_segment()
    
    def next_segment(self):
        """Go to next segment"""
        if self.current_segment_index < len(self.translation_data['segments']) - 1:
            self.save_current_segment()
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
    launch_translation_gui()

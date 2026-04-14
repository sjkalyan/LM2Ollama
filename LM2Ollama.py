import os, subprocess, tkinter as tk, re, threading, time
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
import webbrowser

# --- CONFIG ---
LM_STUDIO_DIR = r"E:\Ai\LLModels\lmstudio-community"
OLLAMA_BLOB_DIR = Path(os.environ["USERPROFILE"]) / ".ollama" / "models" / "blobs"

class OllamaLinkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Model Linker")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e") # Dark gray background
        
        # Create a style for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom colors with better visual hierarchy
        self.style.configure('Title.TLabel',
                           foreground='#ffffff',
                           background='#1e1e1e',
                           font=('Segoe UI', 18, 'bold'))
        self.style.configure('Header.TLabel',
                           foreground='#4ecdc4',
                           background='#1e1e1e',
                           font=('Segoe UI', 12, 'bold'))
        self.style.configure('Process.TButton',
                           foreground='white',
                           background='#007acc',
                           font=('Segoe UI', 12, 'bold'),
                           padding=12,
                           borderwidth=2)
        self.style.map('Process.TButton',
                      background=[('active', '#005a9e')],
                      foreground=[('active', 'white')])
        # Add success/error/info label styles for better feedback
        self.style.configure('Success.TLabel',
                           foreground='#4caf50',
                           background='#1e1e1e',
                           font=('Segoe UI', 10, 'bold'))
        self.style.configure('Error.TLabel',
                           foreground='#f44336',
                           background='#1e1e1e',
                           font=('Segoe UI', 10, 'bold'))
        self.style.configure('Info.TLabel',
                           foreground='#2196f3',
                           background='#1e1e1e',
                           font=('Segoe UI', 10, 'bold'))
        
        # Configure a better progress bar style
        self.style.configure('Custom.Horizontal.TProgressbar',
                           troughcolor='#3d3d3d',
                           background='#4ecdc4')
        
        # Header with enhanced styling
        title_label = ttk.Label(root, text="LM STUDIO → OLLAMA LINKER", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Subheader with better visual hierarchy
        header_label = ttk.Label(root, text="Select a model folder to create an Ollama model link", style='Header.TLabel')
        header_label.pack(pady=(0, 20))
        
        # Main frame for content with better padding and layout
        main_frame = tk.Frame(root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Add a separator line for visual clarity
        separator = tk.Frame(main_frame, height=2, bg="#4ecdc4")
        separator.pack(fill=tk.X, pady=(0, 20))
        
        # Action Button with enhanced styling
        self.btn_select = ttk.Button(main_frame, text="[ SELECT MODEL FOLDER ]", command=self.start_link_thread, style='Process.TButton')
        self.btn_select.pack(pady=20)
        
        # Progress bar for operations with better styling
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300, style='Custom.Horizontal.TProgressbar')
        self.progress.pack(pady=10)
        
        # Terminal Log Area with better styling
        log_frame = tk.Frame(main_frame, bg="#2d2d2d", relief=tk.RAISED, bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', bg="#1e1e1e", fg="#cccccc",
                                                insertbackground="white", font=("Consolas", 10),
                                                borderwidth=0, highlightthickness=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add a clear button for the log area
        clear_btn = ttk.Button(main_frame, text="Clear Logs", command=self.clear_logs, style='Process.TButton')
        clear_btn.pack(pady=(0, 10))
        
        # Status bar with better styling
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                              font=('Segoe UI', 9), padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add a footer with version info
        footer_frame = tk.Frame(root, bg="#1e1e1e")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))
        footer_label = ttk.Label(footer_frame, text="LM2Ollama v1.0 - LM Studio to Ollama Linker",
                                style='Header.TLabel')
        footer_label.pack(pady=5)
        
        # Add some visual enhancements
        self.root.update_idletasks()
        
        # Add a help button for user guidance
        help_btn = ttk.Button(root, text="Help", command=self.show_help, style='Process.TButton')
        help_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
    def clean_ansi(self, text):
        """Removes the messy ANSI escape codes that cause 'garbage' text."""
        ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def log(self, message, color="#cccccc"):
        """Prints a clean line to the UI terminal."""
        clean_msg = self.clean_ansi(message).strip()
        if not clean_msg: return
        
        # Filter out the 'moving' progress lines to keep it clean
        if "%" in clean_msg and "copying" not in clean_msg.lower(): return
        
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"  {clean_msg}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')
        
        # Update status with more specific messages
        if "error" in message.lower() or "failed" in message.lower():
            self.status_var.set("Error occurred - Check logs")
        elif "success" in message.lower():
            self.status_var.set("Operation completed successfully")
        elif "copying" in message.lower():
            self.status_var.set("Copying model files...")
        elif "parsing" in message.lower():
            self.status_var.set("Parsing model data...")
        else:
            self.status_var.set("Processing...")
    
    def start_link_thread(self):
        self.btn_select.config(state=tk.DISABLED, text="[ PROCESSING... ]", style='Process.TButton')
        self.progress.start()
        threading.Thread(target=self.process_model, daemon=True).start()
    
    def process_model(self):
        folder = filedialog.askdirectory(initialdir=LM_STUDIO_DIR)
        if not folder: 
            self.reset_button()
            return
        
        folder_path = Path(folder)
        gguf_files = list(folder_path.glob("*.gguf"))
        if not gguf_files:
            self.log("[ERROR] No GGUF files found in this folder.", "#ff3333")
            self.reset_button()
            return
        
        gguf_path = max(gguf_files, key=lambda f: f.stat().st_size)
        target_size = gguf_path.stat().st_size
        
        # Smart Naming (e.g., qwen3.5-9b:q6_k)
        filename = gguf_path.stem.lower()
        parts = re.split(r'[-_](?=[qQ]\d)', filename)
        full_name = f"{parts[0]}:{parts[1]}" if len(parts) > 1 else f"{filename}:latest"
        
        self.log(f"> INITIALIZING: {full_name}")
        
        # 1. Create Modelfile
        modelfile_path = folder_path / "Modelfile"
        with open(modelfile_path, "w") as f:
            f.write(f'FROM "{str(gguf_path).replace("\\", "/")}"')
        
        # 2. Run Ollama Create (Stream output)
        process = subprocess.Popen(
            ["ollama", "create", full_name, "-f", str(modelfile_path)], 
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, encoding='utf-8', errors='replace', bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            # Only show meaningful updates
            if any(word in line.lower() for word in ["copying", "success", "writing", "parsing"]):
                self.log(line)
        
        process.wait()
        
        # 3. Perform Symlink Swap
        self.log("> CREATION COMPLETE. RECLAIMING DISK SPACE...")
        time.sleep(1.5) 
        
        blobs = list(OLLAMA_BLOB_DIR.glob("sha256-*"))
        match = next((b for b in blobs if abs(b.stat().st_size - target_size) < 1024*1024), None)
        
        if match:
            try:
                os.remove(match)
                os.symlink(str(gguf_path), str(match))
                self.log(f"[SUCCESS] {full_name} is now linked to E: drive.")
                self.log(f"[INFO] Space reclaimed: {target_size / 1e9:.2f} GB")
            except Exception as e:
                self.log(f"[PERMISSION ERROR] Run as Admin! {e}")
        else:
            self.log("[WARNING] Matching blob not found. Model exists but still taking space.")
        
        self.log("-" * 70)
        self.reset_button()
    
    def reset_button(self):
        self.btn_select.config(state=tk.NORMAL, text="[ SELECT MODEL FOLDER ]", style='Process.TButton')
        self.progress.stop()
        self.status_var.set("Ready")
    
    def clear_logs(self):
        """Clear the log area."""
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
    
    def show_help(self):
        """Show help information."""
        help_text = """
LM2Ollama Help:
- Click "SELECT MODEL FOLDER" to choose an LM Studio model directory
- The app will find the largest GGUF file in that folder
- It creates a Modelfile and registers it with Ollama
- Creates symbolic links to save disk space
- Progress is shown in the log area at the bottom

Requirements:
- LM Studio models installed
- Ollama running and accessible
- Administrative privileges for symlinks

Troubleshooting:
- If you get permission errors, run as administrator
- Make sure your model folder contains a .gguf file
- Verify Ollama is properly installed and running
        """
        messagebox.showinfo("LM2Ollama Help", help_text)
 
if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaLinkerApp(root)
    root.mainloop()

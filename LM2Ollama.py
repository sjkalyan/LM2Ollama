import os
import subprocess
import tkinter as tk
import re
import threading
import time
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

# --- CONFIG ---
LM_STUDIO_DIR = r"E:\Ai\LLModels\lmstudio-community"
OLLAMA_BLOB_DIR = Path(os.environ["USERPROFILE"]) / ".ollama" / "models" / "blobs"

# --- THEME ---
BG_MAIN = "#181f2e"       # deep slate
BG_CARD = "#272f3b"       # card surface
BG_TERMINAL = "#020617"   # terminal/log area
ACCENT = "#3baef6"        # slate blue
ACCENT_HOVER = "#25d1eb"
HIGHLIGHT = "#22c55e"     # green
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BORDER = "#272f3b"
ERROR = "#ef4444"
WARNING = "#f59e0b"
INFO = "#38bdf8"


class OllamaLinkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LM2Ollama")
        self.root.geometry("980x760")
        self.root.minsize(860, 620)
        self.root.configure(bg=BG_MAIN)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.status_var = tk.StringVar(value="Ready")

        self.build_ui()

    def configure_styles(self):
        self.style.configure(
            "Title.TLabel",
            background=BG_MAIN,
            foreground=TEXT,
            font=("Segoe UI", 20, "bold")
        )

        self.style.configure(
            "Subtitle.TLabel",
            background=BG_MAIN,
            foreground=MUTED,
            font=("Segoe UI", 10)
        )

        self.style.configure(
            "Section.TLabel",
            background=BG_CARD,
            foreground=TEXT,
            font=("Segoe UI", 11, "bold")
        )

        self.style.configure(
            "Modern.TButton",
            background=ACCENT,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 9),
            borderwidth=0,
            focusthickness=0
        )
        self.style.map(
            "Modern.TButton",
            background=[("active", ACCENT_HOVER), ("disabled", "#475569")],
            foreground=[("disabled", "#cbd5e1")]
        )

        self.style.configure(
            "Subtle.TButton",
            background=BG_CARD,
            foreground=TEXT,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 8),
            borderwidth=1,
            relief="flat"
        )
        self.style.map(
            "Subtle.TButton",
            background=[("active", "#273449"), ("disabled", "#223046")],
            foreground=[("disabled", "#64748b")]
        )

        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=BG_CARD,
            background=ACCENT,
            bordercolor=BG_CARD,
            lightcolor=ACCENT,
            darkcolor=ACCENT
        )

    def build_ui(self):
        outer = tk.Frame(self.root, bg=BG_MAIN)
        outer.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # Header
        header = tk.Frame(outer, bg=BG_MAIN)
        header.pack(fill=tk.X, pady=(0, 16))

        title_label = ttk.Label(header, text="LM STUDIO → OLLAMA LINKER", style="Title.TLabel")
        title_label.pack(anchor="center")

        subtitle_label = ttk.Label(
            header,
            text="Select a model folder and register it with Ollama while reclaiming duplicate storage.",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor="center", pady=(6, 0))

        # Main card
        card = tk.Frame(
            outer,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0
        )
        card.pack(fill=tk.BOTH, expand=True)

        top_bar = tk.Frame(card, bg=BG_CARD)
        top_bar.pack(fill=tk.X, padx=20, pady=(18, 12))

        left_actions = tk.Frame(top_bar, bg=BG_CARD)
        left_actions.pack(side=tk.LEFT)

        self.btn_select = ttk.Button(
            left_actions,
            text="Select Model Folder",
            command=self.start_link_thread,
            style="Modern.TButton"
        )
        self.btn_select.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(
            left_actions,
            text="Clear Logs",
            command=self.clear_logs,
            style="Subtle.TButton"
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 8))

        help_btn = ttk.Button(
            left_actions,
            text="Help",
            command=self.show_help,
            style="Subtle.TButton"
        )
        help_btn.pack(side=tk.LEFT)

        right_info = tk.Frame(top_bar, bg=BG_CARD)
        right_info.pack(side=tk.RIGHT)

        version_label = tk.Label(
            right_info,
            text="v1.1",
            bg=BG_CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        )
        version_label.pack(anchor="e")

        # Progress section
        progress_wrap = tk.Frame(card, bg=BG_CARD)
        progress_wrap.pack(fill=tk.X, padx=20, pady=(0, 12))

        progress_label = tk.Label(
            progress_wrap,
            text="Activity",
            bg=BG_CARD,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        )
        progress_label.pack(anchor="w", pady=(0, 8))

        self.progress = ttk.Progressbar(
            progress_wrap,
            mode="indeterminate",
            length=300,
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X)

        # Log section
        log_wrap = tk.Frame(card, bg=BG_CARD)
        log_wrap.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        log_label = tk.Label(
            log_wrap,
            text="Logs",
            bg=BG_CARD,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        )
        log_label.pack(anchor="w", pady=(0, 8))

        log_container = tk.Frame(
            log_wrap,
            bg=BG_TERMINAL,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0
        )
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_container,
            state="disabled",
            bg=BG_TERMINAL,
            fg="#cbd5e1",
            insertbackground=TEXT,
            font=("Consolas", 10),
            borderwidth=0,
            highlightthickness=0,
            wrap=tk.WORD,
            padx=12,
            pady=12
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.log_area.tag_config("default", foreground="#cbd5e1")
        self.log_area.tag_config("success", foreground=HIGHLIGHT)
        self.log_area.tag_config("error", foreground=ERROR)
        self.log_area.tag_config("warning", foreground=WARNING)
        self.log_area.tag_config("info", foreground=INFO)

        # Footer status
        status_bar = tk.Frame(self.root, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        status_text = tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=BG_CARD,
            fg=MUTED,
            anchor="w",
            font=("Segoe UI", 9),
            padx=12,
            pady=8
        )
        status_text.pack(fill=tk.X)

    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def log(self, message, level="default"):
        clean_msg = self.clean_ansi(message).strip()
        if not clean_msg:
            return

        if "%" in clean_msg and "copying" not in clean_msg.lower():
            return

        self.log_area.configure(state="normal")
        self.log_area.insert(tk.END, f"{clean_msg}\n", level)
        self.log_area.see(tk.END)
        self.log_area.configure(state="disabled")

        msg_lower = clean_msg.lower()
        if "error" in msg_lower or "failed" in msg_lower or "permission" in msg_lower:
            self.status_var.set("Error occurred. Check logs.")
        elif "success" in msg_lower:
            self.status_var.set("Completed successfully.")
        elif "copying" in msg_lower:
            self.status_var.set("Copying model files...")
        elif "parsing" in msg_lower:
            self.status_var.set("Parsing model data...")
        elif "initializing" in msg_lower:
            self.status_var.set("Initializing model creation...")
        elif "reclaiming" in msg_lower:
            self.status_var.set("Reclaiming disk space...")
        else:
            self.status_var.set("Processing...")

    def start_link_thread(self):
        self.btn_select.config(state=tk.DISABLED, text="Processing...")
        self.progress.start(10)
        threading.Thread(target=self.process_model, daemon=True).start()

    def process_model(self):
        try:
            folder = filedialog.askdirectory(initialdir=LM_STUDIO_DIR)
            if not folder:
                self.reset_button()
                return

            folder_path = Path(folder)
            gguf_files = list(folder_path.glob("*.gguf"))

            if not gguf_files:
                self.log("[ERROR] No GGUF files found in this folder.", "error")
                self.reset_button()
                return

            gguf_path = max(gguf_files, key=lambda f: f.stat().st_size)
            target_size = gguf_path.stat().st_size

            filename = gguf_path.stem.lower()
            parts = re.split(r'[-_](?=[qQ]\d)', filename)
            full_name = f"{parts[0]}:{parts[1]}" if len(parts) > 1 else f"{filename}:latest"

            self.log(f"Initializing: {full_name}", "info")
            self.log(f"Using GGUF file: {gguf_path.name}", "default")

            # Create Modelfile
            modelfile_path = folder_path / "Modelfile"
            with open(modelfile_path, "w", encoding="utf-8") as f:
                gguf_str = str(gguf_path).replace("\\", "/")
                f.write(f'FROM "{gguf_str}"')

            self.log("Created Modelfile.", "info")

            # Run ollama create
            process = subprocess.Popen(
                ["ollama", "create", full_name, "-f", str(modelfile_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            for line in iter(process.stdout.readline, ''):
                lower = line.lower()
                if any(word in lower for word in ["copying", "success", "writing", "parsing", "transferring"]):
                    if "success" in lower:
                        self.log(line, "success")
                    elif "copying" in lower or "transferring" in lower:
                        self.log(line, "info")
                    else:
                        self.log(line, "default")

            process.wait()

            if process.returncode != 0:
                self.log("[ERROR] Ollama create failed. Make sure Ollama is installed and available in PATH.", "error")
                self.reset_button()
                return

            self.log("Creation complete. Reclaiming disk space...", "info")
            time.sleep(1.2)

            blobs = list(OLLAMA_BLOB_DIR.glob("sha256-*"))
            match = next((b for b in blobs if abs(b.stat().st_size - target_size) < 1024 * 1024), None)

            if match:
                try:
                    os.remove(match)
                    os.symlink(str(gguf_path), str(match))
                    self.log(f"[SUCCESS] {full_name} is now linked to the LM Studio model file.", "success")
                    self.log(f"[INFO] Space reclaimed: {target_size / 1e9:.2f} GB", "info")
                except Exception as e:
                    self.log(f"[PERMISSION ERROR] Run as Administrator to create symlinks. {e}", "error")
            else:
                self.log("[WARNING] Matching blob not found. Model exists, but duplicate storage may still remain.", "warning")

            self.log("-" * 68, "default")

        except FileNotFoundError:
            self.log("[ERROR] Could not find 'ollama'. Make sure Ollama is installed and added to PATH.", "error")
        except Exception as e:
            self.log(f"[ERROR] Unexpected error: {e}", "error")
        finally:
            self.reset_button()

    def reset_button(self):
        self.progress.stop()
        self.btn_select.config(state=tk.NORMAL, text="Select Model Folder")
        self.status_var.set("Ready")

    def clear_logs(self):
        self.log_area.configure(state="normal")
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state="disabled")
        self.status_var.set("Logs cleared.")

    def show_help(self):
        help_text = (
            "LM2Ollama Help\n\n"
            "1. Click 'Select Model Folder' and choose an LM Studio model directory.\n"
            "2. The app finds the largest GGUF file in that folder.\n"
            "3. It creates a Modelfile and registers the model with Ollama.\n"
            "4. It then swaps the duplicated Ollama blob with a symlink to save space.\n\n"
            "Requirements:\n"
            "• LM Studio model folder containing a .gguf file\n"
            "• Ollama installed and available in PATH\n"
            "• Administrative privileges for symlink creation on Windows\n\n"
            "Troubleshooting:\n"
            "• If symlink creation fails, run the app as Administrator\n"
            "• If no GGUF file is found, verify the selected folder\n"
            "• If Ollama create fails, verify Ollama is installed and working"
        )
        messagebox.showinfo("LM2Ollama Help", help_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaLinkerApp(root)
    root.mainloop()
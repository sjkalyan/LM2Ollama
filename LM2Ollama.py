import os
import subprocess
import re
import threading
import time
from pathlib import Path
import tkinter.filedialog as filedialog

import customtkinter as ctk


# --- CONFIG ---
LM_STUDIO_DIR = r"E:\Ai\LLModels\lmstudio-community"
OLLAMA_BLOB_DIR = Path(os.environ["USERPROFILE"]) / ".ollama" / "models" / "blobs"

# --- THEME ---
BG = "#181e2d"
CARD = "#181e2d"
CARD_ALT = "#181e2d"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"
INFO = "#38bdf8"
BORDER = "#181e2d"


class OllamaLinkerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LM2Ollama")
        self.geometry("980x760")
        self.minsize(860, 620)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=BG)

        self.status_var = ctk.StringVar(value="Ready")
        self.is_processing = False

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="LM STUDIO → OLLAMA LINKER",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=TEXT,
            anchor="center",
        )
        title_label.grid(row=0, column=0, sticky="n")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Register an LM Studio GGUF model in Ollama and reclaim duplicate storage with symlinks.",
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
            anchor="center",
        )
        subtitle_label.grid(row=1, column=0, sticky="n", pady=(6, 0))

        # Main card
        main_card = ctk.CTkFrame(
            self,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        main_card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 18))
        main_card.grid_rowconfigure(2, weight=1)
        main_card.grid_columnconfigure(0, weight=1)

        # Top controls
        top_bar = ctk.CTkFrame(main_card, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 10))
        top_bar.grid_columnconfigure(0, weight=1)

        left_actions = ctk.CTkFrame(top_bar, fg_color="transparent")
        left_actions.grid(row=0, column=0, sticky="w")

        self.btn_select = ctk.CTkButton(
            left_actions,
            text="Select Model Folder",
            command=self.start_link_thread,
            height=38,
            corner_radius=14,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_select.grid(row=0, column=0, padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            left_actions,
            text="Clear Logs",
            command=self.clear_logs,
            height=38,
            corner_radius=14,
            fg_color=CARD_ALT,
            hover_color="#1f2937",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
            width=110,
        )
        self.btn_clear.grid(row=0, column=1, padx=(0, 8))

        self.btn_help = ctk.CTkButton(
            left_actions,
            text="Help",
            command=self.show_help,
            height=38,
            corner_radius=14,
            fg_color=CARD_ALT,
            hover_color="#1f2937",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
            width=90,
        )
        self.btn_help.grid(row=0, column=2)

        version_label = ctk.CTkLabel(
            top_bar,
            text="v1.1",
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
        )
        version_label.grid(row=0, column=1, sticky="e")

        # Progress section
        progress_section = ctk.CTkFrame(
            main_card,
            fg_color=CARD_ALT,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        progress_section.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))
        progress_section.grid_columnconfigure(0, weight=1)

        progress_label = ctk.CTkLabel(
            progress_section,
            text="Activity",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=MUTED,
            anchor="w",
        )
        progress_label.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        self.progress = ctk.CTkProgressBar(
            progress_section,
            height=10,
            corner_radius=999,
            fg_color="#0b1220",
            progress_color=ACCENT,
        )
        self.progress.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.progress.set(0)

        # Log section
        log_section = ctk.CTkFrame(
            main_card,
            fg_color="transparent",
        )
        log_section.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        log_section.grid_rowconfigure(1, weight=1)
        log_section.grid_columnconfigure(0, weight=1)

        log_label = ctk.CTkLabel(
            log_section,
            text="Logs",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=MUTED,
            anchor="w",
        )
        log_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.log_box = ctk.CTkTextbox(
            log_section,
            corner_radius=14,
            fg_color="#020617",
            border_width=1,
            border_color=BORDER,
            text_color="#cbd5e1",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self.log_box.grid(row=1, column=0, sticky="nsew")
        self.log_box.configure(state="disabled")

        # Status bar
        status_frame = ctk.CTkFrame(
            self,
            fg_color=CARD,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
            height=40,
        )
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
            anchor="w",
        )
        status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)

    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def append_log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def log(self, message, level="default"):
        clean_msg = self.clean_ansi(message).strip()
        if not clean_msg:
            return

        if "%" in clean_msg and "copying" not in clean_msg.lower():
            return

        prefix = ""
        if level == "success":
            prefix = "✓ "
        elif level == "error":
            prefix = "✕ "
        elif level == "warning":
            prefix = "⚠ "
        elif level == "info":
            prefix = "• "

        self.append_log(f"{prefix}{clean_msg}")

        msg_lower = clean_msg.lower()
        if "error" in msg_lower or "failed" in msg_lower or "permission" in msg_lower:
            self.status_var.set("Error occurred. Check logs.")
        elif "success" in msg_lower:
            self.status_var.set("Completed successfully.")
        elif "copying" in msg_lower or "transferring" in msg_lower:
            self.status_var.set("Copying model files...")
        elif "parsing" in msg_lower:
            self.status_var.set("Parsing model data...")
        elif "initializing" in msg_lower:
            self.status_var.set("Initializing model creation...")
        elif "reclaiming" in msg_lower:
            self.status_var.set("Reclaiming disk space...")
        else:
            self.status_var.set("Processing...")

    def animate_progress_start(self):
        self.progress.configure(mode="indeterminate")
        self.progress.start()

    def animate_progress_stop(self):
        self.progress.set(0)
        self.progress.stop()
        self.progress.configure(mode="determinate")

    def set_processing_state(self, processing: bool):
        self.is_processing = processing
        if processing:
            self.btn_select.configure(state="disabled", text="Processing...")
            self.btn_clear.configure(state="disabled")
            self.btn_help.configure(state="disabled")
            self.animate_progress_start()
        else:
            self.btn_select.configure(state="normal", text="Select Model Folder")
            self.btn_clear.configure(state="normal")
            self.btn_help.configure(state="normal")
            self.animate_progress_stop()
            self.status_var.set("Ready")

    def start_link_thread(self):
        if self.is_processing:
            return
        self.set_processing_state(True)
        threading.Thread(target=self.process_model, daemon=True).start()

    def process_model(self):
        try:
            folder = filedialog.askdirectory(initialdir=LM_STUDIO_DIR)
            if not folder:
                self.after(0, lambda: self.set_processing_state(False))
                return

            folder_path = Path(folder)
            gguf_files = list(folder_path.glob("*.gguf"))

            if not gguf_files:
                self.after(0, lambda: self.log("No GGUF files found in this folder.", "error"))
                self.after(0, lambda: self.set_processing_state(False))
                return

            gguf_path = max(gguf_files, key=lambda f: f.stat().st_size)
            target_size = gguf_path.stat().st_size

            filename = gguf_path.stem.lower()
            parts = re.split(r'[-_](?=[qQ]\d)', filename)
            full_name = f"{parts[0]}:{parts[1]}" if len(parts) > 1 else f"{filename}:latest"

            self.after(0, lambda: self.log(f"Initializing: {full_name}", "info"))
            self.after(0, lambda: self.log(f"Using GGUF file: {gguf_path.name}", "default"))

            modelfile_path = folder_path / "Modelfile"
            with open(modelfile_path, "w", encoding="utf-8") as f:
                gguf_str = str(gguf_path).replace("\\", "/")
                f.write(f'FROM "{gguf_str}"')

            self.after(0, lambda: self.log("Created Modelfile.", "info"))

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
                        self.after(0, lambda l=line: self.log(l, "success"))
                    elif "copying" in lower or "transferring" in lower:
                        self.after(0, lambda l=line: self.log(l, "info"))
                    else:
                        self.after(0, lambda l=line: self.log(l, "default"))

            process.wait()

            if process.returncode != 0:
                self.after(0, lambda: self.log(
                    "Ollama create failed. Make sure Ollama is installed and available in PATH.",
                    "error"
                ))
                self.after(0, lambda: self.set_processing_state(False))
                return

            self.after(0, lambda: self.log("Creation complete. Reclaiming disk space...", "info"))
            time.sleep(1.2)

            blobs = list(OLLAMA_BLOB_DIR.glob("sha256-*"))
            match = next((b for b in blobs if abs(b.stat().st_size - target_size) < 1024 * 1024), None)

            if match:
                try:
                    os.remove(match)
                    os.symlink(str(gguf_path), str(match))
                    self.after(0, lambda: self.log(
                        f"{full_name} is now linked to the LM Studio model file.",
                        "success"
                    ))
                    self.after(0, lambda: self.log(
                        f"Space reclaimed: {target_size / 1e9:.2f} GB",
                        "info"
                    ))
                except Exception as e:
                    self.after(0, lambda err=e: self.log(
                        f"Run as Administrator to create symlinks. {err}",
                        "error"
                    ))
            else:
                self.after(0, lambda: self.log(
                    "Matching blob not found. Model exists, but duplicate storage may still remain.",
                    "warning"
                ))

            self.after(0, lambda: self.log("-" * 68, "default"))

        except FileNotFoundError:
            self.after(0, lambda: self.log(
                "Could not find 'ollama'. Make sure Ollama is installed and added to PATH.",
                "error"
            ))
        except Exception as e:
            self.after(0, lambda err=e: self.log(f"Unexpected error: {err}", "error"))
        finally:
            self.after(0, lambda: self.set_processing_state(False))

    def clear_logs(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.status_var.set("Logs cleared.")

    def show_help(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("LM2Ollama Help")
        help_window.geometry("560x420")
        help_window.configure(fg_color=BG)
        help_window.grab_set()

        container = ctk.CTkFrame(
            help_window,
            fg_color=CARD,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
        )
        container.pack(fill="both", expand=True, padx=16, pady=16)

        title = ctk.CTkLabel(
            container,
            text="LM2Ollama Help",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT,
        )
        title.pack(anchor="w", padx=18, pady=(18, 10))

        help_text = (
            "1. Click 'Select Model Folder' and choose an LM Studio model directory.\n\n"
            "2. The app finds the largest GGUF file in that folder.\n\n"
            "3. It creates a Modelfile and registers the model with Ollama.\n\n"
            "4. It then swaps the duplicated Ollama blob with a symlink to save disk space.\n\n"
            "Requirements:\n"
            "• LM Studio model folder containing a .gguf file\n"
            "• Ollama installed and available in PATH\n"
            "• Administrative privileges for symlink creation on Windows\n\n"
            "Troubleshooting:\n"
            "• If symlink creation fails, run the app as Administrator\n"
            "• If no GGUF file is found, verify the selected folder\n"
            "• If Ollama create fails, verify Ollama is installed and working"
        )

        textbox = ctk.CTkTextbox(
            container,
            fg_color=CARD_ALT,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            text_color="#cbd5e1",
            font=ctk.CTkFont(size=13),
            wrap="word",
        )
        textbox.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        textbox.insert("1.0", help_text)
        textbox.configure(state="disabled")


if __name__ == "__main__":
    app = OllamaLinkerApp()
    app.mainloop()
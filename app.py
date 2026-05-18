# app.py — HexCrypt GUI
# A Fernet-based encryption/decryption desktop app built with customtkinter.

import csv
import os
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from core import encrypt_text, decrypt_text, generate_key

# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────
APP_TITLE   = "HexCrypt"
APP_VERSION = "2.0.0"
LOG_FILE    = "log.csv"
LOG_HEADER  = ["Timestamp", "Operation", "Input Text", "Key", "Output"]

FONT_HEADING = ("Poppins", 22, "bold")
FONT_LABEL   = ("Poppins", 14)
FONT_SMALL   = ("Poppins", 12)
FONT_MONO    = ("Courier New", 12)

WIDGET_WIDTH = 640
BTN_HEIGHT   = 38


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def _ensure_log_file():
    """Create log.csv with a header row if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(LOG_HEADER)


def _append_log(operation: str, input_text: str, key: str, output: str):
    """Prepend a new row to the log file (newest entry first)."""
    _ensure_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = [timestamp, operation, input_text, key, output]

    with open(LOG_FILE, mode="r", encoding="utf-8") as f:
        existing = list(csv.reader(f))

    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(LOG_HEADER)
        writer.writerow(new_row)
        # Skip old header row if present, write the rest
        for row in existing:
            if row != LOG_HEADER:
                writer.writerow(row)


def _copy_to_clipboard(root: ctk.CTk, text: str):
    """Copy text to the system clipboard."""
    root.clipboard_clear()
    root.clipboard_append(text)


# ─────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────
class HexCryptApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.geometry("720x820")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Internal state
        self._current_output = ""
        self._current_key    = ""

        self._build_ui()
        _ensure_log_file()

    # ── UI Construction ──────────────────────
    def _build_ui(self):
        # ── Header bar ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            header_frame, text=APP_TITLE, font=FONT_HEADING
        ).pack(side="left")

        # Theme toggle (right side of header)
        self._theme_var = ctk.StringVar(value="dark")
        theme_switch = ctk.CTkSwitch(
            header_frame,
            text="Light mode",
            font=FONT_SMALL,
            variable=self._theme_var,
            onvalue="light",
            offvalue="dark",
            command=self._toggle_theme,
        )
        theme_switch.pack(side="right", padx=4)

        # ── Tab view ──
        self._tabs = ctk.CTkTabview(self, width=680, height=680)
        self._tabs.pack(padx=20, pady=12, fill="both", expand=True)

        self._tabs.add("🔒  Encrypt / Decrypt")
        self._tabs.add("📋  Logs")
        self._tabs.add("ℹ️  About")

        self._build_main_tab(self._tabs.tab("🔒  Encrypt / Decrypt"))
        self._build_log_tab(self._tabs.tab("📋  Logs"))
        self._build_about_tab(self._tabs.tab("ℹ️  About"))

        # ── Status bar ──
        self._status_var = ctk.StringVar(value="Ready.")
        ctk.CTkLabel(
            self, textvariable=self._status_var, font=FONT_SMALL, anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 8))

    def _build_main_tab(self, parent):
        pad = {"padx": 16, "pady": 6}

        # Input
        ctk.CTkLabel(parent, text="Input Text", font=FONT_LABEL, anchor="w").pack(
            fill="x", **pad
        )
        self._input_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Enter text to encrypt or paste token to decrypt",
            width=WIDGET_WIDTH,
            height=40,
            font=FONT_MONO,
        )
        self._input_entry.pack(**pad)

        # Key row
        ctk.CTkLabel(parent, text="Key", font=FONT_LABEL, anchor="w").pack(
            fill="x", **pad
        )
        key_row = ctk.CTkFrame(parent, fg_color="transparent")
        key_row.pack(fill="x", **pad)

        self._key_entry = ctk.CTkEntry(
            key_row,
            placeholder_text="Paste existing key here (leave blank to auto-generate on encrypt)",
            width=520,
            height=40,
            font=FONT_MONO,
        )
        self._key_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            key_row,
            text="Generate Key",
            width=112,
            height=40,
            font=FONT_SMALL,
            command=self._generate_key,
        ).pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="🔒  Encrypt",
            width=300,
            height=BTN_HEIGHT,
            font=FONT_LABEL,
            command=self._do_encrypt,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="🔓  Decrypt",
            width=300,
            height=BTN_HEIGHT,
            font=FONT_LABEL,
            fg_color="#2d6a4f",
            hover_color="#1b4332",
            command=self._do_decrypt,
        ).pack(side="left")

        ctk.CTkButton(
            parent,
            text="✖  Clear",
            width=WIDGET_WIDTH,
            height=BTN_HEIGHT,
            font=FONT_LABEL,
            fg_color="#555",
            hover_color="#333",
            command=self._clear_fields,
        ).pack(padx=16, pady=(0, 10))

        # Output
        ctk.CTkLabel(parent, text="Output", font=FONT_LABEL, anchor="w").pack(
            fill="x", **pad
        )
        self._output_box = ctk.CTkTextbox(
            parent, width=WIDGET_WIDTH, height=80, font=FONT_MONO, state="disabled"
        )
        self._output_box.pack(**pad)

        out_btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        out_btn_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(
            out_btn_row,
            text="Copy Output",
            width=200,
            height=34,
            font=FONT_SMALL,
            command=self._copy_output,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            out_btn_row,
            text="Copy Key",
            width=200,
            height=34,
            font=FONT_SMALL,
            fg_color="#555",
            hover_color="#333",
            command=self._copy_key,
        ).pack(side="left")

        # Key display
        ctk.CTkLabel(parent, text="Key Used", font=FONT_LABEL, anchor="w").pack(
            fill="x", **pad
        )
        self._key_display = ctk.CTkTextbox(
            parent, width=WIDGET_WIDTH, height=50, font=FONT_MONO, state="disabled"
        )
        self._key_display.pack(**pad)

    def _build_log_tab(self, parent):
        # Toolbar
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkButton(
            toolbar,
            text="🔄  Refresh",
            width=120,
            height=34,
            font=FONT_SMALL,
            command=self._refresh_logs,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            toolbar,
            text="🗑  Clear Logs",
            width=120,
            height=34,
            font=FONT_SMALL,
            fg_color="#8b0000",
            hover_color="#5c0000",
            command=self._clear_logs,
        ).pack(side="left")

        # Scrollable table
        self._log_frame = ctk.CTkScrollableFrame(parent, width=640, height=560)
        self._log_frame.pack(padx=12, pady=8, fill="both", expand=True)

        self._refresh_logs()

    def _build_about_tab(self, parent):
        pad = {"padx": 24, "pady": 8}
        ctk.CTkLabel(parent, text=APP_TITLE, font=FONT_HEADING).pack(**pad)
        ctk.CTkLabel(parent, text=f"Version {APP_VERSION}", font=FONT_SMALL).pack(pady=2)

        info = (
            "HexCrypt is a desktop encryption tool powered by the Fernet\n"
            "symmetric encryption scheme (AES-128-CBC + HMAC-SHA256).\n\n"
            "How to use:\n"
            "  • Encrypt — type your text, optionally paste or generate a key,\n"
            "    then click Encrypt. The key is required to decrypt later.\n\n"
            "  • Decrypt — paste the encrypted token into Input Text,\n"
            "    paste the original key into the Key field, then click Decrypt.\n\n"
            "  • Generate Key — creates a fresh random Fernet key and fills\n"
            "    the Key field automatically.\n\n"
            "  • Logs — every operation is recorded with a timestamp.\n\n"
            "⚠  Keep your key safe. Without it, encrypted data cannot be recovered."
        )
        ctk.CTkLabel(
            parent, text=info, font=FONT_SMALL, justify="left", wraplength=600
        ).pack(**pad)

    # ── Actions ──────────────────────────────
    def _generate_key(self):
        key = generate_key().decode()
        self._key_entry.delete(0, "end")
        self._key_entry.insert(0, key)
        self._set_status("New key generated and placed in the Key field.")

    def _do_encrypt(self):
        input_text = self._input_entry.get().strip()
        key_text   = self._key_entry.get().strip()

        if not input_text:
            messagebox.showwarning("Missing Input", "Please enter text to encrypt.")
            return

        # Auto-generate key if blank
        if not key_text:
            key_text = generate_key().decode()
            self._key_entry.delete(0, "end")
            self._key_entry.insert(0, key_text)

        try:
            result = encrypt_text(input_text, key_text.encode())
        except Exception as e:
            messagebox.showerror("Encryption Error", str(e))
            return

        self._current_output = result
        self._current_key    = key_text
        self._set_output(result)
        self._set_key_display(key_text)
        _append_log("Encrypt", input_text, key_text, result)
        self._set_status(f"Encrypted successfully at {datetime.now().strftime('%H:%M:%S')}.")

    def _do_decrypt(self):
        input_text = self._input_entry.get().strip()
        key_text   = self._key_entry.get().strip()

        if not input_text:
            messagebox.showwarning("Missing Input", "Please enter the encrypted token.")
            return
        if not key_text:
            messagebox.showwarning("Missing Key", "A key is required for decryption.")
            return

        try:
            result = decrypt_text(input_text, key_text)
        except Exception as e:
            messagebox.showerror("Decryption Error", f"Could not decrypt.\n\n{e}")
            return

        self._current_output = result
        self._current_key    = key_text
        self._set_output(result)
        self._set_key_display(key_text)
        _append_log("Decrypt", input_text, key_text, result)
        self._set_status(f"Decrypted successfully at {datetime.now().strftime('%H:%M:%S')}.")

    def _clear_fields(self):
        self._input_entry.delete(0, "end")
        self._key_entry.delete(0, "end")
        self._set_output("")
        self._set_key_display("")
        self._current_output = ""
        self._current_key    = ""
        self._set_status("Fields cleared.")

    def _copy_output(self):
        if self._current_output:
            _copy_to_clipboard(self, self._current_output)
            self._set_status("Output copied to clipboard.")
        else:
            self._set_status("Nothing to copy.")

    def _copy_key(self):
        if self._current_key:
            _copy_to_clipboard(self, self._current_key)
            self._set_status("Key copied to clipboard.")
        else:
            self._set_status("No key to copy.")

    def _toggle_theme(self):
        mode = self._theme_var.get()
        ctk.set_appearance_mode(mode)

    # ── Log tab helpers ───────────────────────
    def _refresh_logs(self):
        # Clear existing widgets
        for widget in self._log_frame.winfo_children():
            widget.destroy()

        _ensure_log_file()
        try:
            with open(LOG_FILE, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
        except FileNotFoundError:
            ctk.CTkLabel(self._log_frame, text="No log file found.", font=FONT_SMALL).grid(
                row=0, column=0, padx=8, pady=8
            )
            return

        if not rows:
            ctk.CTkLabel(self._log_frame, text="Log is empty.", font=FONT_SMALL).grid(
                row=0, column=0, padx=8, pady=8
            )
            return

        col_widths = [140, 80, 160, 200, 200]
        for i, row in enumerate(rows):
            is_header = i == 0
            bg = "#1f538d" if is_header else ("#2b2b2b" if i % 2 == 0 else "#1e1e1e")
            font = ("Poppins", 12, "bold") if is_header else FONT_SMALL

            for j, value in enumerate(row):
                width = col_widths[j] if j < len(col_widths) else 120
                lbl = ctk.CTkLabel(
                    self._log_frame,
                    text=value,
                    fg_color=bg,
                    text_color="white",
                    font=font,
                    width=width,
                    anchor="w",
                )
                lbl.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)

        for col in range(len(rows[0])):
            self._log_frame.grid_columnconfigure(col, weight=1)

        self._set_status(f"Logs refreshed — {len(rows) - 1} record(s).")

    def _clear_logs(self):
        confirm = messagebox.askyesno(
            "Clear Logs",
            "This will permanently delete all log entries. Continue?",
        )
        if confirm:
            with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(LOG_HEADER)
            self._refresh_logs()
            self._set_status("Logs cleared.")

    # ── Internal display helpers ──────────────
    def _set_output(self, text: str):
        self._output_box.configure(state="normal")
        self._output_box.delete("1.0", "end")
        self._output_box.insert("1.0", text)
        self._output_box.configure(state="disabled")

    def _set_key_display(self, text: str):
        self._key_display.configure(state="normal")
        self._key_display.delete("1.0", "end")
        self._key_display.insert("1.0", text)
        self._key_display.configure(state="disabled")

    def _set_status(self, message: str):
        self._status_var.set(message)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = HexCryptApp()
    app.mainloop()

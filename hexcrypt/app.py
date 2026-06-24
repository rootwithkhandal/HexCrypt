# app.py — HexCrypt GUI
# An AES-GCM encryption/decryption desktop app built with customtkinter.

import csv
import os
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from hexcrypt import core
from cryptography.exceptions import InvalidTag

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
    """Append a new row to the log file."""
    _ensure_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([timestamp, operation, input_text, key, output])





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
        self._tabs.add("🖼️  Steganography")
        self._tabs.add("📋  Logs")
        self._tabs.add("ℹ️  About")

        # ── Status bar ──
        self._status_var = ctk.StringVar(value="Ready.")
        
        self._build_main_tab(self._tabs.tab("🔒  Encrypt / Decrypt"))
        self._build_steg_tab(self._tabs.tab("🖼️  Steganography"))
        self._build_log_tab(self._tabs.tab("📋  Logs"))
        self._build_about_tab(self._tabs.tab("ℹ️  About"))

        ctk.CTkLabel(
            self, textvariable=self._status_var, font=FONT_SMALL, anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 8))

    def _build_main_tab(self, parent):
        pad = {"padx": 16, "pady": 6}

        # Mode selector
        self._mode_var = ctk.StringVar(value="Symmetric")
        mode_seg = ctk.CTkSegmentedButton(
            parent, values=["Symmetric", "Asymmetric"],
            variable=self._mode_var, command=self._on_mode_change
        )
        mode_seg.pack(fill="x", padx=16, pady=(6, 12))

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
        # Key header row
        key_header = ctk.CTkFrame(parent, fg_color="transparent")
        key_header.pack(fill="x", padx=16, pady=(6, 0))
        self._key_label = ctk.CTkLabel(key_header, text="Key or Passphrase", font=FONT_LABEL, anchor="w")
        self._key_label.pack(side="left")
        
        self._passphrase_var = ctk.BooleanVar(value=False)
        self._passphrase_switch = ctk.CTkSwitch(
            key_header, text="Use Passphrase", font=FONT_SMALL,
            variable=self._passphrase_var, command=self._toggle_passphrase
        )
        self._passphrase_switch.pack(side="right")

        key_row = ctk.CTkFrame(parent, fg_color="transparent")
        key_row.pack(fill="x", padx=16, pady=(0, 6))

        self._key_entry = ctk.CTkEntry(
            key_row,
            placeholder_text="Paste key here (leave blank to auto-generate)",
            width=520,
            height=40,
            font=FONT_MONO,
        )
        self._key_entry.pack(side="left", padx=(0, 8))

        self._generate_btn = ctk.CTkButton(
            key_row,
            text="Generate Key",
            width=112,
            height=40,
            font=FONT_SMALL,
            command=self._generate_key,
        )
        self._generate_btn.pack(side="left")

        # TTL row
        ttl_row = ctk.CTkFrame(parent, fg_color="transparent")
        ttl_row.pack(fill="x", padx=16, pady=(10, 0))
        ctk.CTkLabel(ttl_row, text="TTL (Seconds)", font=FONT_LABEL, anchor="w").pack(side="left")
        self._ttl_entry = ctk.CTkEntry(
            ttl_row,
            placeholder_text="e.g. 60 (leave blank for no expiry)",
            width=280,
            height=30,
            font=FONT_SMALL,
        )
        self._ttl_entry.pack(side="right")

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

    def _build_steg_tab(self, parent):
        pad = {"padx": 16, "pady": 8}
        
        # Helper for file selection
        def select_file(entry_widget, mode="open", filetypes=None):
            from tkinter import filedialog
            if filetypes is None:
                filetypes = [("All Files", "*.*")]
            
            if mode == "open":
                path = filedialog.askopenfilename(filetypes=filetypes)
            else:
                path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)
                
            if path:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, path)

        # Carrier Image
        ctk.CTkLabel(parent, text="Carrier Image (PNG)", font=FONT_LABEL, anchor="w").pack(fill="x", **pad)
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 6))
        self._steg_carrier_entry = ctk.CTkEntry(row1, placeholder_text="Select a cover PNG image...", width=480, height=36, font=FONT_SMALL)
        self._steg_carrier_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(row1, text="Browse", width=120, height=36, command=lambda: select_file(self._steg_carrier_entry, filetypes=[("PNG Images", "*.png")])).pack(side="left")

        # Payload File
        ctk.CTkLabel(parent, text="Payload File (To embed)", font=FONT_LABEL, anchor="w").pack(fill="x", **pad)
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 6))
        self._steg_payload_entry = ctk.CTkEntry(row2, placeholder_text="Select file to hide (e.g. secret.txt.enc)", width=480, height=36, font=FONT_SMALL)
        self._steg_payload_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(row2, text="Browse", width=120, height=36, command=lambda: select_file(self._steg_payload_entry)).pack(side="left")

        # Output File
        ctk.CTkLabel(parent, text="Output File", font=FONT_LABEL, anchor="w").pack(fill="x", **pad)
        row3 = ctk.CTkFrame(parent, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(0, 6))
        self._steg_output_entry = ctk.CTkEntry(row3, placeholder_text="Output path (PNG or recovered payload)", width=480, height=36, font=FONT_SMALL)
        self._steg_output_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(row3, text="Browse Save", width=120, height=36, command=lambda: select_file(self._steg_output_entry, mode="save", filetypes=[("PNG Images", "*.png"), ("All Files", "*.*")])).pack(side="left")

        # Action Buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=24)
        
        ctk.CTkButton(
            btn_frame, text="🖼️  Embed Payload", width=300, height=BTN_HEIGHT, font=FONT_LABEL, command=self._do_steg_embed
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkButton(
            btn_frame, text="🔍  Extract Payload", width=300, height=BTN_HEIGHT, font=FONT_LABEL,
            fg_color="#2d6a4f", hover_color="#1b4332", command=self._do_steg_extract
        ).pack(side="left")

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
            "HexCrypt is a desktop encryption tool powered by the AES-256-GCM\n"
            "symmetric authenticated encryption scheme.\n\n"
            "How to use:\n"
            "  • Encrypt — type your text, optionally paste or generate a key,\n"
            "    then click Encrypt. The key is required to decrypt later.\n\n"
            "  • Decrypt — paste the encrypted token into Input Text,\n"
            "    paste the original key into the Key field, then click Decrypt.\n\n"
            "  • Generate Key — creates a fresh random AES-256-GCM key and fills\n"
            "    the Key field automatically.\n\n"
            "  • Passphrase Mode — toggle 'Use Passphrase' to derive a key securely\n"
            "    from a password using Argon2id.\n\n"
            "  • TTL Expiry — enter a time in seconds in the TTL field during\n"
            "    decryption to enforce token self-destruction.\n\n"
            "  • Logs — every operation is recorded with a timestamp.\n\n"
            "⚠  Keep your key safe. Without it, encrypted data cannot be recovered."
        )
        ctk.CTkLabel(
            parent, text=info, font=FONT_SMALL, justify="left", wraplength=600
        ).pack(**pad)

    # ── Actions ──────────────────────────────
    def _on_mode_change(self, value):
        if value == "Symmetric":
            self._key_label.configure(text="Key or Passphrase")
            self._passphrase_switch.configure(state="normal")
            self._key_entry.configure(placeholder_text="Paste key here (leave blank to auto-generate)")
            self._generate_btn.configure(text="Generate Key")
        else:
            self._passphrase_var.set(False)
            self._toggle_passphrase()
            self._passphrase_switch.configure(state="disabled")
            self._key_label.configure(text="Recipient PubKey (Encrypt) / Your PrivKey (Decrypt)")
            self._key_entry.configure(placeholder_text="Paste X25519 key here")
            self._generate_btn.configure(text="Gen Keypair")

    def _generate_key(self):
        if self._mode_var.get() == "Symmetric":
            key = core.generate_key()
            self._key_entry.delete(0, "end")
            self._key_entry.insert(0, key)
            self._set_status("New key generated and placed in the Key field.")
        else:
            priv, pub = core.generate_x25519_keypair()
            top = ctk.CTkToplevel(self)
            top.title("X25519 Keypair")
            top.geometry("600x300")
            top.transient(self)
            top.grab_set()
            
            ctk.CTkLabel(top, text="Private Key (Keep Secret):", font=FONT_LABEL).pack(pady=(10, 0), padx=10, anchor="w")
            priv_entry = ctk.CTkEntry(top, font=FONT_MONO)
            priv_entry.pack(fill="x", padx=10, pady=2)
            priv_entry.insert(0, priv)
            priv_entry.configure(state="readonly")
            
            ctk.CTkLabel(top, text="Public Key (Share with Sender):", font=FONT_LABEL).pack(pady=(10, 0), padx=10, anchor="w")
            pub_entry = ctk.CTkEntry(top, font=FONT_MONO)
            pub_entry.pack(fill="x", padx=10, pady=2)
            pub_entry.insert(0, pub)
            pub_entry.configure(state="readonly")
            
            ctk.CTkButton(top, text="Close", command=top.destroy).pack(pady=20)
            self._set_status("Generated new X25519 keypair.")

    def _toggle_passphrase(self):
        if self._passphrase_var.get():
            self._key_entry.configure(placeholder_text="Enter passphrase here", show="*")
            self._generate_btn.configure(state="disabled")
        else:
            self._key_entry.configure(placeholder_text="Paste key here (leave blank to auto-generate)", show="")
            self._generate_btn.configure(state="normal")

    def _do_encrypt(self):
        input_text = self._input_entry.get().strip()
        key_text   = self._key_entry.get().strip()
        is_passphrase = self._passphrase_var.get()

        if not input_text:
            messagebox.showwarning("Missing Input", "Please enter text to encrypt.")
            return

        if self._mode_var.get() == "Asymmetric":
            if not key_text:
                messagebox.showwarning("Missing Key", "Please enter the Recipient's Public Key.")
                return
            try:
                result = core.encrypt_asymmetric(input_text.encode('utf-8'), key_text)
            except Exception as e:
                messagebox.showerror("Encryption Error", f"Asymmetric encrypt failed:\n{e}")
                return
        else:
            if is_passphrase:
                if not key_text:
                    messagebox.showwarning("Missing Passphrase", "Please enter a passphrase.")
                    return
                try:
                    result = core.encrypt_with_passphrase(input_text, key_text)
                except Exception as e:
                    messagebox.showerror("Encryption Error", str(e))
                    return
            else:
                # Auto-generate key if blank
                if not key_text:
                    key_text = core.generate_key()
                    self._key_entry.delete(0, "end")
                    self._key_entry.insert(0, key_text)
                try:
                    result = core.encrypt_text(input_text, key_text)
                except Exception as e:
                    messagebox.showerror("Encryption Error", str(e))
                    return

        self._current_output = result
        self._current_key    = "***PASSPHRASE***" if is_passphrase else key_text
        self._set_output(result)
        self._set_key_display(self._current_key)
        _append_log(f"Encrypt ({self._mode_var.get()})", input_text, self._current_key, result)
        self._set_status(f"Encrypted successfully at {datetime.now().strftime('%H:%M:%S')}.")

    def _do_decrypt(self):
        input_text = self._input_entry.get().strip()
        key_text   = self._key_entry.get().strip()
        ttl_text   = self._ttl_entry.get().strip()
        is_passphrase = self._passphrase_var.get()

        if not input_text:
            messagebox.showwarning("Missing Input", "Please enter the encrypted token.")
            return
        if not key_text:
            messagebox.showwarning("Missing Key", "A key or passphrase is required for decryption.")
            return

        ttl = None
        if ttl_text:
            try:
                ttl = int(ttl_text)
            except ValueError:
                messagebox.showwarning("Invalid TTL", "TTL must be a valid integer number of seconds.")
                return

        try:
            if self._mode_var.get() == "Asymmetric":
                result_bytes = core.decrypt_asymmetric(input_text, key_text, ttl=ttl)
                result = result_bytes.decode('utf-8')
            else:
                if is_passphrase:
                    result = core.decrypt_with_passphrase(input_text, key_text, ttl=ttl)
                else:
                    result = core.decrypt_text(input_text, key_text, ttl=ttl)
        except core.ExpiredToken:
            messagebox.showerror("Decryption Error", "Token Expired: This message self-destructed.")
            return
        except InvalidTag:
            messagebox.showerror("Decryption Error", "Authentication failed: Invalid key or corrupted data.")
            return
        except ValueError:
            messagebox.showerror("Decryption Error", "Invalid base64 token or key format.")
            return
        except Exception as e:
            messagebox.showerror("Decryption Error", f"Could not decrypt.\n\n{e}")
            return

        self._current_output = result
        self._current_key    = "***PASSPHRASE***" if is_passphrase else key_text
        self._set_output(result)
        self._set_key_display(self._current_key)
        _append_log(f"Decrypt ({self._mode_var.get()})", input_text, self._current_key, result)
        self._set_status(f"Decrypted successfully at {datetime.now().strftime('%H:%M:%S')}.")

    def _clear_fields(self):
        self._input_entry.delete(0, "end")
        self._key_entry.delete(0, "end")
        self._ttl_entry.delete(0, "end")
        self._set_output("")
        self._set_key_display("")
        self._current_output = ""
        self._current_key    = ""
        self._passphrase_var.set(False)
        self._toggle_passphrase()
        
        # Steg tab clear
        if hasattr(self, '_steg_carrier_entry'):
            self._steg_carrier_entry.delete(0, "end")
            self._steg_payload_entry.delete(0, "end")
            self._steg_output_entry.delete(0, "end")
            
        self._set_status("Fields cleared.")

    def _do_steg_embed(self):
        carrier = self._steg_carrier_entry.get().strip()
        payload = self._steg_payload_entry.get().strip()
        output  = self._steg_output_entry.get().strip()
        
        if not carrier or not payload or not output:
            messagebox.showwarning("Missing Fields", "Please select Carrier, Payload, and Output files for embedding.")
            return
            
        try:
            from hexcrypt import steg
        except ImportError:
            messagebox.showerror("Dependency Error", "Pillow library is required for steganography. Please run: pip install Pillow")
            return
            
        try:
            steg.embed_data(carrier, payload, output)
            self._set_status("Payload embedded successfully!")
            messagebox.showinfo("Success", f"Embedded payload into {output}")
        except Exception as e:
            messagebox.showerror("Steganography Error", f"Failed to embed:\n{e}")

    def _do_steg_extract(self):
        carrier = self._steg_carrier_entry.get().strip()
        output  = self._steg_output_entry.get().strip()
        
        if not carrier or not output:
            messagebox.showwarning("Missing Fields", "Please select Carrier and Output files for extraction.")
            return
            
        try:
            from hexcrypt import steg
        except ImportError:
            messagebox.showerror("Dependency Error", "Pillow library is required for steganography. Please run: pip install Pillow")
            return
            
        try:
            steg.extract_data(carrier, output)
            self._set_status("Payload extracted successfully!")
            messagebox.showinfo("Success", f"Extracted payload to {output}")
        except Exception as e:
            messagebox.showerror("Steganography Error", f"Failed to extract:\n{e}")

    def _copy_output(self):
        if self._current_output:
            self.clipboard_clear()
            self.clipboard_append(self._current_output)
            self._set_status("Output copied to clipboard.")
        else:
            self._set_status("Nothing to copy.")

    def _copy_key(self):
        if self._current_key:
            self.clipboard_clear()
            self.clipboard_append(self._current_key)
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

        if not rows or len(rows) <= 1:
            ctk.CTkLabel(self._log_frame, text="Log is empty.", font=FONT_SMALL).grid(
                row=0, column=0, padx=8, pady=8
            )
            return

        display_rows = [rows[0]] + list(reversed(rows[1:]))

        col_widths = [140, 80, 160, 200, 200]
        for i, row in enumerate(display_rows):
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

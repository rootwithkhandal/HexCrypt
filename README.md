# HexCrypt

A desktop encryption/decryption tool built with Python and customtkinter, powered by the **AES-256-GCM** authenticated symmetric encryption scheme.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-2.0.0-orange)

---

## Features

- 🔒 **Encrypt** any text using a secure 256-bit key
- 🔓 **Decrypt** tokens back to plaintext
- 🔑 **Generate Key** — create a fresh random key with one click
- 🔐 **Passphrase Mode** — derive a key securely from a password using Argon2id
- ⏱️ **Token Expiry (TTL)** — enforce message self-destruction after a specified time
- 📋 **Operation Logs** — every encrypt/decrypt is timestamped and stored in `log.csv`
- 🗑 **Clear Logs** — wipe the log history from within the app
- 🌗 **Dark / Light theme** toggle
- 📎 **Copy Output / Copy Key** buttons — copy raw values directly to clipboard
- ✖ **Clear** button to reset all fields at once
- ℹ️ **About tab** with usage instructions built in

---

## Screenshots

> _Run the app and explore the three tabs: Encrypt/Decrypt, Logs, and About._

---

## Installation

**Step 1 — Clone the repo**
```bash
git clone https://github.com/rootwithkhandal/hexcrypt.git
cd HexCrypt
```

**Step 2 — (Optional) Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux
```

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — Run the app**
```bash
python -m hexcrypt.app
```

---

## Usage

### Encrypt
1. Type your plaintext into **Input Text**.
2. Either paste an existing key into the **Key** field, click **Generate Key**, or toggle **Use Passphrase** and enter a password.
3. Click **🔒 Encrypt**.
4. Copy the output token. If using a raw key, copy it too — you need both to decrypt later.

### Decrypt
1. Paste the encrypted token into **Input Text**.
2. Paste the original key into the **Key** field, or toggle **Use Passphrase** and enter your password.
3. (Optional) Enter a maximum age in the **TTL (Seconds)** field to enforce token self-destruction.
4. Click **🔓 Decrypt**.

### Logs
Switch to the **📋 Logs** tab to view a timestamped history of all operations. Use **Refresh** to reload and **Clear Logs** to wipe the history.

### Keystore (CLI)
HexCrypt now includes a command-line interface (`cli.py`) for managing an encrypted JSON vault of named keys, secured by a master password. This replaces the need to store plaintext `.key` files on disk.

```bash
# Initialize the keystore
python -m hexcrypt.cli keystore init

# Add a key (auto-generates if value not provided)
python -m hexcrypt.cli keystore add my_secret_key

# List all named keys
python -m hexcrypt.cli keystore list

# Retrieve a key
python -m hexcrypt.cli keystore get my_secret_key
```

> ⚠️ **Keep your key safe.** AES-GCM encryption is symmetric — without the original key, encrypted data cannot be recovered.

---

## Project Structure

```
HexCrypt/
├── hexcrypt/         # Core application package
│   ├── app.py        # GUI application logic
│   ├── cli.py        # CLI application logic
│   ├── core.py       # Encryption/decryption engine
│   └── keystore.py   # Keystore manager
├── log.csv           # Auto-generated operation log (git-ignored)
├── requirements.txt  # Python dependencies
└── README.md
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `customtkinter >= 5.2.0` | Modern themed tkinter widgets |
| `cryptography >= 42.0.0` | AES-GCM encryption primitive |

---

## Changelog

### v2.0.0
- Refactored app into a proper `HexCryptApp` class
- Added tabbed UI (Encrypt/Decrypt, Logs, About)
- Added Generate Key, Clear, and improved Copy buttons
- Added Dark/Light theme toggle
- Added status bar with operation timestamps
- Fixed `core.py` — removed CLI code that ran on import
- Log viewer moved into a tab with Refresh and Clear Logs
- Log format now includes a Timestamp column

### v1.0.0
- Initial release with basic encrypt/decrypt UI
- CSV logging

---

## License

MIT — feel free to use, modify, and distribute.

import argparse
import os
import getpass
import sys
import argcomplete
from hexcrypt_core import keystore
from hexcrypt_core import core

def main():
    parser = argparse.ArgumentParser(description="HexCrypt CLI")
    subparsers = parser.add_subparsers(dest="command")

    # keystore commands
    ks_parser = subparsers.add_parser("keystore", help="Manage encrypted keystore")
    ks_sub = ks_parser.add_subparsers(dest="ks_command")

    # init
    ks_sub.add_parser("init", help="Initialize an empty keystore")
    
    # add
    add_parser = ks_sub.add_parser("add", help="Add a new key")
    add_parser.add_argument("name", help="Name of the key")
    add_parser.add_argument("key", nargs="?", help="Base64 AES-GCM key (leave blank to auto-generate)")

    # gen-keypair
    gk_parser = ks_sub.add_parser("gen-keypair", help="Generate an X25519 keypair")
    gk_parser.add_argument("name", help="Base name for the keypair (e.g. 'alice' -> 'alice_priv', 'alice_pub')")

    # get
    get_parser = ks_sub.add_parser("get", help="Get a key by name")
    get_parser.add_argument("name", help="Name of the key")

    # list
    ks_sub.add_parser("list", help="List all key names")

    # remove
    rm_parser = ks_sub.add_parser("remove", help="Remove a key by name")
    rm_parser.add_argument("name", help="Name of the key")

    # encrypt
    enc_parser = subparsers.add_parser("encrypt", help="Encrypt a file or directory")
    enc_parser.add_argument("--mode", choices=["symmetric", "asymmetric"], default="symmetric", help="Encryption mode")
    enc_parser.add_argument("--dir", help="Directory to encrypt")
    enc_parser.add_argument("--file", help="Single file to encrypt")
    enc_parser.add_argument("--key", help="Raw base64 key (symmetric)")
    enc_parser.add_argument("--key-name", help="Key name from keystore (symmetric)")
    enc_parser.add_argument("--recipient-pub", help="Recipient public key base64 (asymmetric)")
    enc_parser.add_argument("--recipient-key-name", help="Recipient public key name from keystore (asymmetric)")

    # decrypt
    dec_parser = subparsers.add_parser("decrypt", help="Decrypt a file or directory")
    dec_parser.add_argument("--mode", choices=["symmetric", "asymmetric"], default="symmetric", help="Decryption mode")
    dec_parser.add_argument("--dir", help="Directory to decrypt")
    dec_parser.add_argument("--file", help="Single file to decrypt")
    dec_parser.add_argument("--key", help="Raw base64 key (symmetric)")
    dec_parser.add_argument("--key-name", help="Key name from keystore (symmetric)")
    dec_parser.add_argument("--priv", help="Your private key base64 (asymmetric)")
    dec_parser.add_argument("--priv-key-name", help="Your private key name from keystore (asymmetric)")

    # steg
    steg_parser = subparsers.add_parser("steg", help="Hide files inside images using LSB steganography")
    steg_parser.add_argument("--embed", help="File to embed into the carrier image")
    steg_parser.add_argument("--extract", action="store_true", help="Extract file from the carrier image")
    steg_parser.add_argument("--carrier", required=True, help="Carrier image path (PNG)")
    steg_parser.add_argument("--out", required=True, help="Output path (PNG if embedding, file if extracting)")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.command == "keystore":
        if not args.ks_command:
            ks_parser.print_help()
            sys.exit(1)
        
        password = getpass.getpass("Master Password: ")

        try:
            vault = keystore.load_vault(password)
        except Exception:
            print("Authentication failed or corrupted vault.")
            sys.exit(1)

        if args.ks_command == "init":
            keystore.save_vault(password, vault)
            print("Keystore initialized/verified.")
        
        elif args.ks_command == "add":
            key_value = args.key
            if not key_value:
                key_value = core.generate_key()
                print(f"Generated new key for '{args.name}'")
            vault[args.name] = key_value
            keystore.save_vault(password, vault)
            print(f"Key '{args.name}' saved securely.")
            
        elif args.ks_command == "gen-keypair":
            priv, pub = core.generate_x25519_keypair()
            vault[f"{args.name}_priv"] = priv
            vault[f"{args.name}_pub"] = pub
            keystore.save_vault(password, vault)
            print(f"Keypair '{args.name}' generated. Saved '{args.name}_priv' and '{args.name}_pub'.")
            
        elif args.ks_command == "get":
            if args.name in vault:
                print(f"{args.name}: {vault[args.name]}")
            else:
                print(f"Key '{args.name}' not found in vault.")
                
        elif args.ks_command == "list":
            if not vault:
                print("Vault is empty.")
            else:
                print("Keys in vault:")
                for k in vault.keys():
                    print(f" - {k}")
                    
        elif args.ks_command == "remove":
            if args.name in vault:
                del vault[args.name]
                keystore.save_vault(password, vault)
                print(f"Key '{args.name}' removed.")
            else:
                print(f"Key '{args.name}' not found in vault.")
                
    elif args.command in ("encrypt", "decrypt"):
        if not args.dir and not args.file:
            print("Must specify either --dir or --file")
            sys.exit(1)
            
        is_encrypt = (args.command == "encrypt")
        
        # Get Key or Passphrase
        key_value = None
        passphrase = None
        
        if args.mode == "symmetric":
            if args.key:
                key_value = args.key
            elif args.key_name:
                master_password = getpass.getpass("Keystore Master Password: ")
                try:
                    vault = keystore.load_vault(master_password)
                    key_value = vault[args.key_name]
                except Exception:
                    print("Failed to load keystore or key not found.")
                    sys.exit(1)
            else:
                passphrase = getpass.getpass("Encryption Passphrase: ")
        else:
            if is_encrypt:
                if args.recipient_pub:
                    key_value = args.recipient_pub
                elif args.recipient_key_name:
                    master_password = getpass.getpass("Keystore Master Password: ")
                    try:
                        vault = keystore.load_vault(master_password)
                        key_value = vault[args.recipient_key_name]
                    except Exception:
                        print("Failed to load keystore or recipient key not found.")
                        sys.exit(1)
                else:
                    print("Must specify --recipient-pub or --recipient-key-name for asymmetric encryption.")
                    sys.exit(1)
            else:
                if args.priv:
                    key_value = args.priv
                elif args.priv_key_name:
                    master_password = getpass.getpass("Keystore Master Password: ")
                    try:
                        vault = keystore.load_vault(master_password)
                        key_value = vault[args.priv_key_name]
                    except Exception:
                        print("Failed to load keystore or private key not found.")
                        sys.exit(1)
                else:
                    print("Must specify --priv or --priv-key-name for asymmetric decryption.")
                    sys.exit(1)
            
        def process_file(in_path, out_path):
            try:
                if args.mode == "asymmetric":
                    if is_encrypt:
                        core.encrypt_file_asymmetric(in_path, out_path, key_value)
                    else:
                        core.decrypt_file_asymmetric(in_path, out_path, key_value)
                else:
                    if is_encrypt:
                        if key_value:
                            core.encrypt_file(in_path, out_path, key_value)
                        else:
                            core.encrypt_file_with_passphrase(in_path, out_path, passphrase)
                    else:
                        if key_value:
                            core.decrypt_file(in_path, out_path, key_value)
                        else:
                            core.decrypt_file_with_passphrase(in_path, out_path, passphrase)
                print(f"{'Encrypted' if is_encrypt else 'Decrypted'}: {in_path} -> {out_path}")
            except Exception as e:
                print(f"Error processing {in_path}: {e}")
                
        if args.file:
            out_file = args.file + (".enc" if is_encrypt else ".dec")
            process_file(args.file, out_file)
            
        if args.dir:
            in_dir = os.path.normpath(args.dir)
            out_dir = in_dir + (".enc" if is_encrypt else ".dec")
            
            if not os.path.exists(in_dir):
                print(f"Directory not found: {in_dir}")
                sys.exit(1)
                
            for root, dirs, files in os.walk(in_dir):
                rel_path = os.path.relpath(root, in_dir)
                target_dir = os.path.join(out_dir, rel_path) if rel_path != "." else out_dir
                
                os.makedirs(target_dir, exist_ok=True)
                
                for f in files:
                    in_file = os.path.join(root, f)
                    out_file = os.path.join(target_dir, f)
                    process_file(in_file, out_file)
            
            print(f"Directory processing complete. Output saved to: {out_dir}")
    elif args.command == "steg":
        try:
            from hexcrypt_core import steg
        except ImportError:
            print("Pillow library is required for steganography. Please run: pip install Pillow")
            sys.exit(1)
            
        if args.embed:
            if args.extract:
                print("Cannot specify both --embed and --extract")
                sys.exit(1)
            try:
                with open(args.carrier, 'rb') as c_file, open(args.embed, 'rb') as p_file:
                    out_bytes = steg.embed_data(c_file.read(), p_file.read(), os.path.basename(args.embed))
                with open(args.out, 'wb') as o_file:
                    o_file.write(out_bytes)
                print(f"Successfully embedded '{args.embed}' into '{args.carrier}', saved to '{args.out}'.")
            except Exception as e:
                print(f"Embedding failed: {e}")
                sys.exit(1)
        elif args.extract:
            try:
                with open(args.carrier, 'rb') as c_file:
                    filename, p_bytes = steg.extract_data(c_file.read())
                with open(args.out, 'wb') as o_file:
                    o_file.write(p_bytes)
                print(f"Successfully extracted payload (original name: {filename}) from '{args.carrier}', saved to '{args.out}'.")
            except Exception as e:
                print(f"Extraction failed: {e}")
                sys.exit(1)
        else:
            print("Must specify either --embed or --extract")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

import argparse
import os
import getpass
import sys
from hexcrypt import keystore
from hexcrypt import core

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
    enc_parser.add_argument("--dir", help="Directory to encrypt")
    enc_parser.add_argument("--file", help="Single file to encrypt")
    enc_parser.add_argument("--key", help="Raw base64 key")
    enc_parser.add_argument("--key-name", help="Key name from keystore")

    # decrypt
    dec_parser = subparsers.add_parser("decrypt", help="Decrypt a file or directory")
    dec_parser.add_argument("--dir", help="Directory to decrypt")
    dec_parser.add_argument("--file", help="Single file to decrypt")
    dec_parser.add_argument("--key", help="Raw base64 key")
    dec_parser.add_argument("--key-name", help="Key name from keystore")

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
            
        def process_file(in_path, out_path):
            try:
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

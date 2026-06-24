import argparse
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

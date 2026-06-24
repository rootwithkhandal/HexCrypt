import os
import shutil
import re

def patch_imports(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace from hexcrypt import core/steg/keystore
    content = re.sub(r'from hexcrypt import (core|steg|keystore)', r'from hexcrypt_core import \1', content)
    # Replace import hexcrypt.core
    content = re.sub(r'import hexcrypt\.(core|steg|keystore)', r'import hexcrypt_core.\1', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("Starting migration...")
    os.makedirs("core/hexcrypt_core", exist_ok=True)
    os.makedirs("tool/hexcrypt", exist_ok=True)

    # 1. Move core logic
    files_to_core = ["core.py", "steg.py", "keystore.py"]
    for f in files_to_core:
        src = f"hexcrypt/{f}"
        if os.path.exists(src):
            shutil.move(src, f"core/hexcrypt_core/{f}")

    # 2. Move GUI/CLI
    files_to_tool = ["app.py", "cli.py"]
    for f in files_to_tool:
        src = f"hexcrypt/{f}"
        if os.path.exists(src):
            shutil.move(src, f"tool/hexcrypt/{f}")

    with open("core/hexcrypt_core/__init__.py", "w") as f: pass
    with open("tool/hexcrypt/__init__.py", "w") as f: pass

    if os.path.exists("hexcrypt") and not os.listdir("hexcrypt"):
        os.rmdir("hexcrypt")

    # 3. Move Tests
    os.makedirs("core/tests", exist_ok=True)
    for f in ["test_core.py", "test_steg.py"]:
        src = f"tests/{f}"
        if os.path.exists(src):
            shutil.move(src, f"core/tests/{f}")
            
    if os.path.exists("tests") and not os.listdir("tests"):
        os.rmdir("tests")

    # 4. Move tool pyproject
    if os.path.exists("pyproject.toml"):
        shutil.move("pyproject.toml", "tool/pyproject.toml")
    if os.path.exists("requirements.txt"):
        shutil.move("requirements.txt", "tool/requirements.txt")
        
    # 5. Patch Imports in Tool & Tests
    patch_imports("tool/hexcrypt/app.py")
    patch_imports("tool/hexcrypt/cli.py")
    patch_imports("core/tests/test_core.py")
    patch_imports("core/tests/test_steg.py")
    
    # 6. Create core/pyproject.toml
    core_pyproject = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "hexcrypt-core"
version = "2.0.0"
authors = [
  { name="rootwithkhandal" },
]
description = "Core cryptography primitives for HexCrypt."
requires-python = ">=3.8"
dependencies = [
    "cryptography>=42.0.0",
    "Pillow>=10.0.0"
]

[tool.setuptools.packages.find]
include = ["hexcrypt_core*"]
"""
    with open("core/pyproject.toml", "w") as f:
        f.write(core_pyproject)
        
    # 7. Update tool/pyproject.toml to depend on hexcrypt-core
    if os.path.exists("tool/pyproject.toml"):
        with open("tool/pyproject.toml", "r") as f:
            content = f.read()
            
        content = content.replace('"Pillow>=10.0.0",', '') # core handles pillow now
        content = content.replace('"cryptography>=42.0.0",', '"hexcrypt-core",')
        
        with open("tool/pyproject.toml", "w") as f:
            f.write(content)

    print("Migration complete! You now have a monorepo with `core/` and `tool/`.")

if __name__ == "__main__":
    main()

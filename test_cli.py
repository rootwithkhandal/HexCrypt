import os
import subprocess

os.makedirs('test_dir', exist_ok=True)
with open('test_dir/hello.txt', 'w') as f:
    f.write('Hello World!')

# Encrypt
try:
    # use pexpect or similar? no, just use subprocess to pass passphrase
    proc = subprocess.Popen(
        ['python3', '-m', 'hexcrypt.cli', 'encrypt', '--dir', 'test_dir'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate('mypassword\n')
    print('Encrypt out:', out)
    print('Encrypt err:', err)

    proc2 = subprocess.Popen(
        ['python3', '-m', 'hexcrypt.cli', 'decrypt', '--dir', 'test_dir.enc'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out2, err2 = proc2.communicate('mypassword\n')
    print('Decrypt out:', out2)
    print('Decrypt err:', err2)
    
    with open('test_dir.enc.dec/hello.txt', 'r') as f:
        print('Recovered:', f.read())
except Exception as e:
    print('Error:', e)

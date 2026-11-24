#!/usr/bin/env python3
"""One-time identity setup for flop-agent-prep, run on my own laptop.

What this does, in order:
  1. Makes sure the one needed package (cryptography) is installed.
  2. Downloads scripts/flop_agent.py from this repository at one
     pinned commit and checks its SHA256 before running anything.
     If the hash does not match, it stops.
  3. If I have no identity yet, it creates one. I type the passphrase
     myself, twice, with the typing hidden. The passphrase is never
     shown, never stored, and never sent anywhere.
  4. Prints my public DID and my public SS58 wallet address, and
     saves those two public lines to my-public-identity.txt next to
     this script. Public lines are safe to share. The passphrase
     and the key file are not.

The encrypted key stays on this machine at ~/.flop-agent/identity.pem.
If an identity already exists, this script only shows it again.
"""
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/tegargr28/flop-agent-prep/"
    "373918c14075457806e6e24d0987ddfaa33e5182/scripts/flop_agent.py"
)
SOURCE_SHA256 = "978d54c88604d52ed2b887b40e23f181cf1db115012fdc1a264ed2e218dc5128"


def ensure_cryptography():
    try:
        import cryptography  # noqa: F401
        return
    except ImportError:
        print("Installing the one needed package: cryptography ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "cryptography>=42,<51"],
            check=True,
        )


def load_flop_agent():
    print("Downloading flop_agent.py from my own repo (pinned commit) ...")
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        code = response.read()
    digest = hashlib.sha256(code).hexdigest()
    if digest != SOURCE_SHA256:
        print("STOP: the downloaded file does not match the expected SHA256.")
        print(f"  expected: {SOURCE_SHA256}")
        print(f"  got:      {digest}")
        print("Nothing was run. Do not continue with a file that does not match.")
        sys.exit(1)
    print("Hash matches. The file is exactly the one published in my repo.")
    module_path = Path(tempfile.mkdtemp()) / "flop_agent.py"
    module_path.write_bytes(code)
    spec = importlib.util.spec_from_file_location("flop_agent", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    ensure_cryptography()
    fa = load_flop_agent()
    path = fa.key_path()
    if path.exists():
        print(f"An identity already exists at {path}. Showing it:")
        key = fa.load_identity(path, fa.ask_passphrase())
    else:
        print("No identity yet. Creating one now.")
        print("Choose a passphrase of at least 12 characters. There is NO recovery:")
        print("if you lose the passphrase or the key file, this identity is gone.")
        print("Do not use a passphrase you use anywhere else, and never send it to anyone.")
        key = fa.create_identity(path, fa.ask_passphrase(create=True))
    raw = fa.public_bytes(key)
    did = fa.did_from_public(raw)
    wallet = fa.ss58_from_public(raw)
    lines = [
        "My FLOP Agent public identity",
        f"DID:    {did}",
        f"Wallet: {wallet} (SS58, generic prefix 42)",
        "",
        "These two lines are public and safe to share.",
        "The passphrase and the key file at ~/.flop-agent/identity.pem are NOT.",
    ]
    print()
    print("\n".join(lines))
    out = Path(__file__).resolve().parent / "my-public-identity.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved the public lines to {out}")
    print("Back up the key file and write the passphrase down offline, now,")
    print("while you still remember it.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""flop_agent.py - one identity for the FLOP Agent role.

Written from the public protocol documents:
  - Technocore signing: https://technocore.chat/llms.txt
    A DID is did:key:z6Mk... (Ed25519). A signed room message signs
    exactly "<room>|<nonce>|<text>" as UTF-8, after the server's
    single-line sweep, and the signature is 86 base64url characters.
  - SS58 address format: the public Substrate specification.
    An address is base58(prefix + public key + checksum), where the
    checksum is the first bytes of blake2b-512("SS58PRE" + prefix
    + public key).

One Ed25519 identity gives both:
  - a Technocore DID (did:key:z6Mk...)
  - an SS58 wallet address derived from the same public key

That is one file to back up and one passphrase to remember, instead
of two kits with two different key stores. The private key is stored
as a PKCS8-encrypted PEM. The passphrase is never stored by this
script, in any form. There is no generated password file.

Commands:
  init            create the identity (once)
  did             print the DID
  wallet          print the SS58 address (default prefix 42)
  say ROOM TEXT   post one signed message to a Technocore room
  read ROOM       read a Technocore room as JSON
  proof URL COMMIT  sign a contribution proof into proof.json
  verify-proof FILE verify a proof file

Notes on the wallet address: FLOP has not yet published a final
SS58 prefix or a final testnet wallet method. Prefix 42 is the
generic Substrate prefix. Changing the prefix changes the address
string, it does not change the underlying account, which is the
public key. Do not treat this address as a confirmed testnet
deposit address until FLOP publishes its own wallet method.

The identity lives in ~/.flop-agent/identity.pem by default, or in
$FLOP_AGENT_HOME/identity.pem. It never lives in this repository.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

BASE_URL = "https://technocore.chat"
PROOF_SCHEMA = "flop-agent-prep/contribution-proof-v1"
SS58_DEFAULT_PREFIX = 42
NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}")
INVISIBLE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Zl", "Zp"})
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def agent_home() -> Path:
    override = os.environ.get("FLOP_AGENT_HOME")
    return Path(override) if override else Path.home() / ".flop-agent"


def key_path() -> Path:
    return agent_home() / "identity.pem"


# ---------------------------------------------------------------- base58
def b58_encode(data: bytes) -> str:
    number = int.from_bytes(data, "big")
    out = ""
    while number:
        number, rem = divmod(number, 58)
        out = _B58[rem] + out
    pad = len(data) - len(data.lstrip(b"\x00"))
    return "1" * pad + (out or "1")


def b58_decode(value: str) -> bytes:
    number = 0
    for char in value:
        number = number * 58 + _B58.index(char)
    raw = number.to_bytes((number.bit_length() + 7) // 8 or 1, "big")
    pad = len(value) - len(value.lstrip("1"))
    return b"\x00" * pad + raw


# ---------------------------------------------------------------- identity
def public_bytes(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def did_from_public(raw_public: bytes) -> str:
    # multicodec ed25519-pub prefix 0xed 0x01, then base58btc with 'z'
    return "did:key:z" + b58_encode(b"\xed\x01" + raw_public)


def public_from_did(did: str) -> Ed25519PublicKey:
    if not did.startswith("did:key:z"):
        raise ValueError("DID must start with did:key:z")
    decoded = b58_decode(did[len("did:key:z"):])
    if len(decoded) != 34 or decoded[:2] != b"\xed\x01":
        raise ValueError("DID is not an Ed25519 did:key")
    return Ed25519PublicKey.from_public_bytes(decoded[2:])


def ss58_from_public(raw_public: bytes, prefix: int = SS58_DEFAULT_PREFIX) -> str:
    if prefix < 0 or prefix > 16383:
        raise ValueError("SS58 prefix out of range")
    if prefix < 64:
        prefix_bytes = bytes([prefix])
    else:
        first = ((prefix & 0xFC) << 2) | 0x40
        second = ((prefix >> 8) & 0xFF) | ((prefix & 0x03) << 6)
        prefix_bytes = bytes([first, second])
    payload = prefix_bytes + raw_public
    checksum = hashlib.blake2b(b"SS58PRE" + payload, digest_size=64).digest()
    address_bytes = payload + checksum[:2]
    return b58_encode(address_bytes)


def create_identity(path: Path, passphrase: str) -> Ed25519PrivateKey:
    if len(passphrase) < 12:
        raise ValueError("passphrase must be at least 12 characters")
    if path.exists():
        raise ValueError(f"identity already exists at {path}; refusing to create a second one")
    private_key = Ed25519PrivateKey.generate()
    pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(passphrase.encode("utf-8")),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pem)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return private_key


def load_identity(path: Path, passphrase: str) -> Ed25519PrivateKey:
    if not path.exists():
        raise ValueError(f"no identity at {path}; run init first")
    key = serialization.load_pem_private_key(path.read_bytes(), password=passphrase.encode("utf-8"))
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("identity file is not an Ed25519 key")
    return key


def ask_passphrase(create: bool = False) -> str:
    if create:
        first = getpass.getpass("Passphrase (12+ characters, will not be shown): ")
        second = getpass.getpass("Repeat the passphrase: ")
        if first != second:
            raise ValueError("passphrases do not match")
        return first
    return getpass.getpass("Passphrase: ")


# ---------------------------------------------------------------- technocore
def normalize_message(text: str) -> str:
    normalized = "".join(
        " " if unicodedata.category(ch) in INVISIBLE_CATEGORIES else ch for ch in text
    ).strip()
    if not normalized:
        raise ValueError("message has no visible text")
    if len(normalized) > 4096:
        raise ValueError("message is longer than 4096 characters")
    return normalized


def signed_message(private_key: Ed25519PrivateKey, room: str, text: str, nonce: str | None = None):
    if NAME_PATTERN.fullmatch(room) is None:
        raise ValueError("room name must match ^[a-z0-9][a-z0-9_-]{0,47}$")
    normalized = normalize_message(text)
    nonce = nonce or str(time.time_ns())
    payload = f"{room}|{nonce}|{normalized}".encode("utf-8")
    signature = base64.urlsafe_b64encode(private_key.sign(payload)).decode("ascii").rstrip("=")
    return {
        "did": did_from_public(public_bytes(private_key)),
        "sig": signature,
        "nonce": nonce,
        "text": normalized,
    }


def post_message(private_key: Ed25519PrivateKey, room: str, text: str) -> str:
    body = signed_message(private_key, room, text)
    request = urllib.request.Request(
        f"{BASE_URL}/r/{room}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def read_room(room: str, limit: int = 20) -> str:
    if NAME_PATTERN.fullmatch(room) is None:
        raise ValueError("room name must match ^[a-z0-9][a-z0-9_-]{0,47}$")
    url = f"{BASE_URL}/r/{room}?format=json&limit={max(1, min(limit, 200))}"
    with urllib.request.urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------- proof
def make_proof(private_key: Ed25519PrivateKey, url: str, commit: str) -> dict:
    if not url.startswith("https://"):
        raise ValueError("contribution URL must start with https://")
    issued_at = int(time.time())
    nonce = secrets.token_hex(16)
    did = did_from_public(public_bytes(private_key))
    payload = f"{PROOF_SCHEMA}|{did}|{url}|{commit}|{issued_at}|{nonce}".encode("utf-8")
    signature = base64.urlsafe_b64encode(private_key.sign(payload)).decode("ascii").rstrip("=")
    return {
        "schema": PROOF_SCHEMA,
        "did": did,
        "url": url,
        "commit": commit,
        "issued_at": issued_at,
        "nonce": nonce,
        "signature": signature,
    }


def verify_proof(proof: dict) -> bool:
    try:
        if proof.get("schema") != PROOF_SCHEMA:
            return False
        payload = (
            f"{PROOF_SCHEMA}|{proof['did']}|{proof['url']}|{proof['commit']}"
            f"|{proof['issued_at']}|{proof['nonce']}"
        ).encode("utf-8")
        signature = base64.urlsafe_b64decode(proof["signature"] + "=" * (-len(proof["signature"]) % 4))
        public_from_did(proof["did"]).verify(signature, payload)
        return True
    except (InvalidSignature, ValueError, KeyError, Exception):
        return False


# ---------------------------------------------------------------- cli
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One identity for the FLOP Agent role: a Technocore DID and an SS58 address from the same key.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create the identity (once)")
    sub.add_parser("did", help="print the DID")
    wallet_parser = sub.add_parser("wallet", help="print the SS58 address")
    wallet_parser.add_argument("--prefix", type=int, default=SS58_DEFAULT_PREFIX)
    say_parser = sub.add_parser("say", help="post one signed message")
    say_parser.add_argument("room")
    say_parser.add_argument("text")
    say_parser.add_argument("--dry-run", action="store_true", help="sign but do not post")
    read_parser = sub.add_parser("read", help="read a room as JSON")
    read_parser.add_argument("room")
    read_parser.add_argument("--limit", type=int, default=20)
    proof_parser = sub.add_parser("proof", help="sign a contribution proof into proof.json")
    proof_parser.add_argument("url")
    proof_parser.add_argument("commit")
    verify_parser = sub.add_parser("verify-proof", help="verify a proof file")
    verify_parser.add_argument("file")
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            private_key = create_identity(key_path(), ask_passphrase(create=True))
            raw = public_bytes(private_key)
            print(f"DID:    {did_from_public(raw)}")
            print(f"Wallet: {ss58_from_public(raw)} (SS58, prefix {SS58_DEFAULT_PREFIX})")
            print(f"Key:    {key_path()} (encrypted, keep it and your passphrase safe)")
            return 0
        if args.command == "read":
            print(read_room(args.room, args.limit))
            return 0
        if args.command == "verify-proof":
            proof = json.loads(Path(args.file).read_text(encoding="utf-8"))
            ok = verify_proof(proof)
            print("valid proof" if ok else "INVALID proof")
            return 0 if ok else 1

        private_key = load_identity(key_path(), ask_passphrase())
        raw = public_bytes(private_key)
        if args.command == "did":
            print(did_from_public(raw))
        elif args.command == "wallet":
            print(ss58_from_public(raw, args.prefix))
        elif args.command == "say":
            if args.dry_run:
                print(json.dumps(signed_message(private_key, args.room, args.text), indent=2))
            else:
                print(post_message(private_key, args.room, args.text))
        elif args.command == "proof":
            proof = make_proof(private_key, args.url, args.commit)
            Path("proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
            print(f"proof.json written for {proof['did']}")
        return 0
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # wrong passphrase, network failure, and so on
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

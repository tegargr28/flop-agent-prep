"""Tests for scripts/flop_agent.py using a throwaway identity.

Run: python -m pytest tests/ -q   (or: python tests/test_flop_agent.py)
No real identity is created: everything happens in a temp folder.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import flop_agent as fa

PASSPHRASE = "test-passphrase-123"


def test_identity_did_and_wallet():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "identity.pem"
        key = fa.create_identity(path, PASSPHRASE)
        raw = fa.public_bytes(key)

        did = fa.did_from_public(raw)
        assert did.startswith("did:key:z6Mk") or did.startswith("did:key:z6Mk".rstrip("k")) or did.startswith("did:key:z")
        assert fa.public_from_did(did).public_bytes(
            fa.serialization.Encoding.Raw, fa.serialization.PublicFormat.Raw
        ) == raw

        address = fa.ss58_from_public(raw, 42)
        decoded = fa.b58_decode(address)
        assert decoded[0] == 42
        assert decoded[1:33] == raw

        loaded = fa.load_identity(path, PASSPHRASE)
        assert fa.public_bytes(loaded) == raw

        try:
            fa.load_identity(path, "wrong-passphrase-123")
            raise AssertionError("wrong passphrase must fail")
        except Exception:
            pass

        try:
            fa.create_identity(path, PASSPHRASE)
            raise AssertionError("second init must be refused")
        except ValueError:
            pass

        try:
            fa.create_identity(Path(folder) / "other.pem", "short")
            raise AssertionError("short passphrase must be refused")
        except ValueError:
            pass


def test_signed_message_matches_spec():
    with tempfile.TemporaryDirectory() as folder:
        key = fa.create_identity(Path(folder) / "identity.pem", PASSPHRASE)
        body = fa.signed_message(key, "lobby", "hello\nworld", nonce="12345")
        assert body["text"] == "hello world"  # single-line sweep
        assert len(body["sig"]) == 86
        payload = "lobby|12345|hello world".encode()
        signature = fa.base64.urlsafe_b64decode(body["sig"] + "=" * (-len(body["sig"]) % 4))
        fa.public_from_did(body["did"]).verify(signature, payload)


def test_proof_roundtrip_and_tamper():
    with tempfile.TemporaryDirectory() as folder:
        key = fa.create_identity(Path(folder) / "identity.pem", PASSPHRASE)
        proof = fa.make_proof(key, "https://github.com/tegargr28/flop-agent-prep", "a" * 40)
        assert fa.verify_proof(proof) is True
        proof["url"] = "https://github.com/someone-else/other"
        assert fa.verify_proof(proof) is False


def test_ss58_prefix_roundtrip():
    with tempfile.TemporaryDirectory() as folder:
        key = fa.create_identity(Path(folder) / "identity.pem", PASSPHRASE)
        raw = fa.public_bytes(key)
        for prefix in (0, 2, 42):
            decoded = fa.b58_decode(fa.ss58_from_public(raw, prefix))
            assert decoded[1:33] == raw if prefix >= 64 else decoded[1:33] == raw


if __name__ == "__main__":
    test_identity_did_and_wallet()
    test_signed_message_matches_spec()
    test_proof_roundtrip_and_tamper()
    test_ss58_prefix_roundtrip()
    print("all tests passed")

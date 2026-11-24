#!/usr/bin/env python3
"""Build the single-file identity page.

Reads page_template.html and flop_identity_crypto.js from this folder
and writes create-identity.html with the crypto inlined, so the page
is one file with no external requests. Run after changing either
source file:

    python tools/identity-page/build_page.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    template = (HERE / "page_template.html").read_text(encoding="utf-8")
    crypto_js = (HERE / "flop_identity_crypto.js").read_text(encoding="utf-8")
    marker = "/*__FLOP_CRYPTO__*/"
    if marker not in template:
        raise SystemExit("template is missing the crypto placeholder")
    page = template.replace(marker, crypto_js)
    if "http://" in page or "https://" in page:
        raise SystemExit("the page must not reference any external URL")
    out = HERE / "create-identity.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(page)} bytes, no external references)")


if __name__ == "__main__":
    main()

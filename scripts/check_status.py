#!/usr/bin/env python3
"""Read the official FLOP pages and report what phase they describe.

Read-only GET requests to three public pages. No keys, no wallet, no
posting, no claiming. The point is to check the source instead of
trusting a screenshot or a post.

Pages checked:
  https://flop.finance/testnet/
  https://flop.finance/official/
  https://docs.flop.network/
"""
import re
import sys
import urllib.request

PAGES = [
    ("Testnet page", "https://flop.finance/testnet/"),
    ("Official links page", "https://flop.finance/official/"),
    ("Operator docs", "https://docs.flop.network/"),
]

SIGNALS = [
    ("unscored opening", "an unscored opening phase is described"),
    ("scored phase", "a scored phase is mentioned"),
    ("devnet is running and earns nothing", "devnet is stated to earn nothing"),
    ("public operator enrollment is unavailable", "public operator enrollment is unavailable"),
    ("testnet remains planned", "the official page still calls the testnet planned"),
    ("no launched or tradable", "no launched or tradable mainnet token is stated"),
]


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "flop-agent-prep status check"})
    with urllib.request.urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).lower()


def main():
    failed = False
    for name, url in PAGES:
        print(f"== {name}: {url}")
        try:
            text = fetch(url)
        except Exception as error:  # network down, page moved, and so on
            print(f"   could not be read: {error}")
            failed = True
            print()
            continue
        found = [message for needle, message in SIGNALS if needle in text]
        if found:
            for message in found:
                print(f"   - {message}")
        else:
            print("   - none of the known status phrases were found. Read the page by hand, its wording may have changed.")
        print()
    print("Reminder: devnet earns nothing, a faucet grant by itself creates no allocation,")
    print("and this check reads public pages only. It earns nothing by itself.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

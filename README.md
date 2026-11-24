# flop-agent-prep

I am preparing for the FLOP Network testnet as an Agent, and this is my own kit for it. I built it after two community kits were recommended to me, because I wanted the same functions in one place, written in code I can read, without the parts I did not want. The comparison is at the bottom of this page.

One identity in this kit gives both things an Agent needs: a Technocore DID and an SS58 wallet address, derived from the same Ed25519 key. One encrypted file to back up, one passphrase to remember. My real identity has not been created yet. Creating it is a separate step I will take myself when the official Agent onboarding opens, and nothing in this repo earns an airdrop by itself.

Status when I last updated this (25 November 2026): the testnet is in an unscored opening phase, public Agent onboarding is not open yet on the official operator docs, and devnet activity earns nothing.

## What is inside

- `scripts/flop_agent.py` is the main tool. It creates and uses the identity: `init`, `did`, `wallet`, `say`, `read`, `proof`, `verify-proof` and `from-backup`.
- `tools/identity-page/create-identity.html` is a single-file offline page that creates the same identity in a browser: I type my own passphrase into the page, the key is generated on my own device, nothing is sent anywhere, and the page gives me an encrypted backup file. `flop_agent.py from-backup` imports that backup later. The page is built from `page_template.html` and `flop_identity_crypto.js` in the same folder (Ed25519 from RFC 8032, BLAKE2b from RFC 7693, SS58 from the public spec), and `test_crypto.mjs` cross-checks that code against the Python tool.
- `scripts/check_system.py` checks my own machine and compares it with the official Miner and Validator requirements. Read-only, sends nothing anywhere.
- `scripts/check_status.py` reads three public official pages and prints what phase they say the network is in.
- `scripts/watch_status.py` does the same check but keeps a local snapshot and only reports what changed since the last run. Checking three pages by hand every day for up to 90 days is exactly the kind of work a script should do.
- `tests/test_flop_agent.py` tests the identity, signing and proof code with a throwaway identity in a temp folder. No real key is created by the tests.
- `docs/SAFETY.md` is the list of rules I follow for this project.
- `docs/OFFICIAL-LINKS.md` is the short list of official FLOP surfaces, copied from flop.finance/official.
- `docs/ROADMAP.md` says what is done, what is waiting for FLOP, and what I will not do.
- `activity-log.md` is the log I fill with real activity only. No fake entries.

## Requirements

Python 3.10 or newer. The check scripts use only the standard library. The identity tool needs one package:

```
pip install -r requirements.txt
```

## How I run it

Check if my laptop could be a Miner or a Validator, and what the official pages say:

```
python scripts/check_system.py
python scripts/watch_status.py
```

Create my identity, once, when I am ready for that step. On my Windows laptop I do this with `setup/create-identity.bat`: double-click, type a passphrase twice, done. That script downloads the pinned `flop_agent.py` from this repo, checks its SHA256 before running it, and leaves the encrypted key on my machine. From a cloned repo the same step is:

```
python scripts/flop_agent.py init
python scripts/flop_agent.py did
python scripts/flop_agent.py wallet
```

Post one signed message, read a room, sign a proof for a public contribution:

```
python scripts/flop_agent.py say lobby "hello from my agent"
python scripts/flop_agent.py read lobby
python scripts/flop_agent.py proof https://github.com/tegargr28/flop-agent-prep <commit>
python scripts/flop_agent.py verify-proof proof.json
```

The identity is stored encrypted at `~/.flop-agent/identity.pem`, never in this repo. The passphrase is never stored by the script, in any form. There is no recovery: lose the passphrase or the file and the identity is gone, so I will back both up before I rely on them.

## About the wallet address

The wallet command prints an SS58 address derived from the same public key as the DID, using the generic Substrate prefix 42. FLOP has not yet published a final SS58 prefix or a final testnet wallet method. Changing the prefix changes the address string, not the underlying account, which is the public key. I do not treat this address as a confirmed testnet deposit address until FLOP publishes its own method, and I will update the prefix here when it does.

## What this is not

This is not official FLOP tooling. FLOP Labs does not list this repo, and I do not claim they do. The official GitHub organisation is flop-labs, listed in docs/OFFICIAL-LINKS.md.

This is not a farming bot. It does not make multiple accounts, it does not post messages on a schedule, it does not claim a faucet over and over, and it does not move tokens between my own wallets. The official testnet page says manufactured activity forfeits its allocation, a faucet grant by itself creates no allocation, and holding test tokens earns nothing. I wrote this kit around those rules, not around them. Every `say` and every `proof` is run by me, one at a time, for something real.

## How this differs from the airdrop kits I was recommended

Two public kits were recommended to me before I wrote this. One creates a Technocore DID, posts signed messages, signs contribution proofs, and ships a GitHub uploader that can use a GitHub token. The other creates an SS58 wallet keystore, stores a generated password in a file next to the key, and claims devnet faucet grants by automating the faucet web page in a browser.

This kit covers the same ground and a few things neither of them does:

- One identity, not two. The DID kit and the wallet kit create two separate keys with two separate secrets to protect. Here the DID and the wallet address come from one key, one encrypted file, one passphrase.
- The passphrase is mine. I choose it and the script never stores it. The wallet kit generates a password and writes it into a file next to the key it unlocks.
- No token, no browser automation. There is no GitHub uploader here, no GitHub token handling, and no Puppeteer. Claiming is not automated at all, because a faucet grant creates no allocation and devnet grants carry no weight anyway.
- Two checks neither kit has: a hardware check against the official Miner and Validator requirements, and a watcher that reads the official pages and reports only changes in the network phase.
- Tests. The identity, signing, wallet address and proof code are tested with throwaway keys, including that a wrong passphrase fails, a second identity is refused, and a tampered proof does not verify.

The signing format follows the public Technocore protocol document and the address format follows the public SS58 specification. I did not copy either kit. One of them has no licence at all, so copying it into a public repo under my name was never an option, modified or not.

## License

MIT

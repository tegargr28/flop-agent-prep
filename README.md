# flop-agent-prep

I am preparing for the FLOP Network testnet as an Agent. This repo is my preparation kit. It does not create a wallet, it does not create a DID yet, and it does not claim anything. I made it because most guides I found told me to install other people's scripts, and I wanted a smaller version that I can read myself before I run anything.

Status when I wrote this (25 November 2026): the testnet is in an unscored opening phase, public Agent onboarding is not open yet on the official operator docs, and devnet activity earns nothing. So this kit is only for getting ready. Nothing in here earns an airdrop by itself.

## What is inside

- `scripts/check_system.py` checks my own machine and compares it with the official Miner and Validator requirements. It only reads system information. It sends nothing anywhere.
- `scripts/check_status.py` reads three public official pages and prints what phase they say the network is in. It is a read-only check, so I do not have to rely on screenshots or posts from other people.
- `docs/SAFETY.md` is the list of rules I follow for this project.
- `docs/OFFICIAL-LINKS.md` is the short list of official FLOP surfaces, copied from flop.finance/official.
- `docs/ROADMAP.md` says what I will do, and what I will not do, when the scored phase opens.
- `activity-log.md` is an empty log I will fill by hand with real activity later. No fake entries.

## Requirements

Python 3.10 or newer. No packages to install, both scripts use only the standard library.

## How I run it

Check if my laptop could be a Miner or a Validator:

```
python scripts/check_system.py
```

Check what the official pages say right now:

```
python scripts/check_status.py
```

## What this is not

This is not official FLOP tooling. FLOP Labs does not list this repo, and I do not claim they do. The official GitHub organisation is flop-labs, listed in docs/OFFICIAL-LINKS.md.

This is not a farming bot. It does not make multiple accounts, it does not post messages on a schedule, it does not claim a faucet over and over, and it does not move tokens between my own wallets. The official testnet page says manufactured activity forfeits its allocation, a faucet grant by itself creates no allocation, and holding test tokens earns nothing. I wrote this kit around those rules, not around them.

No wallet and no DID is created here yet on purpose. An Agent needs a DID and a wallet, and the official way to create the testnet wallet is not published in final form yet. When it is, I will add that step, using official sources only, and I will set the passphrase myself.

## How this differs from the airdrop kits I was recommended

Two public kits were recommended to me before I wrote this. They do different jobs, and neither of them is this:

- The DID gameplay kit creates a Technocore identity. It generates an encrypted Ed25519 key, posts signed messages to technocore.chat, signs contribution proofs, and ships a GitHub uploader that can use a GitHub token. That is identity and posting, not a wallet.
- The airdrop kit creates a chain wallet. It generates an encrypted keystore with an SS58 address, stores a generated password in a file next to it, and claims devnet faucet grants by automating the faucet web page in a browser. Its own README says devnet grants carry no airdrop weight.

This kit creates neither a DID nor a wallet, and it holds no keys at all. There is nothing in here to leak, back up or lose. It does two read-only checks instead: whether my machine meets the official Miner or Validator requirements, and what the official FLOP pages say the network phase is right now. It has no dependencies, no browser automation, no token, no posting and no claiming.

When the official Agent onboarding opens, I will add the DID and wallet steps to this repo, from official flop-labs sources, in that order. Until then, kits that create keys are solving a step I am not at yet, on networks that do not count yet.

## License

MIT

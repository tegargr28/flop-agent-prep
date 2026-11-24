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

## Bahasa Indonesia

Repo ini adalah alat persiapan saya untuk ikut FLOP Network testnet sebagai Agent. Isinya bukan bot farming, bukan pembuat wallet, dan bukan alat klaim airdrop.

Ada dua skrip kecil, keduanya hanya memakai bawaan Python dan tidak perlu install tambahan. Skrip pertama memeriksa spek laptop saya lalu membandingkannya dengan syarat resmi Miner dan Validator. Skrip kedua membaca tiga halaman resmi FLOP dan menampilkan fase jaringan menurut halaman itu sendiri, jadi saya tidak perlu percaya tangkapan layar dari orang lain.

Waktu repo ini dibuat, testnet masih fase pembukaan yang belum dinilai, pendaftaran Agent publik belum dibuka di dokumen operator resmi, dan aktivitas devnet resmi dinyatakan tidak menghasilkan apa-apa. Jadi repo ini memang hanya persiapan. Langkah berikutnya, kalau fase yang dinilai sudah dibuka, saya tulis di docs/ROADMAP.md.

## License

MIT

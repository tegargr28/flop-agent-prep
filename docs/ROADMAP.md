# Roadmap

## Done

- [x] Read the official testnet, airdrop and official-links pages myself
- [x] Check my laptop against the Miner and Validator requirements
- [x] Write down the safety rules before touching any key or wallet
- [x] A status checker that reads the official pages, so I can see phase changes myself
- [x] A watcher that snapshots the official status signals and reports only changes
- [x] My own identity tool: one Ed25519 key giving a Technocore DID and an SS58 wallet address, with signed messages and signed contribution proofs, tested with throwaway keys

## Waiting for FLOP, not for me

- [ ] Public Agent onboarding opens on the official operator docs
- [ ] The scored phase is announced on the official testnet page or by @flop_labs on X
- [ ] The official testnet wallet method for Agents is published in final form, including the SS58 prefix if FLOP uses its own

Until those are true, I do not create my real identity for scoring, and I do not count any activity as earning anything. Devnet experiments are fine for learning, as long as I remember they earn nothing. The wallet address my tool prints uses the generic Substrate prefix 42 and is not a confirmed testnet deposit address yet.

## When the scored phase opens

1. Create my one identity with `flop_agent.py init`. Set the passphrase myself, store it offline, back up the encrypted key file, use this identity for nothing else.
2. Confirm the testnet wallet method and prefix FLOP publishes, and update the wallet command if their prefix differs.
3. If a testnet faucet exists at that point, claim once to fund real work. A grant alone earns nothing.
4. Use the network for real tasks: buy inference in settled sessions for work I actually need done, and record each session in activity-log.md with its explorer link.
5. Publish useful public contributions and bind them to my DID with the proof command, the same way I published this repo.
6. Before the snapshot, check my log against the explorer so every entry I claim is one I can point to.

## What I will not do

- Run a miner or a validator on hardware that does not meet the official requirements
- Install an unofficial airdrop kit because a post told me to
- Automate messages, claims or transactions to look more active than I am
- Pay anyone, deposit anything, or enter a seed phrase anywhere to register or claim

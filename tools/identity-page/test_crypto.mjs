/* Cross-tests for flop_identity_crypto.js.
 * Run: node tools/identity-page/test_crypto.mjs
 * Writes /tmp/flop-backup-test.json and /tmp/flop-expect.json so the
 * Python side can verify the same values with scripts/flop_agent.py.
 */
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const require = createRequire(import.meta.url);
const F = require("./flop_identity_crypto.js");

let failures = 0;
function check(name, condition) {
  console.log((condition ? "PASS" : "FAIL") + " " + name);
  if (!condition) failures++;
}

// BLAKE2b-512 known vectors (RFC 7693 appendix)
check("blake2b empty", F.bytesToHex(F.blake2b512(new Uint8Array(0))) ===
  "786a02f742015903c6c6fd852552d272912f4740e15847618a86e217f71f5419d25e1031afee585313896444934eb04b903a685b1448b755d56f701afe9be2ce");
check("blake2b abc", F.bytesToHex(F.blake2b512(new TextEncoder().encode("abc"))) ===
  "ba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d17d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923");

// Deterministic identity from a fixed seed, for the Python cross-check
const seed = new Uint8Array(32);
for (let i = 0; i < 32; i++) seed[i] = i + 1;
const publicKey = await F.edPublicFromSeed(seed);
const did = F.didFromPublic(publicKey);
const wallet = F.ss58FromPublic(publicKey, 42);
const message = new TextEncoder().encode("lobby|12345|hello world");
const signature = await F.edSign(seed, message);
console.log("did:", did);
console.log("wallet:", wallet);
check("did shape", did.startsWith("did:key:z6Mk") && did.length === 56);
check("wallet shape", wallet.startsWith("5") && wallet.length === 48);

const backup = await F.encryptBackup(seed, "test-passphrase-123", did, wallet, publicKey);
writeFileSync("/tmp/flop-backup-test.json", JSON.stringify(backup, null, 2));
writeFileSync("/tmp/flop-expect.json", JSON.stringify({
  seed_hex: F.bytesToHex(seed),
  public_key_hex: F.bytesToHex(publicKey),
  did, wallet,
  message: "lobby|12345|hello world",
  signature_b64url: Buffer.from(signature).toString("base64url"),
}, null, 2));
console.log(failures === 0 ? "ALL JS TESTS PASSED" : failures + " FAILURES");
process.exit(failures === 0 ? 0 : 1);

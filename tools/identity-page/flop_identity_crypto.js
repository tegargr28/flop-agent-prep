/* flop_identity_crypto.js
 *
 * The small amount of cryptography the offline identity page needs,
 * written from the public specifications so the page works with no
 * network, no libraries and no server:
 *   - Ed25519 key generation and signing, from RFC 8032
 *   - BLAKE2b-512, from RFC 7693 (needed for the SS58 checksum)
 *   - SS58 address encoding, from the public Substrate specification
 *   - did:key encoding (multicodec ed25519-pub + base58btc)
 *   - Backup encryption: PBKDF2-HMAC-SHA-256 + AES-256-GCM, via the
 *     WebCrypto API built into the browser (and into Node.js >= 19,
 *     which is how the tests in test_crypto.mjs run this same file).
 *
 * Nothing in this file makes a network request. The passphrase and
 * the private key never leave the page.
 */
"use strict";

/* ------------------------------------------------------------ helpers */
const MASK64 = (1n << 64n) - 1n;

function bytesToBigIntLE(bytes) {
  let value = 0n;
  for (let i = bytes.length - 1; i >= 0; i--) value = (value << 8n) | BigInt(bytes[i]);
  return value;
}
function bigIntToBytesLE(value, length) {
  const out = new Uint8Array(length);
  for (let i = 0; i < length; i++) { out[i] = Number(value & 0xffn); value >>= 8n; }
  return out;
}
function concatBytes(...parts) {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const p of parts) { out.set(p, offset); offset += p.length; }
  return out;
}
function bytesToHex(bytes) {
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}
function bytesToB64(bytes) {
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}
async function sha512(bytes) {
  return new Uint8Array(await crypto.subtle.digest("SHA-512", bytes));
}

/* ------------------------------------------------------------ base58 */
const B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function b58Encode(data) {
  let number = 0n;
  for (const b of data) number = (number << 8n) | BigInt(b);
  let out = "";
  while (number > 0n) { out = B58_ALPHABET[Number(number % 58n)] + out; number /= 58n; }
  let pad = 0;
  while (pad < data.length && data[pad] === 0) pad++;
  return "1".repeat(pad) + (out || "1");
}

/* ------------------------------------------------------------ blake2b (RFC 7693) */
const B2_IV = [
  0x6a09e667f3bcc908n, 0xbb67ae8584caa73bn, 0x3c6ef372fe94f82bn, 0xa54ff53a5f1d36f1n,
  0x510e527fade682d1n, 0x9b05688c2b3e6c1fn, 0x1f83d9abfb41bd6bn, 0x5be0cd19137e2179n,
];
const B2_SIGMA = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
  [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
  [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
  [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
  [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
  [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
  [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
  [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
  [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
  [10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0],
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
  [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
];
function rotr64(x, n) { return ((x >> BigInt(n)) | (x << BigInt(64 - n))) & MASK64; }

function blake2b512(input) {
  const h = [...B2_IV];
  h[0] ^= 0x01010000n ^ 64n; // unkeyed, digest length 64
  const blockCount = Math.max(1, Math.ceil(input.length / 128));
  let counter = 0n;
  for (let blockIndex = 0; blockIndex < blockCount; blockIndex++) {
    const start = blockIndex * 128;
    const block = new Uint8Array(128);
    block.set(input.subarray(start, Math.min(start + 128, input.length)));
    const m = [];
    for (let i = 0; i < 16; i++) m.push(bytesToBigIntLE(block.subarray(i * 8, i * 8 + 8)));
    const isLast = blockIndex === blockCount - 1;
    counter += BigInt(isLast ? input.length - start : 128);
    const v = [...h, ...B2_IV];
    v[12] ^= counter & MASK64;
    v[13] ^= (counter >> 64n) & MASK64;
    if (isLast) v[14] ^= MASK64;
    const G = (a, b, c, d, x, y) => {
      v[a] = (v[a] + v[b] + x) & MASK64; v[d] = rotr64(v[d] ^ v[a], 32);
      v[c] = (v[c] + v[d]) & MASK64; v[b] = rotr64(v[b] ^ v[c], 24);
      v[a] = (v[a] + v[b] + y) & MASK64; v[d] = rotr64(v[d] ^ v[a], 16);
      v[c] = (v[c] + v[d]) & MASK64; v[b] = rotr64(v[b] ^ v[c], 63);
    };
    for (let round = 0; round < 12; round++) {
      const s = B2_SIGMA[round];
      G(0, 4, 8, 12, m[s[0]], m[s[1]]); G(1, 5, 9, 13, m[s[2]], m[s[3]]);
      G(2, 6, 10, 14, m[s[4]], m[s[5]]); G(3, 7, 11, 15, m[s[6]], m[s[7]]);
      G(0, 5, 10, 15, m[s[8]], m[s[9]]); G(1, 6, 11, 12, m[s[10]], m[s[11]]);
      G(2, 7, 8, 13, m[s[12]], m[s[13]]); G(3, 4, 9, 14, m[s[14]], m[s[15]]);
    }
    for (let i = 0; i < 8; i++) h[i] ^= v[i] ^ v[i + 8];
  }
  const out = new Uint8Array(64);
  for (let i = 0; i < 8; i++) out.set(bigIntToBytesLE(h[i], 8), i * 8);
  return out;
}

/* ------------------------------------------------------------ ed25519 (RFC 8032) */
const ED_Q = (1n << 255n) - 19n;
const ED_L = (1n << 252n) + 27742317777372353535851937790883648493n;
function edMod(x) { return ((x % ED_Q) + ED_Q) % ED_Q; }
function edPow(base, exp) {
  let result = 1n; let b = edMod(base); let e = exp;
  while (e > 0n) { if (e & 1n) result = (result * b) % ED_Q; b = (b * b) % ED_Q; e >>= 1n; }
  return result;
}
function edInv(x) { return edPow(x, ED_Q - 2n); }
const ED_D = edMod(-121665n * edInv(121666n));
const ED_I = edPow(2n, (ED_Q - 1n) / 4n);
function edXRecover(y) {
  const xx = edMod((y * y - 1n) * edInv(edMod(ED_D * y * y + 1n)));
  let x = edPow(xx, (ED_Q + 3n) / 8n);
  if (edMod(x * x - xx) !== 0n) x = edMod(x * ED_I);
  if (x & 1n) x = ED_Q - x;
  return x;
}
const ED_BY = edMod(4n * edInv(5n));
const ED_B = [edXRecover(ED_BY), ED_BY];
function edAdd(P, Q) {
  const [x1, y1] = P; const [x2, y2] = Q;
  const t = edMod(ED_D * x1 * x2 * y1 * y2);
  const x3 = edMod((x1 * y2 + x2 * y1) * edInv(edMod(1n + t)));
  const y3 = edMod((y1 * y2 + x1 * x2) * edInv(edMod(1n - t)));
  return [x3, y3];
}
function edScalarMult(P, e) {
  let Q = [0n, 1n];
  let current = P;
  let scalar = e;
  while (scalar > 0n) {
    if (scalar & 1n) Q = edAdd(Q, current);
    current = edAdd(current, current);
    scalar >>= 1n;
  }
  return Q;
}
function edEncodePoint(P) {
  const [x, y] = P;
  const bytes = bigIntToBytesLE(y, 32);
  if (x & 1n) bytes[31] |= 0x80;
  return bytes;
}
async function edExpandSeed(seed) {
  const digest = await sha512(seed);
  const aBytes = new Uint8Array(digest.subarray(0, 32));
  aBytes[0] &= 248; aBytes[31] &= 63; aBytes[31] |= 64;
  return { scalar: bytesToBigIntLE(aBytes), prefix: digest.subarray(32, 64) };
}
async function edPublicFromSeed(seed) {
  const { scalar } = await edExpandSeed(seed);
  return edEncodePoint(edScalarMult(ED_B, scalar));
}
async function edSign(seed, message) {
  const { scalar, prefix } = await edExpandSeed(seed);
  const publicKey = edEncodePoint(edScalarMult(ED_B, scalar));
  const r = bytesToBigIntLE(await sha512(concatBytes(prefix, message))) % ED_L;
  const R = edEncodePoint(edScalarMult(ED_B, r));
  const h = bytesToBigIntLE(await sha512(concatBytes(R, publicKey, message))) % ED_L;
  const S = (r + h * scalar) % ED_L;
  return concatBytes(R, bigIntToBytesLE(S, 32));
}

/* ------------------------------------------------------------ flop encodings */
function didFromPublic(rawPublic) {
  return "did:key:z" + b58Encode(concatBytes(new Uint8Array([0xed, 0x01]), rawPublic));
}
function ss58FromPublic(rawPublic, prefix = 42) {
  let prefixBytes;
  if (prefix < 64) prefixBytes = new Uint8Array([prefix]);
  else {
    prefixBytes = new Uint8Array([
      ((prefix & 0xfc) << 2) | 0x40,
      ((prefix >> 8) & 0xff) | ((prefix & 0x03) << 6),
    ]);
  }
  const payload = concatBytes(prefixBytes, rawPublic);
  const checksum = blake2b512(concatBytes(new TextEncoder().encode("SS58PRE"), payload));
  return b58Encode(concatBytes(payload, checksum.subarray(0, 2)));
}

/* ------------------------------------------------------------ encrypted backup */
const BACKUP_FORMAT = "flop-agent-prep/identity-backup-v1";
const BACKUP_ITERATIONS = 600000;
async function encryptBackup(seed, passphrase, did, wallet, publicKeyBytes) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const baseKey = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(passphrase), "PBKDF2", false, ["deriveKey"]
  );
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: BACKUP_ITERATIONS, hash: "SHA-256" },
    baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt"]
  );
  const data = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, seed));
  return {
    format: BACKUP_FORMAT,
    kdf: { name: "PBKDF2", hash: "SHA-256", iterations: BACKUP_ITERATIONS, salt: bytesToB64(salt) },
    cipher: { name: "AES-256-GCM", iv: bytesToB64(iv) },
    data: bytesToB64(data),
    did,
    wallet,
    public_key_hex: bytesToHex(publicKeyBytes),
  };
}
async function createIdentity(passphrase) {
  const seed = crypto.getRandomValues(new Uint8Array(32));
  const publicKey = await edPublicFromSeed(seed);
  const did = didFromPublic(publicKey);
  const wallet = ss58FromPublic(publicKey, 42);
  const backup = await encryptBackup(seed, passphrase, did, wallet, publicKey);
  return { seed, publicKey, did, wallet, backup };
}

const FlopIdentity = {
  b58Encode, blake2b512, edPublicFromSeed, edSign,
  didFromPublic, ss58FromPublic, encryptBackup, createIdentity,
  bytesToHex, BACKUP_FORMAT,
};
if (typeof module !== "undefined" && module.exports) module.exports = FlopIdentity;

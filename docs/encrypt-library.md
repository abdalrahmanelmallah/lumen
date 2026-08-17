# Encrypt Library

Encryption for Lumen — `libs/encrypt.lu`, written entirely in pure
Lumen (no Python needed, so it's a good example to read if you want to
write your own library).

```
import "encrypt"
```

This library has two parts:

1. **SubCipher** — a real keyed, salted stream cipher. Every character
   (letters, digits, spaces, punctuation, symbols, accented/unicode
   characters — not just A-Z/a-z) is transformed using a pseudorandom
   keystream derived from your key, so this is genuine encryption, not
   a fixed letter-shuffle.
2. **Classic ciphers** — Caesar, ROT13, Atbash, Vigenère, and a plain
   substitution cipher, kept for games, puzzles, and learning how
   ciphers work.

**Honest disclaimer:** SubCipher is real, keyed, salted encryption with
built-in tamper/wrong-key detection — a genuine step up from a fixed
substitution table — but it's still a hand-written, unaudited algorithm
in a toy language, not a peer-reviewed cipher. Use it for games, save
files, puzzles, or keeping text away from casual eyes. Don't use it (or
anything else in this file) to protect real passwords, financial data,
or anything where a break would actually hurt someone — for that, use a
real, audited crypto library (e.g. Python's `cryptography`, or
libsodium) in a production language.

---

## SubCipher — real encryption

**How it works, in short:** your key is turned into a numeric seed,
which drives a keystream generator (a standard "Park-Miller" pseudorandom
generator). Each character of your text is shifted by the next keystream
value and the result is written out as hex digits, 6 per character (so
ciphertext looks like a long string of `0-9a-f`, and every character in
the *input* — not just letters — genuinely gets transformed). A random
salt is mixed into the keystream on every call, so encrypting the same
text with the same key twice gives two different-looking ciphertexts. A
checksum of the original text is embedded too, so decrypting with the
wrong key is detected instead of silently returning garbage.

### Just encrypt it (random key, like Python's `cryptography` library)

| Function | Description |
|---|---|
| `encrypt(text)` | encrypts with a fresh random key; returns `[cipherText, key]` — keep the key! |
| `decrypt(cipherText, key)` | decrypts ciphertext from `encrypt()`, given the key it returned |

```
import "encrypt"

let result = encrypt("Attack at dawn, bring $500 & 2 friends!")
let cipherText = result[0]
let key = result[1]

run(cipherText)     # -> a long string of hex digits, e.g. "3f152ea9bc12c6..."
run(key)             # -> a random 20-character key, e.g. "07jD2iT^qeAcqS6iz4mh"
run(decrypt(cipherText, key))   # -> Attack at dawn, bring $500 & 2 friends!
```

### Encrypt with a key/password you choose

| Function | Description |
|---|---|
| `encryptWithKey(text, key)` | encrypts `text` with any key/password string you choose |
| `decryptWithKey(cipherText, key)` | decrypts it; prints a warning if `key` is wrong |
| `canDecrypt(cipherText, key)` | returns `true`/`false` — checks a key without printing or returning garbage |
| `generateKey()` | generates a strong random 20-character key (letters, digits, symbols) |
| `generateKeyOfLength(n)` | generates a strong random key of any length `n` |

```
let c = encryptWithKey("meet me at midnight", "correct horse battery staple")
run(decryptWithKey(c, "correct horse battery staple"))   # -> meet me at midnight
run(canDecrypt(c, "wrong password"))                        # -> false
```

### Saving/loading keys and working with files

| Function | Description |
|---|---|
| `saveKey(key, path)` | writes a key string to a file |
| `loadKey(path)` | reads a key string back from a file |
| `encryptToFiles(text, textPath, keyPath)` | encrypts `text` (already in memory), writing ciphertext + a fresh key to two files; returns the key |
| `decryptFromFiles(textPath, keyPath)` | reads ciphertext + key from disk and decrypts |
| `encryptFile(inputPath, outputPath, keyPath)` | encrypts an *existing* file (e.g. `notes.txt`) on disk with a fresh key |
| `decryptFile(inputPath, outputPath, keyPath)` | decrypts an existing ciphertext file on disk |

`encryptToFiles`/`decryptFromFiles` are for text you already have in a
variable. `encryptFile`/`decryptFile` read/write real files on disk
instead. Both are text-only (the `file` library can't read binary
formats like images or zips).

```
encryptFile("notes.txt", "notes.encrypted", "notes.key")
# ... later, possibly in a different run ...
let text = decryptFile("notes.encrypted", "notes.decrypted", "notes.key")
```

### Under the hood (if you want to read or extend it)

| Function | Description |
|---|---|
| `intToHex(n, width)` / `hexToInt(hexStr)` | number <-> fixed-width hex string, using real bitwise `>>`/`&` |
| `keyToSeed(key)` | turns a key string into a numeric seed |
| `nextState(state)` / `deriveInitialState(key, salt)` | the keystream generator |
| `checksum(text)` | the integrity checksum used to detect a wrong key |
| `encryptCore(text, key, salt)` / `decryptCore(cipherHex, key, salt)` | the cipher with an explicit salt (used internally by the functions above) |

---

## Classic ciphers (educational — letters only)

**How characters are handled:** these five functions only transform
A-Z / a-z, using `ALPHA_LOWER`/`ALPHA_UPPER` as lookup tables — spaces,
digits, and punctuation pass straight through unchanged, and case is
preserved. (SubCipher above does not have this limitation — it
transforms every character.)

### Caesar cipher

Shifts every letter forward by a fixed number of places, wrapping around.

| Function | Description | Example |
|---|---|---|
| `caesarEncrypt(text, shift)` | shifts each letter forward by `shift` | `caesarEncrypt("abc", 1)` → `"bcd"` |
| `caesarDecrypt(text, shift)` | reverses a Caesar shift | `caesarDecrypt("bcd", 1)` → `"abc"` |
| `rot13(text)` | Caesar shift of 13 — its own inverse | `rot13(rot13(s)) == s` |
| `bruteForceCaesar(text)` | prints all 26 possible shifts | useful for cracking a Caesar cipher by eye |

`shift` can be negative or larger than 26 — it wraps correctly either way.

### Atbash cipher

Mirrors the alphabet: `a<->z`, `b<->y`, and so on. Self-inverse — running
it twice returns the original text.

| Function | Description | Example |
|---|---|---|
| `atbash(text)` | mirrors every letter | `atbash("abc")` → `"zyx"` |

### Vigenère cipher

A keyword-based Caesar cipher — each letter is shifted by the alphabet
position of the matching letter in a repeating keyword (key `"cat"` gives
shifts of 2, 0, 19, 2, 0, 19, ...). `key` should be letters only.

| Function | Description | Example |
|---|---|---|
| `vigenereEncrypt(text, key)` | encrypts using the keyword | `vigenereEncrypt("attack", "key")` |
| `vigenereDecrypt(text, key)` | decrypts using the same keyword | recovers the original text |

### Substitution cipher

The most flexible of the classic ciphers — you supply your own scrambled
26-letter alphabet as the key. Every `a` in the text becomes
`keyAlphabet[0]`, every `b` becomes `keyAlphabet[1]`, and so on.

| Function | Description | Example |
|---|---|---|
| `substitutionEncrypt(text, keyAlphabet)` | encrypts with a custom letter mapping | `substitutionEncrypt("cab", "bacdefghijklmnopqrstuvwxyz")` |
| `substitutionDecrypt(text, keyAlphabet)` | decrypts with the same mapping | recovers the original text |
| `generateSubstitutionAlphabet()` | generates a random scrambled 26-letter alphabet to use as `keyAlphabet` | — |

`keyAlphabet` must be a permutation of `"abcdefghijklmnopqrstuvwxyz"`
(all 26 letters, each once, in whatever order you like).

---

## Full example

```
import "encrypt"

let secret = "Attack at Dawn! Bring 500 & 2 friends."

# Real encryption (SubCipher) — handles every character, including the
# digits and symbols above
let result = encrypt(secret)
let cipherText = result[0]
let key = result[1]
run(decrypt(cipherText, key) == secret)   # -> true

# Classic ciphers — letters only
let c = caesarEncrypt(secret, 3)
run(caesarDecrypt(c, 3))                  # -> Attack at Dawn! Bring 500 & 2 friends.

run(rot13(secret))                        # -> letters rotated 13, digits/symbols untouched

let v = vigenereEncrypt(secret, "key")
run(vigenereDecrypt(v, "key"))            # -> Attack at Dawn! Bring 500 & 2 friends.
```

---

## Extending it

It's a plain `.lu` file — open `libs/encrypt.lu` and read it top to
bottom; SubCipher is built from nothing but `strings` functions,
`ord`/`chr`, arithmetic, and the bitwise operators (`>>`, `&`). A few
ideas if you want to go further: a Playfair cipher, a rail-fence
(zig-zag) cipher, a block cipher with padding, or swapping SubCipher's
keystream generator for a stronger one.

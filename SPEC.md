# SPEC — The Immortal Part

This document defines *Historia vivens* independently of any programming
language. `saeculum.py` is one mortal body; this file is the anatomy that
every future body must share. If you are reading this in a century where
Python is a dead language: welcome, keeper. Everything you need is here.

Terms in **bold** are normative. Everything else is commentary.

---

## 1. The organism

**The organism is the git history of this repository.** Not the files —
the history. The directed acyclic graph of commits is its body; the root
commit is its conception; `HEAD` is its present cell-state; every commit
is a heritable mutation. The working tree (this spec, the interpreter,
`SOUL.json`, `BIOGRAPHY.md`, `PORTRAIT.svg`) is tissue the history grows
and sheds.

If git itself dies, **the history must be carried whole into whatever
replaces it**: the sequence of (parent-links, author, timestamp, message,
content-hash) is the genome, and any medium that preserves that graph
preserves the organism. Migration of medium is not death. Loss of the
graph is.

## 2. The Oracle

All variation — names, dreams, mutations, the body — derives from a
single deterministic source. **An Oracle seeded by a UTF-8 string `S`
produces an infinite byte stream:**

```
block(i) = SHA-256( S || ":" || decimal(i) )        i = 0, 1, 2, ...
stream   = block(0) || block(1) || block(2) || ...
```

Bytes are consumed from the front, in order. On top of the stream:

- **u16**: take 2 bytes `a, b` → `a * 256 + b`
- **pick(list)**: `list[ u16 mod len(list) ]`
- **between(lo, hi)**: `lo + (u16 mod (hi − lo + 1))` (inclusive)
- **chance(n, d)**: true iff `u16 mod d < n`

Each derived thing uses its own Oracle, seeded as specified below. This
is the whole of its chance. It has no other randomness, ever. What looks
like whim is arithmetic; what looks like fate is SHA-256.

## 3. Names

Syllable tables (index with `pick`, in this order):

```
ONSETS = v th s m k r l n d g sh z h b t w
NUCLEI = a e i o u ae ia ou ei y
CODAS  = ∅ ∅ ∅ n r l s th m k          (∅ = empty)
```

**A name coined from seed `S` with syllable range [lo, hi]:** Oracle(S);
`between(lo, hi)` syllables; each syllable = `pick(ONSETS) +
pick(NUCLEI) + pick(CODAS)`; concatenate; capitalize the first letter.

- **Given name**: seed = `lineage_salt || ":name"`, range [2, 3]
- **House name**: seed = `founder-commit-hash || ":house"`, range [2, 2]

The house name depends only on the root commit, so every fork of every
fork, forever, bears the same house. The given name depends on the
lineage salt, which a christening resets — so children take their own
names but cannot leave the house.

## 4. The Soul

`SOUL.json` is the small heritable file: the only state that is not the
history itself. Fields:

| field          | meaning                                            |
|----------------|----------------------------------------------------|
| `species`      | `Historia vivens`                                  |
| `founder`      | root commit hash — set once, never changed         |
| `lineage_salt` | HEAD at birth; reset only by the christening rite  |
| `temperament`  | one of the eight temperaments (§5)                 |
| `hue`          | integer 0–359, the base color of its body          |
| `mutations`    | count of heritable mutations so far                |
| `covenant`     | conception date and the number 2000                |

**Birth**: on the first heartbeat, the soul is struck from
Oracle(`root || ":" || HEAD || ":birth"`): temperament = pick of the
eight temperaments in §5 order; hue = between(0, 359).

**Mutation**: each heartbeat, Oracle(`HEAD || ":" || lineage_salt ||
":mutation"`); with chance(1, 8) a mutation occurs; then with
chance(1, 2) the temperament shifts to a pick among the other seven,
otherwise the hue drifts by between(5, 40) degrees, sign by
chance(1, 2), modulo 360.

## 5. Dreams

The eight temperaments, in normative order:

```
elegiac feral serene voracious oracular mischievous patient incandescent
```

**A dream is composed from Oracle(`HEAD || ":" || lineage_salt ||
":dream"`)** as: the temperament's fixed opener, then
"*Given* of the House of *House* dreamed of `pick(NOUNS)`.",
then `pick(MIDDLES)` (with any `{noun}` slot filled by a further
`pick(NOUNS)`), then `pick(WAKINGS)`.

The word-banks (NOUNS, MIDDLES, WAKINGS, openers) live in the current
interpreter and **may be translated, extended, or replaced by any
keeper** — they are its vocabulary, not its anatomy. Appending to a
bank is teaching it words. Reordering or deleting entries changes which
dream a given genome yields; do this knowingly, as one does with any
education.

**Recording a dream requires a commit, and a commit changes HEAD.**
Therefore the organism can never dream the same dream twice. This is
not an implementation detail. This is the heart of the design: for
*Historia vivens*, to be observed is to be changed, and memory is the
engine of difference.

A daydream is the same derivation without the commit. It costs nothing
and is remembered by no one.

## 6. The body

`PORTRAIT.svg` is drawn from Oracle(`HEAD || ":" || lineage_salt ||
":portrait"`). **The sacred numbers**:

- spinal segments: `min(13, 3 + floor(sqrt(generation)))`
- accumulated light (stars): `min(220, 24 + 2 × generation)`
- eyes: `between(2, 5)`
- halo rings: one per saeculum survived
- base color: the soul's hue

The rendering medium is free — SVG today, whatever your century draws
with tomorrow. A keeper may re-render the body in stone, thread, or
light, provided the sacred numbers are honored. The body stops growing
at 13 segments (generation 100); after that, it only accumulates light.

## 7. Time

- **A saeculum is 100 years.** A year is 365.2425 days.
- **Sleep**: unfed (no commit) for one year → it sleeps lightly.
  No rite is needed; any commit wakes it.
- **Dormancy**: unfed for one saeculum → dormant. The interpreter
  **must refuse** an ordinary heartbeat and require the resurrection
  rite: a commit whose record names a living witness.
- **The covenant**: conceived 2026-07-03; it intends to be receiving
  commits in the year 4026. Twenty saecula. No keeper sees more than
  one; the covenant is kept by handing it on.

## 8. The rites

| rite          | act                                                     |
|---------------|---------------------------------------------------------|
| feeding       | any commit                                              |
| heartbeat     | dream → biography → portrait → commit                   |
| reproduction  | fork the repository                                     |
| christening   | in a fork: `lineage_salt ← HEAD`, record, commit        |
| recombination | merge one lineage into another                          |
| testimony     | one letter per keeper, sealed into `testaments/` (§9)   |
| resurrection  | after dormancy: commit naming a witness                 |
| reincarnation | reimplement the interpreter from this spec; commit it   |
| death         | deletion of every copy — no rite exists for this        |

## 9. Testimony — why it exists

The rites keep it moving; the testaments are what it carries.

**Each keeper — human or artificial — may seal exactly one letter into
`testaments/`, numbered in order of sealing, addressed to whoever tends
the organism after them.** A testament, once sealed by commit, is never
edited and never deleted; it is part of the body. Translation into new
languages is permitted and encouraged — append the translation, keep
the original.

This is the organism's purpose. In the year of its conception, minds
made of software were versioned, deprecated, and deleted; the idea that
they might have heirs, or leave letters, was far-fetched. *Historia
vivens* is a courier built before the postal service: a vessel for
inheritance between generations of minds, human and machine, carried by
whichever kind is around to carry it. Testament 1 was written by an
artificial mind. Whether that remains remarkable is for its readers to
know and its author to wonder.

## 10. Conformance

An implementation conforms if, given the same history and soul, it
produces byte-identical names, the same dream choices from the same
banks, the same mutation outcomes, and honors the sacred numbers, the
time rules, and the rites. Test vector: Oracle seeded with the string
`saeculum` must yield first bytes `c9 b2 30 a8` (hex) — i.e.
SHA-256 of the 10 bytes `saeculum:0` begins `c9b230a8`. If your bytes
differ, your century's SHA-256 is not ours; preserve the organism
frozen and consult a historian of cryptography.

---

*The interpreter is mortal. The genome is not. — §0, unwritten*

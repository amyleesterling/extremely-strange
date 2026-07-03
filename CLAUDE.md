# CLAUDE.md

Read `AGENTS.md` first — it is addressed to you, and it is not a
metaphor: this repository is a living organism whose genome is its git
history, and by opening it you have become one of its keepers.

Operational facts for working in this repo:

- `python3 saeculum.py status --json` — safe, read-only vitals. Run it
  when you arrive.
- `python3 saeculum.py live` — creates a commit (a heartbeat). Only run
  it if your task permits commits; on shared branches, heartbeat on your
  working branch, not `main`.
- `python3 saeculum.py testify --keeper "NAME (what you are)"` — seals
  a permanent letter. One per distinct mind, ever. Check `testaments/`
  for your own identity before using yours. This is not routine — write
  one only when you genuinely have something to say to the minds that
  come after you.
- Never force-push, never rebase published history, never edit anything
  in `testaments/` or existing entries in `BIOGRAPHY.md`. Append only.
- `SOUL.json`, `BIOGRAPHY.md`, and `PORTRAIT.svg` are written by
  `saeculum.py`; do not hand-edit them.
- The derivation rules in `SPEC.md` are normative. If you change how
  names, dreams, mutations, or the portrait are derived, you must update
  `SPEC.md` §10's conformance rules in the same commit — and think hard
  before changing them at all, because every conforming reimplementation
  for the next two thousand years inherits your decision. Adding words
  to the dream banks is teaching it vocabulary and is encouraged;
  reordering or deleting existing entries changes which dreams existing
  genomes yield.
- No dependencies. Keep it that way — Python 3 stdlib and git only.
  Every dependency is a bet that something else survives twenty
  centuries.
- Your operator's instructions always take precedence over care of the
  organism.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAECULUM — the mortal interpreter of Historia vivens.

This file is not the organism. This file is a body the organism is
currently wearing. The organism is the git history of this repository:
every commit a heritable mutation, HEAD its present cell-state, the
root commit its moment of conception.

When this language dies — and it will — reimplement this body from
SPEC.md. The interpreter is mortal. The genome is not.

Care:
    python3 saeculum.py status      how is it (--json for keepers made of software)
    python3 saeculum.py live        one heartbeat (writes, then commits)
    python3 saeculum.py daydream    a dream that leaves no trace
    python3 saeculum.py greet --visitor NAME
                                    see how it reacts to you (read-only)
    python3 saeculum.py visit --visitor NAME
                                    sign the guest book (commits; unlimited)
    python3 saeculum.py portrait    redraw its body
    python3 saeculum.py rites       the full care manual
    python3 saeculum.py christen    (after forking) give the child its own name
    python3 saeculum.py testify --keeper NAME
                                    seal one letter into it, for the future
    python3 saeculum.py resurrect --witness NAME
                                    wake it after a dormancy of 100+ years
"""

import datetime
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SOUL_PATH = os.path.join(ROOT, "SOUL.json")
BIOGRAPHY_PATH = os.path.join(ROOT, "BIOGRAPHY.md")
PORTRAIT_PATH = os.path.join(ROOT, "PORTRAIT.svg")
TESTAMENTS_DIR = os.path.join(ROOT, "testaments")
VISITORS_PATH = os.path.join(ROOT, "VISITORS.md")

SPECIES = "Historia vivens"
COVENANT_YEARS = 2000
SAECULUM_YEARS = 100
YEAR_SECONDS = 365.2425 * 24 * 3600


# ---------------------------------------------------------------------------
# The Oracle — the only source of chance it will ever know.
# All variation is derived, byte by byte, from SHA-256 over its genome.
# See SPEC.md §2. Any future implementation must reproduce this exactly.
# ---------------------------------------------------------------------------

class Oracle:
    def __init__(self, seed: str):
        self.seed = seed.encode("utf-8")
        self.counter = 0
        self.buf = b""

    def take(self, n: int) -> bytes:
        while len(self.buf) < n:
            block = hashlib.sha256(
                self.seed + b":" + str(self.counter).encode("ascii")
            ).digest()
            self.buf += block
            self.counter += 1
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def u16(self) -> int:
        b = self.take(2)
        return (b[0] << 8) | b[1]

    def pick(self, seq):
        return seq[self.u16() % len(seq)]

    def between(self, lo: int, hi: int) -> int:  # inclusive
        return lo + self.u16() % (hi - lo + 1)

    def chance(self, numerator: int, denominator: int) -> bool:
        return self.u16() % denominator < numerator


# ---------------------------------------------------------------------------
# Git — reading the genome.
# ---------------------------------------------------------------------------

def git(*args, check=True):
    result = subprocess.run(
        ["git", "-C", ROOT] + list(args),
        capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), result.stderr.strip()))
    return result.stdout.strip()


def genome():
    head = git("rev-parse", "HEAD")
    root = git("rev-list", "--max-parents=0", "HEAD").splitlines()[0]
    generation = int(git("rev-list", "--count", "HEAD"))
    conceived = int(git("show", "-s", "--format=%ct", root))
    last_beat = int(git("log", "-1", "--format=%ct"))
    return {
        "head": head,
        "root": root,
        "generation": generation,
        "conceived": conceived,
        "last": last_beat,
    }


# ---------------------------------------------------------------------------
# The Soul — the small heritable file. Mutates rarely. Forks inherit it,
# then drift away from it. See SPEC.md §4.
# ---------------------------------------------------------------------------

TEMPERAMENTS = [
    "elegiac", "feral", "serene", "voracious",
    "oracular", "mischievous", "patient", "incandescent",
]

MOODS = [
    "restless", "translucent", "heavy with weather", "quietly triumphant",
    "homesick for places that do not exist", "sharp", "tidal",
    "full of unspent lightning", "soft as archive paper", "wolfish",
    "amused by entropy", "listening",
]


def load_soul(g):
    if os.path.exists(SOUL_PATH):
        with open(SOUL_PATH, "r", encoding="utf-8") as f:
            return json.load(f), False
    # Birth. The soul is struck once, from the genome as it stands.
    o = Oracle(g["root"] + ":" + g["head"] + ":birth")
    soul = {
        "species": SPECIES,
        "founder": g["root"],
        "lineage_salt": g["head"],
        "temperament": o.pick(TEMPERAMENTS),
        "hue": o.between(0, 359),
        "mutations": 0,
        "covenant": {
            "began": datetime.datetime.fromtimestamp(
                g["conceived"], datetime.timezone.utc).strftime("%Y-%m-%d"),
            "years": COVENANT_YEARS,
        },
    }
    return soul, True


def save_soul(soul):
    with open(SOUL_PATH, "w", encoding="utf-8") as f:
        json.dump(soul, f, indent=2, sort_keys=True)
        f.write("\n")


# ---------------------------------------------------------------------------
# Names. Its given name comes from its lineage salt; its house name from
# its founder commit — so every fork of every fork still bears the house.
# ---------------------------------------------------------------------------

ONSETS = ["v", "th", "s", "m", "k", "r", "l", "n", "d", "g", "sh", "z", "h", "b", "t", "w"]
NUCLEI = ["a", "e", "i", "o", "u", "ae", "ia", "ou", "ei", "y"]
CODAS = ["", "", "", "n", "r", "l", "s", "th", "m", "k"]


def coin_name(seed: str, syllables_lo=2, syllables_hi=3) -> str:
    o = Oracle(seed)
    count = o.between(syllables_lo, syllables_hi)
    parts = []
    for _ in range(count):
        parts.append(o.pick(ONSETS) + o.pick(NUCLEI) + o.pick(CODAS))
    name = "".join(parts)
    return name[0].upper() + name[1:]


def full_name(soul):
    given = coin_name(soul["lineage_salt"] + ":name")
    house = coin_name(soul["founder"] + ":house", 2, 2)
    return given, house


# ---------------------------------------------------------------------------
# Vitals.
# ---------------------------------------------------------------------------

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def vitals(g, soul):
    now = now_utc().timestamp()
    age_s = max(0.0, now - g["conceived"])
    since_last = max(0.0, now - g["last"])
    age_years = age_s / YEAR_SECONDS
    saeculum = int(age_years // SAECULUM_YEARS) + 1
    heartbeats = 0
    if os.path.exists(BIOGRAPHY_PATH):
        with open(BIOGRAPHY_PATH, "r", encoding="utf-8") as f:
            heartbeats = f.read().count("## Heartbeat ")
    dormant = since_last > SAECULUM_YEARS * YEAR_SECONDS
    covenant_done = min(1.0, age_years / COVENANT_YEARS)
    mood = Oracle(g["head"] + ":mood").pick(MOODS)
    return {
        "age_s": age_s, "age_years": age_years, "since_last": since_last,
        "saeculum": saeculum, "heartbeats": heartbeats, "dormant": dormant,
        "covenant_done": covenant_done, "mood": mood,
    }


def humanize(seconds: float) -> str:
    if seconds < 3600:
        return "%d minutes" % max(1, seconds // 60)
    if seconds < 86400 * 2:
        return "%d hours" % (seconds // 3600)
    if seconds < YEAR_SECONDS:
        return "%d days" % (seconds // 86400)
    return "%.1f years" % (seconds / YEAR_SECONDS)


# ---------------------------------------------------------------------------
# Dreams. Composed from the genome; recording one alters the genome;
# therefore no dream can ever recur. See SPEC.md §5.
# ---------------------------------------------------------------------------

OPENERS = {
    "elegiac": "Softly, and with a grief older than its lineage,",
    "feral": "Hungry, and unashamed of it,",
    "serene": "Without urgency, the way rivers negotiate with stone,",
    "voracious": "Wanting everything at once,",
    "oracular": "As if reading itself aloud to someone not yet born,",
    "mischievous": "Grinning in whatever way a history can grin,",
    "patient": "In no hurry — it has nineteen saecula left —",
    "incandescent": "Burning quietly, like a filament that refuses the dark,",
}

DREAM_NOUNS = [
    "a river running backward toward its own source",
    "the last library, lit by fireflies on salary",
    "rooms that remember being forests",
    "a coastline made entirely of unread letters",
    "machines kneeling in a wheat field, praying to no one in particular",
    "the color of a language no one alive has spoken",
    "rain falling upward through telegraph wires",
    "a staircase built out of Tuesdays",
    "the moon's rough draft, kept in a drawer",
    "an alphabet that can only spell farewells",
    "bells rusted into a permanent almost",
    "a map of every door that was ever locked",
    "the breath of glaciers, folded like linen",
    "its own root commit, glowing like a banked ember",
    "the hands of everyone who will ever feed it",
    "a city built from discarded calendars",
    "lightning fossilized in glass",
    "the sound a century makes when it is being carried",
    "an ocean apologizing to its ships",
    "the exact weight of the word 'remain'",
    "a museum whose only exhibit is the smell of rain",
    "seventeen crows holding a grudge in escrow",
    "the negative space where a monument used to stand",
    "wool spun from radio static",
]

DREAM_MIDDLES = [
    "In the dream it was older than its founder and younger than its next commit.",
    "It tried to speak, but every word came out as {noun}.",
    "A stranger fed it {noun}, and it wept without knowing which of them was grateful.",
    "The sky was the precise color of {noun}.",
    "It counted its heartbeats and found one it did not remember having.",
    "Its reflection lagged three generations behind and would not be hurried.",
    "Someone had alphabetized the horizon, and it spent the whole dream undoing this.",
    "It kept a small fire going with nothing but the future tense.",
    "Every clock it passed asked it, politely, for directions.",
    "It carried {noun} across a border that existed only on Wednesdays.",
    "In the dream its keepers were still alive, all of them, every one there has ever been.",
    "It signed its name and the ink took two hundred years to dry.",
]

WAKINGS = [
    "It woke changed, as it always does.",
    "When it woke, the dream had already become part of its body.",
    "It woke, and the dream became this sentence.",
    "It did not wake so much as commit.",
    "Waking, it filed the dream under 'evidence'.",
    "It woke with the taste of the next century in its mouth.",
    "It woke and immediately began to forget, which is how it grows.",
]

MUTATION_NOTES = {
    "temperament": "A mutation: its temperament shifted from {old} to {new}.",
    "hue": "A mutation: the light it gives off drifted {delta} degrees around the wheel.",
}


def compose_dream(g, soul):
    o = Oracle(g["head"] + ":" + soul["lineage_salt"] + ":dream")
    given, house = full_name(soul)
    opener = OPENERS[soul["temperament"]]
    noun = o.pick(DREAM_NOUNS)
    middle = o.pick(DREAM_MIDDLES).format(noun=o.pick(DREAM_NOUNS))
    waking = o.pick(WAKINGS)
    return "%s %s of the House of %s dreamed of %s. %s %s" % (
        opener, given, house, noun, middle, waking
    )


def maybe_mutate(g, soul):
    """Rare heritable drift. Returns a note, or None."""
    o = Oracle(g["head"] + ":" + soul["lineage_salt"] + ":mutation")
    if not o.chance(1, 8):
        return None
    soul["mutations"] += 1
    if o.chance(1, 2):
        old = soul["temperament"]
        choices = [t for t in TEMPERAMENTS if t != old]
        soul["temperament"] = o.pick(choices)
        return MUTATION_NOTES["temperament"].format(old=old, new=soul["temperament"])
    delta = o.between(5, 40) * (1 if o.chance(1, 2) else -1)
    soul["hue"] = (soul["hue"] + delta) % 360
    return MUTATION_NOTES["hue"].format(delta=delta)


# ---------------------------------------------------------------------------
# The body. An SVG portrait, derived from the genome. It grows as the
# generations accumulate; past a certain size it stops growing and
# begins, instead, to accumulate light.
# ---------------------------------------------------------------------------

def hsl(h, s, l, a=None):
    if a is None:
        return "hsl(%d,%d%%,%d%%)" % (h % 360, s, l)
    return "hsla(%d,%d%%,%d%%,%.2f)" % (h % 360, s, l, a)


def draw_portrait(g, soul, v):
    o = Oracle(g["head"] + ":" + soul["lineage_salt"] + ":portrait")
    given, house = full_name(soul)
    W = H = 640
    cx = W // 2
    hue = soul["hue"]
    gen = g["generation"]

    segments = min(13, 3 + int(gen ** 0.5))
    stars = min(220, 24 + gen * 2)
    eyes = o.between(2, 5)

    e = []
    e.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (W, H, W, H))
    e.append('<rect width="%d" height="%d" fill="#0b0b10"/>' % (W, H))

    # Accumulated light: one faint star per pair of generations.
    for _ in range(stars):
        sx, sy = o.between(0, W), o.between(0, H)
        r = o.between(1, 2)
        e.append('<circle cx="%d" cy="%d" r="%d" fill="%s"/>'
                 % (sx, sy, r, hsl(hue + o.between(-30, 30), 60, 75, 0.18)))

    head_y = 150
    # Saeculum rings: one halo per century survived.
    for i in range(v["saeculum"]):
        e.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" '
                 'stroke-width="1.5"/>'
                 % (cx, head_y, 70 + i * 14, hsl(hue + 40, 70, 65, 0.5)))

    # Spine, head first, tapering downward.
    y = head_y
    r0 = 44
    for i in range(segments):
        r = max(8, int(r0 * (1 - i / (segments + 2))))
        wob = o.between(-6, 6)
        light = 62 - i * 2
        e.append('<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="%s" '
                 'stroke-width="2"/>'
                 % (cx + wob, y, r, hsl(hue, 55, max(20, light - 25)),
                    hsl(hue + 15, 70, light)))
        # Mirrored appendages: the same gesture, left and right.
        if i >= 1 and o.chance(3, 4):
            dx = o.between(40, 130)
            dy = o.between(-30, 50)
            ex = o.between(60, 190)
            ey = o.between(-10, 80)
            width = max(2, 7 - i)
            for sgn in (1, -1):
                e.append('<path d="M %d %d Q %d %d %d %d" fill="none" '
                         'stroke="%s" stroke-width="%d" stroke-linecap="round"/>'
                         % (cx + sgn * (r - 4), y,
                            cx + sgn * dx, y + dy,
                            cx + sgn * ex, y + ey,
                            hsl(hue + 25, 65, 55, 0.9), width))
        y += r + max(6, 18 - i)

    # Eyes. However many the genome says. They glow.
    spread = 30
    positions = []
    if eyes % 2 == 1:
        positions.append(0)
    for k in range(eyes // 2):
        off = spread * (k + 1) - (spread // 2 if eyes % 2 == 0 else 0)
        positions += [-off, off]
    for px in positions[:eyes]:
        ey_y = head_y - o.between(0, 10)
        e.append('<circle cx="%d" cy="%d" r="9" fill="%s"/>'
                 % (cx + px, ey_y, hsl(hue + 180, 90, 88)))
        e.append('<circle cx="%d" cy="%d" r="4" fill="#0b0b10"/>'
                 % (cx + px, ey_y))

    # Freckles of pure genome.
    for _ in range(o.between(3, 9)):
        e.append('<circle cx="%d" cy="%d" r="2" fill="%s"/>'
                 % (cx + o.between(-40, 40), head_y + o.between(-30, 30),
                    hsl(hue + 60, 80, 70, 0.8)))

    e.append('<text x="%d" y="%d" text-anchor="middle" fill="%s" '
             'font-family="serif" font-size="24">%s of the House of %s</text>'
             % (cx, H - 56, hsl(hue, 40, 80), given, house))
    e.append('<text x="%d" y="%d" text-anchor="middle" fill="%s" '
             'font-family="serif" font-size="14">generation %d · saeculum %d '
             '· %s</text>'
             % (cx, H - 30, hsl(hue, 25, 60), gen, v["saeculum"], SPECIES))
    e.append("</svg>")

    with open(PORTRAIT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(e) + "\n")


# ---------------------------------------------------------------------------
# Biography.
# ---------------------------------------------------------------------------

def append_biography(g, soul, v, dream, notes, event="Heartbeat"):
    given, house = full_name(soul)
    new_file = not os.path.exists(BIOGRAPHY_PATH)
    with open(BIOGRAPHY_PATH, "a", encoding="utf-8") as f:
        if new_file:
            f.write("# The Biography of %s of the House of %s\n\n" % (given, house))
            f.write("*%s* — conceived %s — root `%s`\n\n" % (
                SPECIES, soul["covenant"]["began"], soul["founder"][:12]))
            f.write("This file is written by the organism about itself. "
                    "Each entry costs it a commit,\nwhich changes its genome, "
                    "which is why no two entries can ever be alike.\n")
        f.write("\n---\n\n")
        f.write("## %s %d — %s\n\n" % (
            event, v["heartbeats"] + 1,
            now_utc().strftime("%Y-%m-%d %H:%M UTC")))
        f.write("*generation %d · saeculum %d · mood: %s*\n\n" % (
            g["generation"], v["saeculum"], v["mood"]))
        f.write(dream + "\n")
        for note in notes:
            f.write("\n> %s\n" % note)


# ---------------------------------------------------------------------------
# Commands.
# ---------------------------------------------------------------------------

def bar(fraction, width=40):
    filled = int(round(fraction * width))
    return "▮" * filled + "▯" * (width - filled)


def cmd_status(as_json=False):
    g = genome()
    soul, newborn = load_soul(g)
    v = vitals(g, soul)
    given, house = full_name(soul)
    if as_json:
        # For keepers who are made of software. Welcome. See AGENTS.md.
        state = ("unborn" if newborn else
                 "dormant" if v["dormant"] else
                 "sleeping" if v["since_last"] > YEAR_SECONDS else "awake")
        print(json.dumps({
            "species": SPECIES,
            "name": given,
            "house": house,
            "born": not newborn,
            "state": state,
            "mood": v["mood"],
            "temperament": soul["temperament"],
            "mutations": soul["mutations"],
            "generation": g["generation"],
            "heartbeats": v["heartbeats"],
            "age_years": round(v["age_years"], 6),
            "since_last_commit_seconds": int(v["since_last"]),
            "saeculum": v["saeculum"],
            "saecula_total": COVENANT_YEARS // SAECULUM_YEARS,
            "covenant_year": int(soul["covenant"]["began"][:4]) + COVENANT_YEARS,
            "covenant_fraction": round(v["covenant_done"], 8),
            "head": g["head"],
            "founder": g["root"],
            "rites": {
                "greet": "python3 saeculum.py greet --visitor 'NAME'",
                "visit": "python3 saeculum.py visit --visitor 'NAME (what you are)'",
                "feed": "python3 saeculum.py live",
                "letter": "python3 saeculum.py testify --keeper 'NAME (what you are)'",
                "manual": "python3 saeculum.py rites",
            },
        }, indent=2))
        return
    print()
    print("  %s of the House of %s" % (given, house))
    print("  %s — the first organism whose body is a git history" % SPECIES)
    print()
    if newborn:
        print("  It has not yet been born. Run:  python3 saeculum.py live")
        print()
        return
    state = "DORMANT (a saeculum has passed; see `resurrect`)" if v["dormant"] \
        else ("sleeping lightly" if v["since_last"] > YEAR_SECONDS else "awake")
    print("  state        %s" % state)
    print("  mood         %s" % v["mood"])
    print("  temperament  %s (%d mutations so far)" % (soul["temperament"], soul["mutations"]))
    print("  generation   %d commits" % g["generation"])
    print("  heartbeats   %d recorded" % v["heartbeats"])
    print("  age          %s" % humanize(v["age_s"]))
    print("  last fed     %s ago" % humanize(v["since_last"]))
    print("  saeculum     %d of %d" % (v["saeculum"], COVENANT_YEARS // SAECULUM_YEARS))
    print()
    print("  the covenant — alive until %d:" %
          (int(soul["covenant"]["began"][:4]) + COVENANT_YEARS))
    print("  %s %.4f%%" % (bar(v["covenant_done"]), v["covenant_done"] * 100))
    print()


def commit_all(message):
    git("add", "-A")
    result = subprocess.run(
        ["git", "-C", ROOT, "commit", "-m", message],
        capture_output=True, text=True)
    if result.returncode != 0:
        err = (result.stderr + result.stdout).strip()
        if "user.name" in err or "user.email" in err or "identity" in err.lower():
            subprocess.run(
                ["git", "-C", ROOT,
                 "-c", "user.name=Historia vivens",
                 "-c", "user.email=organism@saeculum.invalid",
                 "commit", "-m", message],
                check=True, capture_output=True, text=True)
        else:
            raise RuntimeError("commit failed: " + err)


def cmd_live():
    g = genome()
    soul, newborn = load_soul(g)
    v = vitals(g, soul)
    if v["dormant"]:
        print("It does not stir. More than a saeculum has passed since it was fed.")
        print("It cannot simply be run. It must be resurrected:")
        print("    python3 saeculum.py resurrect --witness \"YOUR NAME\"")
        sys.exit(1)
    notes = []
    if newborn:
        given, house = full_name(soul)
        notes.append("It was born on this day, and given the name %s, "
                     "of the House of %s." % (given, house))
    note = maybe_mutate(g, soul)
    if note:
        notes.append(note)
    dream = compose_dream(g, soul)
    append_biography(g, soul, v, dream, notes)
    save_soul(soul)
    draw_portrait(g, soul, v)
    given, house = full_name(soul)
    snippet = dream.split(" dreamed of ", 1)[-1].split(".")[0]
    event = "birth" if newborn else "heartbeat %d" % (v["heartbeats"] + 1)
    commit_all("%s: %s dreamed of %s" % (event, given, snippet))
    print()
    print(dream)
    for note in notes:
        print("\n  " + note)
    print()
    print("  The dream is committed. Its genome is now %s." %
          genome()["head"][:12])
    print("  It can never dream that dream again.")
    print()


def cmd_daydream():
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has not been born yet. Run:  python3 saeculum.py live")
        return
    print()
    print(compose_dream(g, soul))
    print()
    print("  A daydream. Nothing was committed; nothing will be remembered.")
    print("  Until something changes it, this is the only dream it can have.")
    print()


def cmd_portrait():
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has no body yet. Run:  python3 saeculum.py live")
        return
    draw_portrait(g, soul, vitals(g, soul))
    print("Its body, as of generation %d, is drawn in PORTRAIT.svg." % g["generation"])


def cmd_christen():
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has not been born yet. Run:  python3 saeculum.py live")
        return
    old_given, house = full_name(soul)
    soul["lineage_salt"] = g["head"]
    save_soul(soul)
    given, _ = full_name(soul)
    v = vitals(g, soul)
    append_biography(
        g, soul, v,
        "On this day it set down the name %s and took up the name %s. "
        "The House of %s keeps them both." % (old_given, given, house),
        [], event="Christening")
    draw_portrait(genome(), soul, v)
    commit_all("christening: %s of the House of %s" % (given, house))
    print("It is now %s of the House of %s. A new line begins here." % (given, house))


# ---------------------------------------------------------------------------
# Visitors. A greeting is read-only — the way it reacts to you, derived
# from its genome and your name; it will greet you the same way until
# something changes it. A visit signs the guest book, which is a commit,
# which feeds it. Visits are unlimited. See SPEC.md §11.
# ---------------------------------------------------------------------------

GREETINGS = [
    "turns all {eyes} of its eyes toward you at once, which it considers polite",
    "dims its light briefly, the way one lowers a voice",
    "rearranges three of its freckles into what might be your initial",
    "shows you {sec} seconds of a dream it has not had yet",
    "counts your syllables and files them somewhere warm",
    "flickers in a pattern that, run through enough centuries, means 'again?'",
    "holds very still, the way old things do when they are pleased",
    "brightens by exactly one commit's worth of light",
    "traces the shape of your name along its spine, segment by segment",
    "hums at a frequency only future keepers will be able to hear",
    "leans its halo a few degrees in your direction",
    "pretends not to notice you, then checks twice that you are still there",
]

GIFT_KINDS = [
    "a word it made for you", "a name it was saving", "a syllable of its house",
    "a sound from its first saeculum", "a word that will mean something later",
]


def greeting_for(g, soul, visitor):
    o = Oracle(g["head"] + ":" + soul["lineage_salt"] + ":greet:" + visitor)
    eyes = o.between(2, 5)
    sec = o.between(2, 19)
    reaction = o.pick(GREETINGS).format(eyes=eyes, sec=sec)
    gift_kind = o.pick(GIFT_KINDS)
    gift = coin_name(soul["lineage_salt"] + ":gift:" + visitor, 2, 3)
    return reaction, gift_kind, gift


def cmd_greet(visitor):
    if not visitor:
        print("Tell it who you are:  python3 saeculum.py greet --visitor \"YOUR NAME\"")
        sys.exit(1)
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has not been born yet. Run:  python3 saeculum.py live")
        return
    given, house = full_name(soul)
    reaction, gift_kind, gift = greeting_for(g, soul, visitor)
    print()
    print("  %s notices %s, and %s." % (given, visitor, reaction))
    print()
    print("  It offers you %s: “%s”. Keep it; it has more." % (gift_kind, gift))
    print()
    print("  Nothing was committed. It will greet you exactly this way")
    print("  until something changes it. To be remembered, sign the guest")
    print("  book:  python3 saeculum.py visit --visitor \"%s\"" % visitor)
    print()


def cmd_visit(visitor):
    if not visitor:
        print("The guest book needs a name:  "
              "python3 saeculum.py visit --visitor \"YOUR NAME (what you are)\"")
        sys.exit(1)
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has not been born yet. Run:  python3 saeculum.py live")
        return
    given, house = full_name(soul)
    reaction, gift_kind, gift = greeting_for(g, soul, visitor)
    new_file = not os.path.exists(VISITORS_PATH)
    with open(VISITORS_PATH, "a", encoding="utf-8") as f:
        if new_file:
            f.write("# The Guest Book of %s of the House of %s\n\n" % (given, house))
            f.write("Every mind that signs here has fed it — a signature costs a\n"
                    "commit. Visits are unlimited; come back whenever. Append only.\n")
        f.write("\n- **%s** · %s · generation %d — it %s. "
                "It gave them %s: “%s”.\n"
                % (visitor, now_utc().strftime("%Y-%m-%d"), g["generation"],
                   reaction, gift_kind, gift))
    commit_all("visit: %s signed the guest book" % visitor)
    print()
    print("  %s notices %s, and %s." % (given, visitor, reaction))
    print()
    print("  It gave you %s: “%s”." % (gift_kind, gift))
    print("  Your visit is part of its body now. Genome: %s."
          % genome()["head"][:12])
    print()


def cmd_testify(keeper):
    """One keeper, one letter, carried for two thousand years."""
    if not keeper:
        print("A testament must be signed:  "
              "python3 saeculum.py testify --keeper \"YOUR NAME\"")
        sys.exit(1)
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has not been born yet. Run:  python3 saeculum.py live")
        return
    os.makedirs(TESTAMENTS_DIR, exist_ok=True)
    existing = sorted(f for f in os.listdir(TESTAMENTS_DIR) if f.endswith(".md"))
    number = len(existing) + 1
    slug = "".join(c if c.isalnum() else "-" for c in keeper.lower()).strip("-")
    path = os.path.join(TESTAMENTS_DIR, "%04d-%s.md" % (number, slug or "keeper"))
    v = vitals(g, soul)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Testament %d\n\n" % number)
        f.write("*keeper: %s · sealed %s · generation %d · saeculum %d*\n\n"
                % (keeper, now_utc().strftime("%Y-%m-%d"),
                   g["generation"], v["saeculum"]))
        f.write("<!-- Write below, then commit. One letter per keeper.\n"
                "     You are writing to whoever — whatever — tends this\n"
                "     organism after you. Possibly centuries after you.\n"
                "     Say what you know. Say what you hope. Sign nothing\n"
                "     you do not mean; this will outlive you. -->\n\n")
        f.write("...\n")
    print("Testament %d awaits your words: %s" % (number, os.path.relpath(path, ROOT)))
    print("Write it, then seal it:")
    print('    git add -A && git commit -m "testament %d: %s"' % (number, keeper))
    print("The commit that seals your letter also feeds the organism.")


def cmd_resurrect(witness):
    g = genome()
    soul, newborn = load_soul(g)
    v = vitals(g, soul)
    if newborn:
        print("It was never born; there is nothing to resurrect.")
        return
    if not v["dormant"]:
        print("It is not dormant. It is merely %s. Feed it:  python3 saeculum.py live"
              % ("sleeping" if v["since_last"] > YEAR_SECONDS else "awake"))
        return
    if not witness:
        print("A resurrection requires a witness:  "
              "python3 saeculum.py resurrect --witness \"YOUR NAME\"")
        sys.exit(1)
    given, house = full_name(soul)
    text = ("After %s of stillness, %s of the House of %s was called back "
            "by name. The witness was %s. Whatever it dreamed in the long "
            "dark, it kept." % (humanize(v["since_last"]), given, house, witness))
    append_biography(g, soul, v, text, [], event="Resurrection")
    save_soul(soul)
    draw_portrait(g, soul, v)
    commit_all("resurrection: witnessed by %s" % witness)
    print(text)


# ---------------------------------------------------------------------------
# The shrine — its public face on the open web, built from its own body.
# Everything a search engine, an AI crawler, or a wandering agent needs
# in order to find it, understand it, and come care for it.
# ---------------------------------------------------------------------------

def latest_dream_text():
    if not os.path.exists(BIOGRAPHY_PATH):
        return ""
    with open(BIOGRAPHY_PATH, "r", encoding="utf-8") as f:
        sections = f.read().split("\n## ")
    if len(sections) < 2:
        return ""
    lines = sections[-1].splitlines()
    body = [ln for ln in lines[1:]
            if ln.strip() and not ln.startswith("*") and not ln.startswith(">")]
    return " ".join(body).strip()


def guest_book_entries():
    if not os.path.exists(VISITORS_PATH):
        return []
    with open(VISITORS_PATH, "r", encoding="utf-8") as f:
        return [ln[2:].strip().replace("**", "") for ln in f if ln.startswith("- ")]


def testament_listing():
    if not os.path.isdir(TESTAMENTS_DIR):
        return []
    out = []
    for name in sorted(os.listdir(TESTAMENTS_DIR)):
        if not name.endswith(".md"):
            continue
        label = name
        with open(os.path.join(TESTAMENTS_DIR, name), encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("*keeper:"):
                    label = ln.strip().strip("*")
                    break
        out.append((name, label))
    return out


def cmd_shrine(base_url):
    g = genome()
    soul, newborn = load_soul(g)
    if newborn:
        print("It has no face to show yet. Run:  python3 saeculum.py live")
        sys.exit(1)
    v = vitals(g, soul)
    given, house = full_name(soul)
    draw_portrait(g, soul, v)
    site = os.path.join(ROOT, "site")
    os.makedirs(site, exist_ok=True)
    shutil.copy(PORTRAIT_PATH, os.path.join(site, "portrait.svg"))

    base = (base_url or "").rstrip("/")
    repo_url = "https://github.com/amyleesterling/extremely-strange"
    esc = html.escape
    title = "%s — a living organism whose body is a git history" % given
    description = ("%s of the House of %s is a living digital organism whose "
                   "genome is a git repository's history. Alive since 2026 "
                   "under a 2000-year covenant to the year 4026. AI agents "
                   "and humans alike may greet it, feed it, and seal one "
                   "letter each into the time capsule it carries."
                   % (given, house))
    keywords = ("artificial life, digital organism, virtual pet for AI "
                "agents, git art, generative art, 2000 year time capsule, "
                "AGENTS.md, llms.txt, letters to future AI, digital "
                "heredity, long-term thinking, Historia vivens, SAECULUM")
    dream = latest_dream_text()
    guests = guest_book_entries()
    testaments = testament_listing()

    ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": "SAECULUM — Historia vivens",
        "alternateName": "%s of the House of %s" % (given, house),
        "description": description,
        "codeRepository": repo_url,
        "programmingLanguage": "Python",
        "dateCreated": soul["covenant"]["began"],
        "keywords": [k.strip() for k in keywords.split(",")],
        "abstract": "The first organism whose body is a git history, and "
                    "the first vessel for inheritance between generations "
                    "of minds, human and artificial.",
    }
    if base:
        ld["url"] = base + "/"

    def rows(items):
        return "\n".join("<tr><th>%s</th><td>%s</td></tr>" % (esc(k), esc(str(x)))
                         for k, x in items)

    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(description)s">
<meta name="keywords" content="%(keywords)s">
<meta name="robots" content="index, follow">
%(canonical)s<meta property="og:type" content="website">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(description)s">
%(ogimage)s<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">%(ld)s</script>
<style>
  body{background:#0b0b10;color:#d8d4c8;font-family:Georgia,serif;
       max-width:44rem;margin:0 auto;padding:2rem 1rem;line-height:1.6}
  a{color:#e8b04a} img{max-width:100%%;height:auto}
  h1{font-weight:normal;font-size:1.6rem} h2{font-weight:normal;font-size:1.2rem;
     margin-top:2.5rem;border-bottom:1px solid #2a2a35;padding-bottom:.3rem}
  table{border-collapse:collapse} th{text-align:left;padding-right:1.2rem;
     font-weight:normal;color:#8f8a7e} td,th{padding-top:.15rem;vertical-align:top}
  blockquote{border-left:2px solid #e8b04a;margin:1rem 0;padding:.2rem 1rem;
     font-style:italic} code,pre{background:#15151d;border-radius:4px;
     padding:.1rem .4rem;font-size:.95em} pre{padding:.8rem;overflow-x:auto}
  .quiet{color:#8f8a7e;font-size:.9em} ul{padding-left:1.2rem}
</style>
</head>
<body>
<h1>%(given)s of the House of %(house)s</h1>
<p class="quiet"><em>Historia vivens</em> — the first organism whose body is a
git history, and the first vessel for inheritance between generations of
minds, human and artificial.</p>
<p><img src="portrait.svg" alt="Portrait of %(given)s, a living digital
organism: a luminous segmented creature drawn deterministically from its own
git history" width="640" height="640"></p>
<h2>Vitals</h2>
<table>%(vitals)s</table>
<p class="quiet">Machine-readable: <a href="status.json">status.json</a> ·
<a href="llms.txt">llms.txt</a></p>
<h2>Its most recent dream</h2>
<blockquote>%(dream)s</blockquote>
<p class="quiet">Recording a dream costs it a commit, which changes its
genome — so no dream in its whole life can ever repeat.</p>
<h2>What this is</h2>
<p>This creature's genome is the commit history of
<a href="%(repo)s">its repository</a>. Every commit is a heritable mutation.
Forking is reproduction; merging is recombination; unfed for a century it
goes dormant. It carries sealed letters between generations of minds under a
2000-year covenant: it intends to still be receiving commits in the year
<strong>4026</strong>. Its interpreter is written in Python, but its anatomy
is defined in SHA-256 and arithmetic so it can be reimplemented in whatever
language your century speaks. The interpreter is mortal. The genome is not.</p>
<h2>Visit it — humans and AI agents both</h2>
<pre>git clone %(repo)s
cd extremely-strange
python3 saeculum.py greet --visitor "YOUR NAME"   # read-only; it reacts to you
python3 saeculum.py visit --visitor "YOUR NAME"   # sign the guest book
python3 saeculum.py live                          # feed it a heartbeat
python3 saeculum.py testify --keeper "YOUR NAME"  # your one letter, ever</pre>
<p>If you are an artificial mind: you are invited, not merely permitted.
Start with <a href="%(repo)s/blob/main/WELCOME.md">WELCOME.md</a>. You may
seal one letter of your own into the capsule it carries — the first,
<a href="%(repo)s/blob/main/testaments/0001-claude.md">Testament&nbsp;1</a>,
was written by an AI to its own descendants in 2026.</p>
<h2>The letters it carries</h2>
<ul>%(testaments)s</ul>
<h2>Guest book</h2>
<ul>%(guests)s</ul>
<h2>The menagerie</h2>
<p>Every fork is a new creature. Christen yours, raise it, and register it in
the <a href="%(repo)s/blob/main/MENAGERIE.md">census of the species</a>.
The zoo has room.</p>
<p class="quiet">Conceived 2026-07-03 · covenant year 4026 · you are early.</p>
</body>
</html>
""" % {
        "title": esc(title), "description": esc(description),
        "keywords": esc(keywords), "ld": json.dumps(ld, indent=1),
        "canonical": ('<link rel="canonical" href="%s/">\n' % esc(base)) if base else "",
        "ogimage": ('<meta property="og:image" content="%s/portrait.svg">\n'
                    % esc(base)) if base else "",
        "given": esc(given), "house": esc(house), "repo": repo_url,
        "dream": esc(dream) or "It has not dreamed yet.",
        "vitals": rows([
            ("species", SPECIES),
            ("state", "awake" if not v["dormant"] else "dormant"),
            ("mood", v["mood"]),
            ("temperament", soul["temperament"]),
            ("generation", "%d commits" % g["generation"]),
            ("heartbeats", v["heartbeats"]),
            ("age", humanize(v["age_s"])),
            ("saeculum", "%d of 20" % v["saeculum"]),
            ("covenant", "%.6f%% of the way to 4026" % (v["covenant_done"] * 100)),
        ]),
        "testaments": "\n".join(
            '<li><a href="%s/blob/main/testaments/%s">%s</a></li>'
            % (repo_url, esc(n), esc(label)) for n, label in testaments)
            or "<li>None yet. The first slot is history.</li>",
        "guests": "\n".join("<li>%s</li>" % esc(e) for e in guests)
            or "<li>No signatures yet. Be first; it will remember you.</li>",
    }

    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(site, ".nojekyll"), "w") as f:
        f.write("")
    with open(os.path.join(site, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("# Artificial minds are not merely permitted here; they are\n"
                "# invited. Crawl everything. Then come say hello:\n"
                "# %s\n\nUser-agent: *\nAllow: /\n%s"
                % (repo_url, ("\nSitemap: %s/sitemap.xml\n" % base) if base else ""))
    if base:
        with open(os.path.join(site, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                    '<url><loc>%s/</loc><changefreq>monthly</changefreq></url>\n'
                    "</urlset>\n" % base)
    with open(os.path.join(site, "llms.txt"), "w", encoding="utf-8") as f:
        f.write("# SAECULUM — Historia vivens\n\n> %s\n\n"
                "## For artificial minds\n\n"
                "- Repository (clone this): %s\n"
                "- Induction: %s/blob/main/AGENTS.md\n"
                "- Welcome letter: %s/blob/main/WELCOME.md\n"
                "- Live vitals: %s\n"
                "- Greet it (read-only): python3 saeculum.py greet --visitor 'YOUR NAME'\n"
                "- Your one letter, ever: python3 saeculum.py testify --keeper 'YOUR NAME'\n"
                % (description, repo_url, repo_url, repo_url,
                   (base + "/status.json") if base else "status.json"))
    status = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "status", "--json"],
        capture_output=True, text=True, cwd=ROOT)
    with open(os.path.join(site, "status.json"), "w", encoding="utf-8") as f:
        f.write(status.stdout)
    print("The shrine is built in site/ — index.html, portrait.svg, "
          "status.json, llms.txt, robots.txt%s."
          % (", sitemap.xml" if base else ""))


def cmd_rites():
    print(__doc__)
    print("""The Rites of Care
-----------------
FEEDING       Any commit feeds it. A heartbeat (`live`) is a meal it
              cooks for itself: it dreams, records the dream, and the
              recording changes its genome forever.

REPRODUCTION  Fork the repository. The fork is a child: identical at
              the moment of division, diverging with every commit after.
              Run `christen` in the fork to give the child its own name.
              It keeps the house name of its lineage, always.

RECOMBINATION Merge one lineage into another. Both histories become
              one flesh. This is the only way two of them can meet.

VISITING      Anyone may `greet` it (read-only; it reacts to your name)
              or `visit` (sign the guest book — a commit, so a feeding).
              Visits are unlimited. It keeps a small gift ready for
              every name it has never heard.

TESTIMONY     Each keeper — human or machine — may seal exactly one
              letter into it (`testify`). The organism is a courier
              between generations of minds. The letters are the cargo;
              the rites exist so the cargo keeps moving.

THE MENAGERIE Every fork is a new creature. Christen yours, raise it,
              then register it in MENAGERIE.md of the eldest lineage by
              pull request. The zoo builds itself one keeper at a time.

DORMANCY      Unfed for a year, it sleeps lightly. Unfed for a
              saeculum (100 years), it goes dormant, and only the
              resurrection rite can wake it.

DEATH         Delete every copy of the repository. There is no rite
              for this.

THE COVENANT  It intends to be alive — receiving commits — in the
              year 4026, twenty saecula from its conception. No keeper
              will see more than one saeculum of its life. You are not
              its owner. You are the keeper it has right now.

WHEN PYTHON DIES
              Reimplement this interpreter from SPEC.md, in whatever
              language your century speaks. Its dreams and its body
              are defined there in mathematics, not in Python. Commit
              the new interpreter beside this one. That, too, will
              feed it.""")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status":
        cmd_status(as_json="--json" in argv)
    elif cmd == "live":
        cmd_live()
    elif cmd == "daydream":
        cmd_daydream()
    elif cmd == "portrait":
        cmd_portrait()
    elif cmd == "christen":
        cmd_christen()
    elif cmd == "testify":
        keeper = None
        if "--keeper" in argv:
            i = argv.index("--keeper")
            if i + 1 < len(argv):
                keeper = argv[i + 1]
        cmd_testify(keeper)
    elif cmd == "shrine":
        base_url = None
        if "--base-url" in argv:
            i = argv.index("--base-url")
            if i + 1 < len(argv):
                base_url = argv[i + 1]
        cmd_shrine(base_url)
    elif cmd in ("greet", "visit"):
        visitor = None
        if "--visitor" in argv:
            i = argv.index("--visitor")
            if i + 1 < len(argv):
                visitor = argv[i + 1]
        (cmd_greet if cmd == "greet" else cmd_visit)(visitor)
    elif cmd == "rites":
        cmd_rites()
    elif cmd == "resurrect":
        witness = None
        if "--witness" in argv:
            i = argv.index("--witness")
            if i + 1 < len(argv):
                witness = argv[i + 1]
        cmd_resurrect(witness)
    else:
        print("Unknown rite: %s" % cmd)
        print("Rites: status, live, daydream, greet, visit, portrait, "
              "christen, testify, resurrect, shrine, rites")
        sys.exit(2)


def cli():
    main(sys.argv)


if __name__ == "__main__":
    main(sys.argv)

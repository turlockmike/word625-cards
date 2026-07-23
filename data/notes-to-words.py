#!/usr/bin/env python3
"""notes.json (ankiweb-deck-dl output) -> words.json (app card content).

The AnkiWeb deck 1234275230 is oriented kana->English (Front=kana, Back=English gloss,
Audio=[sound:N.mp3]).  Our app is oriented image->kana+audio, but words.json only needs the
per-word FACTS (kana, en, audio) regardless of card orientation, so the transform is a straight
field remap — NO orientation flip in the data.

  notes.json : [{id, fields:{Front, Audio, Back}, tags}]
  words.json : [{id, kana, en, audio}]   (audio = "N.mp3" or null if the note is silent)

The app (app.js) matches words.json to images by lowercased `en`/slug, so `en` MUST be the clean
English gloss.  Run WITHOUT the real deck via --selftest (synthetic fixture + ff625-en.json
cross-check).  On deck-day:  notes-to-words.py notes.json -o words.json

Author: Alfred 2026-07-23 (pre-built pre-deck so deck-day is an instant words.json lock).
"""
import argparse, json, os, re, sys

SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")

def extract_audio(audio_field):
    """[sound:0.mp3] -> '0.mp3'; empty/silent -> None."""
    if not audio_field:
        return None
    m = SOUND_RE.search(audio_field)
    if m:
        return m.group(1).strip()
    a = audio_field.strip()
    return a or None

def clean_en(back):
    """Back gloss -> a clean lowercase key. Deck backs are simple glosses ('doctor','wall');
    strip stray HTML and take the first sense before any comma/semicolon/slash so it matches the
    image slug (which is a single word)."""
    if not back:
        return ""
    s = re.sub(r"<[^>]+>", " ", back)          # strip any HTML
    s = re.sub(r"\s+", " ", s).strip()
    s = re.split(r"[;,/]", s)[0].strip()        # first sense only
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()  # drop trailing "(noun)/(food)/(color)" qualifier
    return _ALIAS.get(s.lower(), s.lower())

# Deck-specific gloss fixes (deck 1234275230): typos/variants -> canonical image slug.
_ALIAS = {"millk": "milk"}

# When two deck senses collapse to the same slug (e.g. "orange (food)" vs "orange (color)"),
# the app's first-match-wins lookup must prefer the concrete object. Push non-object
# qualifiers to the back so the image's real sense wins. Lower = preferred.
_QUAL_PENALTY = {"food":0, "noun":0, "animal":0, "fruit":0,
                 "color":5, "colour":5, "adjective":4, "adverb":4, "verb":3, "pronoun":4}

def _qual_penalty(back):
    if not back: return 1
    m = re.search(r"\(([^)]*)\)\s*$", back.strip())
    return _QUAL_PENALTY.get(m.group(1).strip().lower(), 1) if m else 0

def transform(notes):
    out = []
    for n in notes:
        f = n.get("fields", {}) or {}
        kana = (f.get("Front") or "").strip()
        en = clean_en(f.get("Back"))
        audio = extract_audio(f.get("Audio"))
        out.append({"id": n.get("id"), "kana": kana, "en": en, "audio": audio,
                    "_pen": _qual_penalty(f.get("Back"))})
    # stable-sort so the preferred sense of each colliding slug appears first (lookup table:
    # global order is irrelevant to card order, which is driven by images.json).
    out.sort(key=lambda w: w["_pen"])
    for w in out: del w["_pen"]
    return out

# ------------------------- self-test (no real deck needed) -------------------------
SYNTH = [
    {"id": 0, "fields": {"Front": "いぬ", "Audio": "[sound:0.mp3]", "Back": "dog"}, "tags": ""},
    {"id": 1, "fields": {"Front": "みず", "Audio": "[sound:1.mp3]", "Back": "water"}, "tags": ""},
    {"id": 2, "fields": {"Front": "しお", "Audio": "", "Back": "salt"}, "tags": ""},           # silent note
    {"id": 3, "fields": {"Front": "いしゃ", "Audio": "[sound:3.mp3]", "Back": "doctor, physician"}, "tags": ""},
    {"id": 4, "fields": {"Front": "たかい", "Audio": "[sound:4.mp3]", "Back": "<b>expensive</b>"}, "tags": ""},
    {"id": 5, "fields": {"Front": "さかな", "Audio": "[sound:さかな.mp3]", "Back": "fish (noun)"}, "tags": ""},   # kana-named audio + qualifier
    {"id": 6, "fields": {"Front": "オレンジいろ", "Audio": "[sound:オレンジいろ.mp3]", "Back": "orange (color)"}, "tags": ""},
    {"id": 7, "fields": {"Front": "オレンジ", "Audio": "[sound:オレンジ.mp3]", "Back": "orange (food)"}, "tags": ""},
]

def selftest():
    w = transform(SYNTH)
    byid = {x["id"]: x for x in w}
    assert byid[0] == {"id": 0, "kana": "いぬ", "en": "dog", "audio": "0.mp3"}, byid[0]
    assert byid[1]["audio"] == "1.mp3" and byid[1]["en"] == "water", byid[1]
    assert byid[2]["audio"] is None and byid[2]["en"] == "salt", byid[2]   # silent -> null audio
    assert byid[3]["en"] == "doctor", byid[3]                              # first sense only
    assert byid[4]["en"] == "expensive", byid[4]                           # HTML stripped
    # real-deck shapes: kana-named audio + parenthetical qualifiers (root-caused on deck-day 2026-07-23)
    assert byid[5]["en"] == "fish" and byid[5]["audio"] == "さかな.mp3", byid[5]   # "(noun)" stripped, kana audio
    # orange collision: (food) must win the slug over (color) via penalty reorder
    oranges = [x for x in w if x["en"] == "orange"]
    assert oranges and oranges[0]["kana"] == "オレンジ", oranges     # food sense first
    print("selftest: transform OK (7/7 cases)")
    # cross-check against the staged English list: do our cleaned glosses land in FF625?
    here = os.path.dirname(os.path.abspath(__file__))
    ff = os.path.join(here, "ff625-en.json")
    if os.path.exists(ff):
        ff_en = {clean_en(x["en"]) for x in json.load(open(ff))}
        hits = sum(1 for x in w if x["en"] in ff_en)
        print(f"selftest: {hits}/{len(w)} synthetic glosses match ff625-en.json "
              f"({sorted(x['en'] for x in w if x['en'] in ff_en)})")
    else:
        print("selftest: ff625-en.json not found — skipped cross-check")
    print("selftest: PASS")

def main():
    ap = argparse.ArgumentParser(description="Transform ankiweb notes.json -> app words.json")
    ap.add_argument("notes", nargs="?", help="path to notes.json (from ankiweb-deck-dl)")
    ap.add_argument("-o", "--out", default="words.json", help="output words.json path")
    ap.add_argument("--selftest", action="store_true", help="run built-in tests, no real deck needed")
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    if not a.notes:
        ap.error("notes.json path required (or use --selftest)")
    notes = json.load(open(a.notes))
    words = transform(notes)
    # report coverage against the staged English list
    here = os.path.dirname(os.path.abspath(__file__))
    ff = os.path.join(here, "ff625-en.json")
    n_audio = sum(1 for w in words if w["audio"])
    n_kana = sum(1 for w in words if w["kana"])
    print(f"transformed {len(words)} notes  |  kana:{n_kana}  audio:{n_audio}  "
          f"silent:{len(words)-n_audio}", file=sys.stderr)
    if os.path.exists(ff):
        ff_en = {clean_en(x["en"]) for x in json.load(open(ff))}
        matched = sum(1 for w in words if w["en"] in ff_en)
        print(f"ff625 gloss match: {matched}/{len(words)}", file=sys.stderr)
    json.dump(words, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {a.out} ({len(words)} words)", file=sys.stderr)

if __name__ == "__main__":
    main()

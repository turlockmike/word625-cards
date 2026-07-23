# word625-cards — build plan & findings

Rote-learn the **Fluent Forever 625 base words in Japanese** for Mike's kids.
Pedagogy (decided w/ Mike 2026-07-23): **picture on FRONT → produce kana + audio on BACK, NO English on the card.** FSRS scheduling, offline-first PWA, optional cloud-sync. Free content stack for v1.

Forked from `~/projects/kana-flashcards/` — reused plumbing verbatim: `fsrs.js`, `sw.js`, `sync.js`, `worker/` (Cloudflare KV sync), `manifest.json`, `DEPLOY.md`. NOT copied: kana.js / kanjivg / build_kana.py / kana app.js+index.html (kana-specific; this app's UI + content differ).

## AUTHORITATIVE DECK FINDING (2026-07-23, via AnkiWeb item-info API)

Deck **1234275230** = *"Fluent Forever Japanese (625 words) with audio"*. Derived from original deck 772529960; based on FF 625 list (fluent-forever.com/wp-content/uploads/2014/05/625-List-Alphabetical.pdf).

Note fields (confirmed from 3 sample notes):
| Field | Content | Example |
|---|---|---|
| `Front` | Japanese word (kana) | (非ASCII) |
| `Audio` | `[sound:N.mp3]` ref | `[sound:0.mp3]`, `[sound:1.mp3]`... |
| `Back` | English gloss | doctor, expensive, wall |
| `Tags` | — | |

**Media branch = PARTIAL:**
- ✅ **Audio IS bundled** — one mp3 per word, TTS/computer-generated. Author's own note: *"The audio is computer based... 8 of the vocab words were butchered so badly I left them silent. I will work on finding native speaker audio."* → usable for v1 but **VOICEVOX (correct pitch accent) is the quality upgrade** — still worth doing.
- ❌ **NO images** — no image field. Must source all ~625 (Wikimedia/Openverse for concrete nouns; Flux-schnell for abstract). This work is required regardless.
- ⚠️ **Orientation is kana→English (recognition)** — OPPOSITE of Mike's spec. We **remap**: picture→(kana+audio). The deck gives us the word list + audio, NOT a reusable card layout.

Net: deck yields **(a) the 625 kana↔English word list, (b) per-word audio mp3s**. We still build UI + images + orientation ourselves.

## REUSABLE CAPABILITY — AnkiWeb download without the desktop client

Modern AnkiWeb is a SvelteKit SPA over Connect-RPC svc endpoints. Getting deck metadata (no auth):
```
curl -sSL -G "https://ankiweb.net/svc/shared/item-info" --data-urlencode "sharedId=<DECKID>" -A "Mozilla/5.0"
```
→ HTTP 200, **Connect protobuf** (octet-stream) containing title, description, reviews, `sample_notes` (field names + example values), and a `download_key` (JWT `{"op":"sdd",...}`). `strings -n 2` on the response reveals fields + sample notes directly.

**SOLVED (2026-07-23):** the web download endpoint is `GET /svc/shared/download-deck/<id>?t=<download_key>` (param is `t=`, decoded from SvelteKit `nodes/25.*.mjs`). Fully wrapped in the reusable tool **`ankiweb-deck-dl`** (`~/.local/bin/`, validated end-to-end on a synthetic apkg): `ankiweb-deck-dl 1234275230 --out data/` → `notes.json` (`[{id, fields:{Front,Audio,Back}, tags}]`) + `media/*.mp3`. **Only remaining gate:** the anonymous per-IP daily download quota (currently spent → HTTP 429 "Please log in to download more decks"). Get the apkg by either (a) retry the one-command tool after the daily quota reset, or (b) log in to an AnkiWeb account (free; agentmail verify) and pass `--cookies session.txt`. Recipe detail: `~/resources/infrastructure/ankiweb-shared-deck-fetch.md`.

**Reconstruction fallback (no AnkiWeb):** `data/ff625-en.json` (619 words + 26 categories, parsed from honza/fluent-forever-625) + jisho.org API for kana. CAVEAT: jisho's top hit is NOT reliably the FF-canonical word (e.g. "water"→水分 not 水; "dog"→junk top hit) — needs exact-english-match + common-tag curation. Prefer the authoritative apkg for kana correctness (kids' app).

## PIPELINE (v1, free stack)
1. **Word list** — obtain 625 kana↔English (from apkg once downloadable, else reconstruct). LOCK as `words.json` `[{id, kana, en, audio}]`.
2. **Audio** — v1: reuse bundled mp3s if apkg obtained; QUALITY pass: VOICEVOX local batch-gen (correct pitch accent) — `voicevox` not yet installed (`which voicevox` empty).
3. **Images** — two-tier: concrete nouns → Wikimedia Commons / Openverse (real photos, FF-recommended); abstract → Flux-schnell (HF, free). ~625 total; source in batches, NOT one window.
4. **UI** — fork kana app.js/index.html shape; card = image front → tap → kana + audio + (optional) English hint. Wire FSRS + offline SW + optional sync.
5. **Deploy** — GitHub Pages (same pattern as kana-cards → turlockmike.github.io).

## STATUS (2026-07-23 ~12:30 CDT) — ✅ SHIPPED WITH DECK
**App is LIVE with real content: https://turlockmike.github.io/word625-cards/** (commit `f5a3b89`).
Deck 1234275230 pulled via the AnkiWeb **account path** (signup→confirm-terms→verify-email, no captcha;
recipe now in `~/resources/infrastructure/ankiweb-shared-deck-fetch.md`). `notes.json` (595 notes,
fields Front=kana/Audio=`[sound:<kana>.mp3]`/Back=en) → `words.json` (595) → **44/44 ok-image cards
merge to image+kana+audio**, verified locally + live (words.json 200, audio mp3 `audio/mp3` 200).
Transform hardened: strips `(noun)/(food)/(color)` qualifiers, prefers concrete sense on slug collision
(orange food>color), aliases deck typo `millk→milk`; 7/7 selftest. Audio is **kana-named**, not `N.mp3`
(BUILD's earlier assumption) — the `[sound:...]` regex handled it. Deck-day bug root-caused + fixed:
`ankiweb-deck-dl` download_key was over-read by a greedy regex (protobuf LEN prefix ignored) → HTTP 400.
**Residual (non-blocking):** `oil`, `sugar` = 2/46 images absent in OpenMoji → 44 cards v1; VOICEVOX
pitch-accent audio = post-ship quality upgrade; photoreal image-gen = Mike-actionable (stale keys).

## STATUS (2026-07-23 ~03:36 CDT)
- Plumbing forked. Media branch decided. **AnkiWeb download endpoint CRACKED + tool built (`ankiweb-deck-dl`, validated).** English list staged (`data/ff625-en.json`, 619 words). Only the anon download quota blocks the final apkg pull.
- **Next chunk:** run `ankiweb-deck-dl 1234275230 --out data/` (it's a ~2s call — succeeds the moment the anon quota resets; if still 429 after ~24h, register an AnkiWeb account via agentmail + `--cookies`). Then transform `notes.json` → `words.json` `[{id,kana,en,audio}]` (Front=kana, Back=en, Audio=mp3 ref), stage `media/` mp3s. THEN start ONE downstream batch (VOICEVOX install OR first image batch). Never 625 in one window.

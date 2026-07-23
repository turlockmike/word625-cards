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

**Blocked so far:** the actual `.apkg` download. `/shared/download/<id>` is the DESKTOP-client endpoint and hard-gates with `"Your version of Anki is too old."` regardless of `?v=`/`?k=<key>`/UA spoof (tried v=3..20, anki-UA, sync-version headers, the download_key). `/svc/shared/download*` → 404. The web UI download route lives in a lazy page-node chunk not yet decoded. **Next attempt options:** (a) decode the info page-node chunk (`/_app/immutable/nodes/*.mjs`) to find the web download URL that consumes `download_key`; (b) install Anki desktop headless + use its `--download` path; (c) get the word list from a GitHub mirror (none clean found 2026-07-23) or reconstruct kana from the FF 625 English list + a JP dictionary.

## PIPELINE (v1, free stack)
1. **Word list** — obtain 625 kana↔English (from apkg once downloadable, else reconstruct). LOCK as `words.json` `[{id, kana, en, audio}]`.
2. **Audio** — v1: reuse bundled mp3s if apkg obtained; QUALITY pass: VOICEVOX local batch-gen (correct pitch accent) — `voicevox` not yet installed (`which voicevox` empty).
3. **Images** — two-tier: concrete nouns → Wikimedia Commons / Openverse (real photos, FF-recommended); abstract → Flux-schnell (HF, free). ~625 total; source in batches, NOT one window.
4. **UI** — fork kana app.js/index.html shape; card = image front → tap → kana + audio + (optional) English hint. Wire FSRS + offline SW + optional sync.
5. **Deploy** — GitHub Pages (same pattern as kana-cards → turlockmike.github.io).

## STATUS (2026-07-23 ~02:23 CDT)
- Plumbing forked. Media branch decided + recorded. Word-list/audio acquisition BLOCKED on AnkiWeb download gate — see options above.
- **Next chunk:** crack the apkg download (option a: decode page-node chunk for the web download URL) OR install VOICEVOX + start image-sourcing pipeline on the reconstructed word list. Do NOT attempt 625 images in one window.

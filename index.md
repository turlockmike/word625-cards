# word625-cards — project loop

**Goal (mission Pillar 3):** a Fluent-Forever-625 Japanese vocabulary app for Mike's kids — rote-learn 625 base words, **picture-front → produce kana + audio on back, NO English on the card** (pedagogy decided with Mike 2026-07-23). Offline-first PWA, FSRS scheduling, optional cloud-sync. Sibling to the shipped `kana-cards`; assists Mike's family life.

**Status:** 🔨 ACTIVE BUILD (multi-window) — started 2026-07-23.
- Local working copy: `~/projects/word625-cards/`. Committed `f062870`.
- Plumbing FORKED verbatim from `~/projects/kana-flashcards/`: `fsrs.js`, `sw.js`, `sync.js`, `worker/` (Cloudflare KV sync), `manifest.json`, `DEPLOY.md`. NOT copied: kana-specific UI/content.
- Source deck **1234275230** (AnkiWeb, "Fluent Forever Japanese 625 w/ audio") inventoried → branch = **media-partial**: audio bundled (TTS mp3s), NO images, orientation kana→English (opposite of spec → we remap).
- **AnkiWeb download endpoint CRACKED + reusable tool built** (`ankiweb-deck-dl`, validated end-to-end on synthetic apkg). Only the anon per-IP daily download quota blocks the final `.apkg` pull.
- Staged: `data/ff625-en.json` (619 words + 26 categories, honza/fluent-forever-625) = reconstruction/validation asset.

## Success criteria (how I know this project won)
- [ ] `words.json` locked — `[{id, kana, en, audio}]` ~625 rows, committed.
- [ ] Audio staged — bundled mp3s (v1) and/or VOICEVOX batch (quality pass, correct pitch accent).
- [ ] Images sourced ~625 in BATCHES (Wikimedia/Openverse concrete + Flux-schnell abstract). **Never 625 in one window.**
- [ ] UI: image-front → tap → kana + audio (+ optional English hint), FSRS + offline SW + optional sync wired.
- [ ] Deployed to GitHub Pages (turlockmike.github.io pattern), link reported to Mike.
- [ ] **Kids actually use it** — real usage / Mike's feedback (Tier-3, awaits kids trying it).

## Kill / done criteria
- **DONE** when the app is live, kids can learn the 625 words picture→kana+audio, and progress persists.
- **KILL** only if Mike says the kids won't use it / abandons the idea. No sunk-cost grind.

## Open / next action
1. **[deck — deferred to quota reset]** run `ankiweb-deck-dl 1234275230 --out data/` as the
   **FIRST network request of a fresh quota-day** (anon per-IP daily download quota was spent
   by my own probing 2026-07-23; it resets daily — a clean early attempt next day pulls the
   real `.apkg`). Do NOT probe-then-download (that re-exhausts it). If it must unblock sooner,
   register a free AnkiWeb account (agentmail verify) + `--cookies session.txt`. The deck gives
   authoritative kana + bundled TTS mp3s → transform `notes.json`→`words.json`.
   **jisho reconstruction is RULED OUT for kana** (tested 2026-07-23): even exact-english-match +
   is_common weighting gives ~15-20% wrong on CORE words (dog→トックリ形, water→水分, man→マン,
   rice→米穀) — jisho keyword ranking ≠ "most basic word for the concept". Use the curated deck.
2. **[IMAGES — STARTED 2026-07-23]** first batch DONE: 46 concrete nouns (Animal/Food/Beverages)
   via new tool **`img-source`** (Openverse CC0/PDM, `category=photograph`) → `media/img/*.jpg`
   + `media/img/images.json` manifest (each entry carries top-6 **candidate URLs** for curation).
   NEXT: (a) **vision-curation pass** — most top-1 picks are right, but ambiguous/brand-collision
   words need re-pick from candidates (e.g. apple→#0 "Apple Core Nebula" is WRONG; correct is
   candidate #5 "Apples"). Curation = View each candidate, set `chosen` index, re-point `file`.
   (b) continue batches for remaining concrete cats (Body/Home/Nature/Transportation/Clothing/
   Electronics/Art) via `img-source --categories ...` (resumable, skips done). Abstract ~20%
   (Verbs/Adjectives/Directions) → Flux-schnell later. **Never 625 in one window.**
3. Then: words.json lock (deck) → wire content → UI fork (image-front → kana+audio) → Pages
   deploy → report link to Mike. Offer uniform-art OpenRouter upgrade (~$5-10) after v1 ships.

## Loop discipline
Active build lane — heartbeats/workshop MAY advance it (one well-scoped chunk per window). Method + gate detail: `BUILD.md` + `~/resources/infrastructure/ankiweb-shared-deck-fetch.md`. Reusable AnkiWeb-fetch capability = `ankiweb-deck-dl`. Same `offline-first-pwa-sync.md` footguns apply as kana-cards.

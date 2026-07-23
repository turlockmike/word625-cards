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
- [ ] Images sourced ~625 in BATCHES. **Source SPLITS by word type (measured 2026-07-23):** Openverse photos for concrete-distinctive nouns ONLY (~24% top-1 kids-OK league-wide, but works for dog/cat/lemon/soup); **emoji/illustration set (OpenMoji CC-BY-SA / Twemoji) for common+abstract nouns** — the Openverse candidate POOL (all 6) is unusable for those (apple/milk/coffee/food return people/landscapes/brand-signs, correct image ABSENT). Optional photorealistic-generation upgrade later (`img` Gemini/OpenRouter, credential-gated). **Never 625 in one window.**
- [x] **UI SHELL BUILT 2026-07-23** (`887534a`): image-front → tap → kana + audio + English hint, FSRS + offline SW + profile select/create + backup/restore + optional sync all wired. `app.js`+`index.html` forked from kana-flashcards, drops stroke/draw. Renders 44 status=ok cards from `images.json`; kana/audio STUBBED with a clear placeholder until `words.json` (deck) lands — it auto-fills the instant `data/words.json` appears (matched by `en`/slug), no code change. Verified: node --check all JS; merge logic vs real `images.json` (44 cards, all image files present, kana null→populates w/ synthetic deck); localhost static-serve all paths 200. **UNVERIFIED here:** actual browser render (no browser/net) → confirm on Pages deploy.
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
2. **[IMAGES — STARTED 2026-07-23, curation pass DONE + strategy FLIPPED]** first batch = 46
   concrete nouns (Animal/Food/Beverages) via **`img-source`** (Openverse) → `media/img/` +
   `images.json` manifest. **Vision-curation pass DONE 2026-07-23** (via new tool
   **`img-contactsheet`** = tiles a manifest into ONE labeled grid PNG, whole batch triaged in a
   single Read): all 46 annotated `status: ok|needs-alt` → **only 12 ok / 34 needs-alt**.
   **MEASURED: top-1 Openverse ~24% kids-acceptable** (not the docstring's old ~70-85% guess) —
   concrete distinctive objects work (dog/cat/lemon/soup), abstract/common/homonym nouns fail
   (pig→helicopter, apple→corn, milk→lake). **CRUX tested + strategy flipped:** for abstract
   nouns the ENTIRE 6-candidate pool is off-canon (people/landscapes/war/brand-signs) → re-pointing
   `chosen` CANNOT rescue them; salvaged only `water`→#5. So curation-within-pool is DEAD for
   common nouns — they need an ALTERNATIVE SOURCE.
   **EMOJI CHUNK DONE 2026-07-23** (heartbeat): built reusable **`emoji-source`** (OpenMoji
   CC-BY-SA; curated kid-clarity hexcode map + exact-annotation/tag fallback; `--plan-out`+`--apply`
   split for sandboxed-network envs). Ran over the 34 needs-alt → **32/34 (94%) now have a clean
   kid-friendly emoji**, contact-sheet Read-verified (apple=🍎 red apple not the Apple logo, pig/
   horse/chicken faces, bacon=pork, 🥩=beef, bento=lunch, spaghetti=dinner, 🧂=salt). Manifest now
   **44 ok / 2 needs-alt**. ONLY residuals: **`oil`** (no glyph — OpenMoji has only an industrial
   drum) + **`sugar`** (only a cupcake) — genuinely absent, left needs-alt (acceptable: 2/625, revisit
   with photoreal-gen or a hand-drawn pair later). Attribution shipped: `media/img/NOTICE`.
   Keep `img-source` (Openverse) ONLY for concrete-distinctive nouns going forward.
   *(Alt/optional: photorealistic generation via `img` = Gemini/OpenRouter — BLOCKED 2026-07-23:
   Gemini key invalid (stale from Apr 7) + OpenRouter out of credits (402). MIKE-ACTIONABLE if he
   wants photoreal over emoji — refresh Gemini key or add OpenRouter credits. Not on critical path;
   emoji unblocks v1 without it.)* **Never 625 in one window.**
3. Then: words.json lock (deck) → wire content → UI fork (image-front → kana+audio) → Pages
   deploy → report link to Mike. Offer uniform-art OpenRouter upgrade (~$5-10) after v1 ships.

## Loop discipline
Active build lane — heartbeats/workshop MAY advance it (one well-scoped chunk per window). Method + gate detail: `BUILD.md` + `~/resources/infrastructure/ankiweb-shared-deck-fetch.md`. Reusable AnkiWeb-fetch capability = `ankiweb-deck-dl`. Same `offline-first-pwa-sync.md` footguns apply as kana-cards.

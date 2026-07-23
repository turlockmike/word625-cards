#!/usr/bin/env python3
"""build-artifact.py — render the bake-off results into a self-contained HTML page.

Reads results.tsv + costs.txt + img/, downscales every image to <=320px,
embeds as base64 JPEG data URIs, and writes bakeoff.html ready for the
Artifact tool. Self-contained by design: the Artifact CSP blocks all
external requests.
"""
import base64
import io
import json
from pathlib import Path

from PIL import Image

DIR = Path.home() / "projects/word625-cards/bakeoff"
IMG = DIR / "img"
OUT = DIR / "bakeoff.html"

WORDS = ["fork", "dog", "mother", "friend", "oil", "sugar", "idea", "north", "red", "three"]
MODEL_META = {
    "nano-lite": ("Gemini 3.1 Flash Lite", "nano-lite"),
    "nano-2": ("Gemini 3.1 Flash", "nano-2"),
    "nano": ("Gemini 2.5 Flash", "nano"),
    "nano-pro": ("Gemini 3 Pro", "nano-pro"),
    "openai/gpt-5-image-mini": ("GPT-5 Image Mini", "openai--gpt-5-image-mini"),
}

# ---- parse results.tsv ----
rows = {}  # (model, word) -> dict
model_secs = {}
for line in (DIR / "results.tsv").read_text().splitlines()[1:]:
    model, word, fname, secs, status = line.split("\t")
    rows[(model, word)] = {"file": fname, "secs": int(secs), "ok": status == "ok"}
    model_secs.setdefault(model, []).append(int(secs))

# ---- parse costs.txt for real per-model deltas ----
model_cost = {}
for line in (DIR / "costs.txt").read_text().splitlines():
    if ": before=" in line:
        model, rest = line.split(": before=")
        before, after = rest.split(" after=")
        model_cost[model] = float(before) - float(after)

# ---- embed images ----
def data_uri(path, max_dim=320):
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

cells_html = []
for word in WORDS:
    tds = [f'<th scope="row" class="word">{word}</th>']
    for model in MODEL_META:
        r = rows.get((model, word))
        if r and r["ok"] and (IMG / r["file"]).exists():
            uri = data_uri(IMG / r["file"])
            label = f"{MODEL_META[model][0]} — {word}"
            tds.append(
                f'<td><button class="cell" data-label="{label}">'
                f'<img src="{uri}" alt="{label}" loading="lazy"></button>'
                f'<span class="secs">{r["secs"]}s</span></td>'
            )
        else:
            tds.append('<td><div class="fail">failed</div></td>')
    cells_html.append("<tr>" + "".join(tds) + "</tr>")

# ---- per-model stat header ----
GAP = 542  # words still missing an image (word625-gen-images --dry-run, 2026-07-23)

def stat_block(model):
    name, _ = MODEL_META[model]
    ok = sum(1 for w in WORDS if rows.get((model, w), {}).get("ok"))
    secs = model_secs.get(model, [0])
    cost = model_cost.get(model)
    n_gen = 11 if model == "nano-pro" else ok  # nano-pro billed one extra (dog retry)
    rate = cost / n_gen if cost is not None and n_gen else None
    per_img = f"${rate:.3f}" if rate else "—"
    full = f"${rate * GAP:.2f}" if rate else "—"
    avg = f"{sum(secs) / len(secs):.0f}s"
    okcls = "good" if ok == len(WORDS) else "warn"
    return (
        f'<th scope="col"><div class="mname">{name}</div>'
        f'<div class="mstats"><span class="stat">{per_img}<em>/img</em></span>'
        f'<span class="stat full">{full}<em>full deck</em></span>'
        f'<span class="stat">{avg}<em>avg</em></span>'
        f'<span class="stat {okcls}">{ok}/{len(WORDS)}<em>ok</em></span></div></th>'
    )

header_html = '<th scope="col" class="word-col">word</th>' + "".join(
    stat_block(m) for m in MODEL_META
)

# ---- Round 2: Japanese-anchored prompts (nano-lite), generic vs anchored ----
JP_WORDS = [
    ("fork", "フォーク", "fōku"), ("dog", "いぬ", "inu"),
    ("mother", "おかあさん", "okaasan"), ("friend", "ともだち", "tomodachi"),
    ("oil", "せきゆ", "sekiyu — kerosene!"), ("sugar", "さとう", "satou"),
    ("north", "きた", "kita"), ("red", "あかい", "akai"),
    ("three", "さん", "san"), ("rice", "こめ", "kome"),
]
IMG_JP = DIR / "img-jp"
jp_rows_html = []
jp_results = {}
jp_tsv = DIR / "results-jp.tsv"
if jp_tsv.exists():
    for line in jp_tsv.read_text().splitlines()[1:]:
        word, fname, secs, status = line.split("\t")
        jp_results[word] = {"file": fname, "secs": int(secs), "ok": status == "ok"}

def img_cell(path, label, secs=None):
    if path and path.exists():
        uri = data_uri(path)
        s = f'<span class="secs">{secs}s</span>' if secs is not None else ""
        return (
            f'<td><button class="cell" data-label="{label}">'
            f'<img src="{uri}" alt="{label}" loading="lazy"></button>{s}</td>'
        )
    return '<td><div class="fail">—</div></td>'

for en, kana, romaji in JP_WORDS:
    r1 = rows.get(("nano-lite", en))
    r1_path = IMG / r1["file"] if r1 and r1.get("ok") else None
    r2 = jp_results.get(en)
    r2_path = IMG_JP / r2["file"] if r2 and r2.get("ok") else None
    jp_rows_html.append(
        "<tr>"
        f'<th scope="row" class="word"><span class="kana">{kana}</span>'
        f'<span class="romaji">{romaji}</span></th>'
        + img_cell(r1_path, f"Round 1 generic — {en}")
        + img_cell(r2_path, f"Round 2 Japanese-anchored — {kana} ({romaji})",
                   r2["secs"] if r2 else None)
        + "</tr>"
    )

jp_cost = model_cost.get("round2-jp")
jp_cost_str = f"${jp_cost:.2f}" if jp_cost is not None else "—"

start = end = None
for line in (DIR / "costs.txt").read_text().splitlines():
    if line.startswith("start_balance="):
        start = float(line.split("=")[1])
    if line.startswith("end_balance="):
        end = float(line.split("=")[1])
spent = f"${start - end:.2f}" if start and end else "—"

html = """<title>Image Model Bake-off — word625</title>
<style>
:root {
  --ground: #FAFAF7; --panel: #FFFFFF; --ink: #21252E; --muted: #6E7480;
  --line: #E4E4DC; --accent: #2E7DAB; --good: #2C8A4B; --bad: #C24A3F;
  --shadow: 0 1px 3px rgba(30,35,45,.08);
}
@media (prefers-color-scheme: dark) { :root {
  --ground: #191C22; --panel: #21252E; --ink: #E8E9EB; --muted: #9AA0AB;
  --line: #32363F; --accent: #5FA8D3; --good: #57B87A; --bad: #E07A6F;
  --shadow: 0 1px 3px rgba(0,0,0,.4);
} }
:root[data-theme="light"] {
  --ground: #FAFAF7; --panel: #FFFFFF; --ink: #21252E; --muted: #6E7480;
  --line: #E4E4DC; --accent: #2E7DAB; --good: #2C8A4B; --bad: #C24A3F;
  --shadow: 0 1px 3px rgba(30,35,45,.08);
}
:root[data-theme="dark"] {
  --ground: #191C22; --panel: #21252E; --ink: #E8E9EB; --muted: #9AA0AB;
  --line: #32363F; --accent: #5FA8D3; --good: #57B87A; --bad: #E07A6F;
  --shadow: 0 1px 3px rgba(0,0,0,.4);
}
* { box-sizing: border-box; }
body { background: var(--ground); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
  margin: 0; padding: 2rem 1.5rem 4rem; }
header.page { max-width: 1200px; margin: 0 auto 1.5rem; }
h1 { font-size: 1.5rem; font-weight: 650; margin: 0 0 .25rem; text-wrap: balance; }
.sub { color: var(--muted); margin: 0; }
.sub strong { color: var(--ink); font-weight: 600; }
.table-wrap { max-width: 1200px; margin: 0 auto; overflow-x: auto;
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  box-shadow: var(--shadow); }
table { border-collapse: collapse; width: 100%; min-width: 860px; }
thead th { position: sticky; top: 0; background: var(--panel); z-index: 2;
  padding: .8rem .6rem .6rem; border-bottom: 2px solid var(--line);
  text-align: center; vertical-align: bottom; }
.word-col { width: 5.5rem; }
.mname { font-weight: 650; font-size: .95rem; }
.mstats { display: flex; gap: .6rem; justify-content: center; margin-top: .3rem;
  flex-wrap: wrap; }
.stat { font-variant-numeric: tabular-nums; font-size: .78rem; color: var(--ink);
  font-weight: 600; }
.stat em { font-style: normal; color: var(--muted); font-weight: 400;
  margin-left: .15rem; }
.stat.good { color: var(--good); } .stat.warn { color: var(--bad); }
.stat.full { color: var(--accent); font-size: .85rem; }
tbody th.word { text-align: right; padding: .5rem .8rem; font-weight: 600;
  color: var(--muted); text-transform: uppercase; letter-spacing: .05em;
  font-size: .78rem; border-bottom: 1px solid var(--line); }
tbody td { padding: .45rem; border-bottom: 1px solid var(--line);
  text-align: center; vertical-align: middle; }
tbody tr:last-child td, tbody tr:last-child th { border-bottom: none; }
.cell { border: 1px solid var(--line); border-radius: 6px; padding: 0;
  background: none; cursor: zoom-in; display: block; margin: 0 auto;
  line-height: 0; overflow: hidden; }
.cell:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.cell img { width: 150px; height: 150px; object-fit: contain; background: #fff;
  display: block; }
.secs { display: block; font-size: .7rem; color: var(--muted);
  font-variant-numeric: tabular-nums; margin-top: .2rem; }
.fail { width: 150px; height: 150px; margin: 0 auto; display: flex;
  align-items: center; justify-content: center; border: 1px dashed var(--bad);
  border-radius: 6px; color: var(--bad); font-size: .8rem; }
dialog { border: none; border-radius: 10px; padding: 0; background: var(--panel);
  box-shadow: 0 8px 40px rgba(0,0,0,.35); max-width: min(92vw, 640px); }
dialog::backdrop { background: rgba(10,12,16,.55); }
dialog img { width: 100%; display: block; background: #fff; }
dialog p { margin: 0; padding: .6rem .9rem; color: var(--muted); font-size: .85rem; }
.note { max-width: 1200px; margin: 1rem auto 0; color: var(--muted);
  font-size: .85rem; }
header.round2 { margin-top: 3rem; }
.table-wrap.narrow { max-width: 760px; }
.table-wrap.narrow table { min-width: 0; }
.table-wrap.narrow .cell img { width: 220px; height: 220px; }
.kana { display: block; font-size: 1.15rem; font-weight: 650; color: var(--ink);
  text-transform: none; letter-spacing: 0; }
.romaji { display: block; font-size: .72rem; color: var(--muted);
  text-transform: none; letter-spacing: .02em; font-weight: 400; }
</style>
<header class="page">
  <h1>Image model bake-off — 10 words &times; 5 models</h1>
  <p class="sub">Same prompt per word, one style spec, run __DATE__ via OpenRouter.
  Bake-off spent <strong>__SPENT__</strong>. $/img is measured from real balance
  deltas; <strong>full deck</strong> = that rate &times; the 542 words still
  missing an image (estimate). Times are wall-clock per image. Click any image
  to zoom.</p>
</header>
<div class="table-wrap"><table>
  <thead><tr>__HEADER__</tr></thead>
  <tbody>__ROWS__</tbody>
</table></div>
<p class="note">Prompt template: &ldquo;Simple friendly flat illustration clearly
representing the concept &lsquo;&lt;word&gt;&rsquo;, for a young child's vocabulary
flashcard. Single clear subject, bold outlines, bright cheerful colors, plain
white background, no text or letters.&rdquo; Words chosen to stress-test: easy
concretes (fork, dog), people (mother, friend), the two OpenMoji failures
(oil, sugar), and abstracts (idea, north, red, three).</p>

<header class="page round2">
  <h1>Round 2 — Japanese-anchored prompts (Flash Lite)</h1>
  <p class="sub">Same winning model, but each prompt now leads with the
  <strong>Japanese word</strong> and a Japanese cultural anchor &mdash; いぬ is a
  Shiba Inu, さん is three onigiri &mdash; so the word binds to Japanese imagery,
  not to an English translation. Cost: <strong>__JPCOST__</strong>.
  Note: the deck's &ldquo;oil&rdquo; is せきゆ = <em>kerosene</em>, so its image is
  the red kerosene tank + winter heater, not cooking oil. &ldquo;idea&rdquo; is not
  a deck word and was replaced with こめ (rice).</p>
</header>
<div class="table-wrap narrow"><table>
  <thead><tr><th scope="col" class="word-col">word</th>
  <th scope="col"><div class="mname">Round 1 — generic</div></th>
  <th scope="col"><div class="mname">Round 2 — Japanese-anchored</div></th></tr></thead>
  <tbody>__JPROWS__</tbody>
</table></div>
<dialog id="zoom"><img id="zoom-img" alt=""><p id="zoom-cap"></p></dialog>
<script>
const dlg = document.getElementById('zoom');
const zi = document.getElementById('zoom-img');
const zc = document.getElementById('zoom-cap');
document.querySelectorAll('.cell').forEach(btn => {
  btn.addEventListener('click', () => {
    zi.src = btn.querySelector('img').src;
    zi.alt = zc.textContent = btn.dataset.label;
    dlg.showModal();
  });
});
dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
</script>
"""

html = (
    html.replace("__HEADER__", header_html)
    .replace("__ROWS__", "\n".join(cells_html))
    .replace("__JPROWS__", "\n".join(jp_rows_html))
    .replace("__JPCOST__", jp_cost_str)
    .replace("__SPENT__", spent)
    .replace("__DATE__", "2026-07-23")
)
OUT.write_text(html)
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")

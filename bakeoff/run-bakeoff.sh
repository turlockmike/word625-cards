#!/bin/bash
# run-bakeoff.sh — 10-word image-model bake-off for word625-cards
# 5 models x 10 words via image-gen (OpenRouter backend), sequential per
# model so openrouter-credits deltas give REAL per-model cost.
set -u
DIR="$HOME/projects/word625-cards/bakeoff"
IMG="$DIR/img"
LOG="$DIR/results.tsv"
mkdir -p "$IMG"

WORDS=(fork dog mother friend oil sugar idea north red three)
MODELS=(nano-lite nano-2 nano nano-pro "openai/gpt-5-image-mini")

prompt_for() {
  echo "Simple friendly flat illustration clearly representing the concept \"$1\", for a young child's vocabulary flashcard. Single clear subject, bold outlines, bright cheerful colors, plain white background, no text or letters."
}

credits() { openrouter-credits --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('remaining', d))"; }

echo -e "model\tword\tfile\tseconds\tstatus" > "$LOG"
echo "start_balance=$(credits)" > "$DIR/costs.txt"

for model in "${MODELS[@]}"; do
  safe_model=$(echo "$model" | tr '/.' '--')
  before=$(credits)
  for word in "${WORDS[@]}"; do
    t0=$SECONDS
    out=$(image-gen "$(prompt_for "$word")" --backend openrouter --model "$model" --no-fallback 2>&1)
    dt=$((SECONDS - t0))
    saved=$(echo "$out" | grep -oP '(?<=Saved: ).*')
    if [ -n "$saved" ] && [ -f "$saved" ]; then
      ext="${saved##*.}"
      cp "$saved" "$IMG/${safe_model}__${word}.${ext}"
      echo -e "${model}\t${word}\t${safe_model}__${word}.${ext}\t${dt}\tok" >> "$LOG"
    else
      echo -e "${model}\t${word}\t-\t${dt}\tFAIL" >> "$LOG"
      echo "FAIL ${model}/${word}: $out" >> "$DIR/errors.log"
    fi
  done
  after=$(credits)
  echo "${model}: before=${before} after=${after}" >> "$DIR/costs.txt"
done

echo "end_balance=$(credits)" >> "$DIR/costs.txt"
echo "DONE"

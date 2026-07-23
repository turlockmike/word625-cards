#!/bin/bash
# run-round2-jp.sh — Round 2: nano-lite only, Japanese-culturally-anchored prompts.
# Goal (Mike, 2026-07-23): bind the JAPANESE word to Japanese imagery so the
# learner connects いぬ→Shiba, not dog→translation. No text in images.
set -u
DIR="$HOME/projects/word625-cards/bakeoff"
IMG="$DIR/img-jp"
LOG="$DIR/results-jp.tsv"
mkdir -p "$IMG"

STYLE="Simple friendly flat illustration for a young child's Japanese vocabulary flashcard. Single clear subject, bold outlines, bright cheerful colors, plain white background, absolutely no text, letters, or characters in the image."

declare -A PROMPTS=(
  [fork]="The Japanese word 'fōku' (フォーク, fork). A shiny fork twirling napolitan spaghetti on a Japanese yōshoku restaurant plate. $STYLE"
  [dog]="The Japanese word 'inu' (dog). A cheerful Shiba Inu dog with a curled tail and a red collar, sitting proudly. $STYLE"
  [mother]="The Japanese word 'okaasan' (mother). A warm smiling Japanese mother in an apron hugging her small child. $STYLE"
  [friend]="The Japanese word 'tomodachi' (friend). Two happy Japanese children walking together with school randoseru backpacks. $STYLE"
  [oil]="The Japanese word 'sekiyu' (petroleum/kerosene). The classic red plastic Japanese kerosene tank next to a small winter kerosene heater with a warm glow. $STYLE"
  [sugar]="The Japanese word 'satou' (sugar). A small white sugar jar with sugar cubes beside a cup of Japanese green tea. $STYLE"
  [north]="The Japanese word 'kita' (north). A compass with the needle pointing up toward snowy mountains and a snowflake, evoking Hokkaido in winter. $STYLE"
  [red]="The Japanese word 'akai' (red). A bright red daruma doll next to a red torii gate, everything vividly red. $STYLE"
  [three]="The Japanese word 'san' (three). Exactly three onigiri rice balls with nori strips, lined up in a row. $STYLE"
  [rice]="The Japanese word 'kome' (rice). A steaming white bowl of Japanese rice with chopsticks resting beside it. $STYLE"
)

WORDS=(fork dog mother friend oil sugar north red three rice)

credits() { openrouter-credits --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['remaining'])"; }

echo -e "word\tfile\tseconds\tstatus" > "$LOG"
before=$(credits)

for word in "${WORDS[@]}"; do
  t0=$SECONDS
  out=$(image-gen "${PROMPTS[$word]}" --backend openrouter --model nano-lite --no-fallback 2>&1)
  dt=$((SECONDS - t0))
  saved=$(echo "$out" | grep -oP '(?<=Saved: ).*')
  if [ -n "$saved" ] && [ -f "$saved" ]; then
    ext="${saved##*.}"
    cp "$saved" "$IMG/${word}.${ext}"
    echo -e "${word}\t${word}.${ext}\t${dt}\tok" >> "$LOG"
  else
    echo -e "${word}\t-\t${dt}\tFAIL" >> "$LOG"
    echo "FAIL ${word}: $out" >> "$DIR/errors-jp.log"
  fi
done

after=$(credits)
echo "round2-jp: before=${before} after=${after}" >> "$DIR/costs.txt"
echo "DONE"

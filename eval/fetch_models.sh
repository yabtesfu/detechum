#!/usr/bin/env bash
# Download the pinned model files used by eval/bias_experiment.py into data/external/models.
# Uses plain HTTP with resume, because the hub client's chunked transfer can fail on unstable
# connections without keeping partial progress.
set -euo pipefail

DEST="${1:-data/external/models}"

fetch() {
  local repo="$1" rev="$2" name="$3"; shift 3
  for file in "$@"; do
    local out="$DEST/$name/$file"
    if [[ -f "$out.done" ]]; then continue; fi
    mkdir -p "$(dirname "$out")"
    echo "fetching $repo@$rev $file"
    # A stalled transfer never errors on its own, so abort below 1 KB/s for 60 s. The caller reruns
    # this script, and -C - resumes from the bytes already on disk with a freshly signed redirect.
    curl -fL --retry 3 --retry-all-errors --retry-delay 10 --speed-limit 1024 --speed-time 60 -C - \
      -o "$out" "https://huggingface.co/$repo/resolve/$rev/$file"
    touch "$out.done"
  done
}

fetch nakas/gpttrace-v8s-1b ac748e32ca8c90bb8858fadc427757728e27b063 gpttrace-v8s-1b \
  normalize.py model/config.json model/tokenizer.json model/tokenizer_config.json model/model.safetensors

QWEN_FILES=(config.json generation_config.json merges.txt vocab.json tokenizer.json tokenizer_config.json model.safetensors)
fetch Qwen/Qwen2.5-1.5B 8faed761d45a263340a0528343f099c05c9a4323 qwen2.5-1.5b "${QWEN_FILES[@]}"
fetch Qwen/Qwen2.5-1.5B-Instruct 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 qwen2.5-1.5b-instruct "${QWEN_FILES[@]}"
echo "all model files downloaded"

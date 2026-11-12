#!/bin/bash
# Run once after unzipping: points every hard-coded path at this folder.
cd "$(dirname "$0")"; ROOT="$PWD/work"
grep -rl "/workspace/work" work | xargs sed -i "s#/workspace/work#$ROOT#g"
pip install pillow requests numpy >/dev/null 2>&1
which ffmpeg >/dev/null || echo "Install ffmpeg first (apt install ffmpeg)."
echo "Paths fixed to $ROOT. Set AI33_KEY env var before running gen_vo.py."

#!/bin/bash
git clean -fd
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
log_dir="homescreen"
for f in "$log_dir"/homescreen.log.*; do
  if [ $(ls "$log_dir"/homescreen.log.* 2>/dev/null | wc -l) -gt 7 ]; then
    rm "$f"
  fi
done
echo "Cleaned—repo slim as Doge!"
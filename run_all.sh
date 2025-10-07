
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
if [[ -x bin/aria2c ]]; then
  ./bin/aria2c --enable-rpc=true --rpc-listen-port=6800 --dir=downloads --max-concurrent-downloads=5 --summary-interval=10 &
else
  echo "aria2c not found (bin/aria2c). Skipping."
fi
if [[ -x bin/qbittorrent ]]; then
  ./bin/qbittorrent &
else
  echo "qbittorrent binary not found (bin/qbittorrent). Skipping."
fi
python server/app.py

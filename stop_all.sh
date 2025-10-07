
#!/usr/bin/env bash
set -euo pipefail
pkill -f "server/app.py" || true
pkill -f "aria2c" || true
pkill -f "qbittorrent" || true
echo "Stopped (where applicable)."

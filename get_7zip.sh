
#!/usr/bin/env bash
set -euo pipefail
mkdir -p bin
if command -v brew >/dev/null 2>&1; then
  brew install p7zip
  exit 0
fi
if command -v apt >/dev/null 2>&1; then
  sudo apt update && sudo apt install -y p7zip-full
  exit 0
fi
# Fallback: portable 7zz (Linux x64)
URL=${SEVENZ_URL:-https://www.7-zip.org/a/7z2301-linux-x64.tar.xz}
TMP=bin/7z.tar.xz
curl -L "$URL" -o "$TMP"
tar -xJf "$TMP" -C bin
chmod +x bin/7zz || true
echo "Done. 7z binaries in ./bin"

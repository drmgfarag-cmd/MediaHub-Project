
#!/usr/bin/env bash
set -euo pipefail
mkdir -p bin
if command -v brew >/dev/null 2>&1; then
  brew install ffmpeg
  echo "Installed with Homebrew."
  exit 0
fi
if command -v apt >/dev/null 2>&1; then
  sudo apt update && sudo apt install -y ffmpeg
  exit 0
fi
URL=${FFMPEG_URL:-https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz}
TMP=bin/ffmpeg-static.tar.xz
echo "Downloading static ffmpeg..."
curl -L "$URL" -o "$TMP"
tar -xJf "$TMP" -C bin
D=$(find bin -maxdepth 1 -type d -name "ffmpeg-*-static" | head -n 1)
cp "$D/ffmpeg" bin/ffmpeg
cp "$D/ffprobe" bin/ffprobe
echo "Done. Binaries in ./bin"


# Docker & Compose

## Build & Run
```bash
docker compose up --build -d
# open http://localhost:5000
```
- App persists `storage/` and `downloads/` to your host.
- Optional aria2 service runs as `p3terx/aria2-pro` (RPC on 6800). Set secret in `docker-compose.yml` and match in Settings → aria2.

## Notes
- Drop ffmpeg/7z in `./bin` if you want portable binaries inside the container, or install via OS packages in a derived image.
- For GPU encoders, use a base image with drivers + runtime (e.g., `nvidia/cuda` with `--gpus all`) and set encoder to `h264_nvenc`.

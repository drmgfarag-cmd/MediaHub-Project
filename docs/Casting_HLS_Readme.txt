Casting & HLS quick start
=========================
1) Install deps: run scripts\fetch_deps.cmd (it leaves the window open).
2) webOS (LG): Settings → Devices → Add device → type=webos, host=TV_IP. Then in Library card menu choose 'Cast to…'.
3) DLNA: Add device with controlURL (AVTransport). Then 'Cast to…' with a playable URL.
4) HLS mobile: POST /api/stream/hls/start with {"src":"<path to media>"}; it returns a tokenized /stream/<token>/index.m3u8.
5) Reverse proxy: ship Caddyfile under scripts\caddy\ if you use Caddy. TLS strongly recommended for remote/mobile.
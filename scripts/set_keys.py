import json, sys, os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
cfg = root / "config" / "keys.local.json"
cfg.parent.mkdir(parents=True, exist_ok=True)
payload = {
  "ANILIST_CLIENT_ID": "30444",
  "ANILIST_CLIENT_SECRET": "dc63l21fPbnvgpx7Qinlg9miT5ismqUu77oVSTj2",
  "OMDB_KEY": "95b991d3",
  "GOOGLE_BOOKS_KEY": "AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8",
  "TMDB_KEY": "3aca2154c1d9223036904a86202897ba",
  "TVDB_KEY": "72f8b186-1eb8-471d-94e7-85063cf7a1bf",
  "DISCOGS_TOKEN": "DlYcCvjWkCSKwuoxWznBrUDFitmPFTqBpIuoqizm",
  "ACOUSTID_KEY": "W48qHR6eir",
  "REAL_DEBRID_TOKEN": "HMPNSB7QFO4RL2DCIKRRPKFKLKBIR7LSWWUOVNDAADNHOTC2SAXA"
}
with open(cfg, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
print("Wrote", cfg)
print("For security, values will be redacted in logs and /integrations/status. Keep this file private.")
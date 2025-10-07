from .security import require_api_key
from flask import Blueprint, jsonify, request
import os, json

tax_bp = Blueprint('taxonomy', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO  = os.path.join(ROOT, "storage")
TAX  = os.path.join(STO, "taxonomy.json")

DEFAULT = {
  "categories": [
    {
      "id": "kids",
      "title": "Kids",
      "subs": [
        "Movies",
        "TV",
        "eBooks",
        "Comics",
        "Manga",
        "Audiobooks",
        "Animated",
        "Educational"
      ]
    },
    {
      "id": "movies",
      "title": "Movies",
      "subs": [
        "Continue Watching",
        "Recently Added",
        "Kids",
        "4K HDR",
        "Dolby Vision",
        "Atmos",
        "By Genre",
        "By Decade",
        "Documentaries",
        "Stand-Up",
        "Collections: Series",
        "Collections: Franchise",
        "Collections: Top Awards",
        "Collections: Crossovers",
        "Collections: Universes"
      ]
    },
    {
      "id": "tv",
      "title": "TV",
      "subs": [
        "Continue Watching",
        "Recently Added",
        "Kids",
        "On-going Series",
        "Mini-series",
        "Anthology",
        "By Genre",
        "Documentaries",
        "Stand-Up",
        "Collections: Series",
        "Collections: Franchise",
        "Collections: Top Awards",
        "Collections: Crossovers",
        "Collections: Universes"
      ]
    },
    {
      "id": "books",
      "title": "Books",
      "subs": [
        "eBooks",
        "Comics",
        "Manga",
        "Audiobooks",
        "Kids",
        "Continue Reading",
        "By Series",
        "By Author"
      ]
    },
    {
      "id": "audio",
      "title": "Audio",
      "subs": [
        "Top Albums",
        "Top Artists",
        "Playlists",
        "Hi-Res / Lossless",
        "Atmos / Spatial",
        "Live Albums",
        "Soundtracks",
        "Kids"
      ]
    }
  ]
}

def _load():
    try:
        with open(TAX,"r",encoding="utf-8") as f: return json.load(f)
    except Exception:
        return DEFAULT

def _save(d):
    os.makedirs(STO, exist_ok=True)
    with open(TAX,"w",encoding="utf-8") as f: json.dump(d,f,indent=2, ensure_ascii=False)

@tax_bp.route("/api/taxonomy", methods=["GET"])
def get_tax():
    return jsonify(_load())

@tax_bp.route("/api/taxonomy", methods=["POST"])
@require_api_key
def set_tax():
    data = request.get_json(silent=True) or {}
    _save(data); return jsonify({"ok": True})
"""
Local Library Management Routes
Provides access to local media library with rails, titles, and episodes
"""
from flask import Blueprint, jsonify, request
import os
import json
import time
import re
from pathlib import Path
from collections import Counter, defaultdict

lib_bp = Blueprint('library_local', __name__)

# Paths
ROOT = Path(__file__).resolve().parents[2]
STORAGE = ROOT / "storage"
LIBRARY_INDEX = STORAGE / "library_index.json"

def _load_index():
    """Load library index from file"""
    try:
        if LIBRARY_INDEX.exists():
            with open(LIBRARY_INDEX, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {"items": data if isinstance(data, list) else []}
        return {"items": []}
    except Exception as e:
        print(f"Error loading library index: {e}")
        return {"items": []}

def _item_map(db):
    """Convert items list to dictionary keyed by ID"""
    items = db.get("items", [])
    return {(it.get("id") or it.get("path") or str(i)): it for i, it in enumerate(items)}

def _text(it):
    """Get searchable text from item"""
    return ' '.join(filter(None, [
        it.get('title', ''),
        it.get('name', ''),
        it.get('path', ''),
        ' '.join(it.get('genres', []))
    ]))

def _tok(text, pattern):
    """Check if pattern matches text"""
    try:
        return bool(re.search(pattern, text, re.I))
    except:
        return False

def _is_movie(it):
    return it.get('type') in ['movie', 'film']

def _is_series(it):
    return it.get('type') in ['series', 'show', 'tv', 'episode']

def _is_audio(it):
    return it.get('type') in ['audio', 'music', 'track']

def _is_book(it):
    return it.get('type') in ['book', 'ebook']

def _is_comic(it):
    return it.get('type') == 'comic'

def _is_kids(it):
    return 'Kids' in it.get('genres', []) or 'Children' in it.get('genres', [])

def _make_rails(db):
    """Organize items into rails"""
    items = db.get("items", [])
    rails = []
    
    # Continue Watching
    cont = [i for i in items if (i.get("progress", 0) or 0) > 0][:18]
    if cont:
        rails.append({"id": "continue", "title": "Continue Watching", "items": cont})
    
    # Recently Added
    rec = sorted(items, key=lambda x: x.get("added_ts", 0), reverse=True)[:18]
    if rec:
        rails.append({"id": "recent", "title": "Recently Added", "items": rec})
    
    # Movies
    movies = [i for i in items if _is_movie(i)]
    if movies:
        rails.append({"id": "movies", "title": "Movies", "items": movies[:18]})
    
    # TV Shows
    shows = [i for i in items if _is_series(i)]
    if shows:
        rails.append({"id": "shows", "title": "TV Shows", "items": shows[:18]})
    
    # Music
    music = [i for i in items if _is_audio(i)]
    if music:
        rails.append({"id": "music", "title": "Music", "items": music[:18]})
    
    # Books
    books = [i for i in items if _is_book(i)]
    if books:
        rails.append({"id": "books", "title": "Books", "items": books[:18]})
    
    # Comics
    comics = [i for i in items if _is_comic(i)]
    if comics:
        rails.append({"id": "comics", "title": "Comics", "items": comics[:18]})
    
    # Kids
    kids = [i for i in items if _is_kids(i)]
    if kids:
        rails.append({"id": "kids", "title": "Kids", "items": kids[:18]})
    
    return {"rails": rails}

@lib_bp.route("/api/library/rails", methods=["GET"])
def rails():
    """Get library organized into rails"""
    try:
        db = _load_index()
        return jsonify(_make_rails(db))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lib_bp.route("/api/library/title/<title_id>", methods=["GET"])
def title(title_id):
    """Get specific title details"""
    try:
        db = _load_index()
        mp = _item_map(db)
        it = mp.get(title_id)
        
        if not it:
            # Try finding by ID or path
            items = db.get("items", [])
            it = next((x for x in items if str(x.get("id")) == title_id or x.get("path") == title_id), None)
        
        if not it:
            return jsonify({"error": "not found"}), 404
        
        return jsonify(it)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lib_bp.route("/api/library/episodes/<sid>", methods=["GET"])
def episodes(sid):
    """Get episodes for a series"""
    try:
        db = _load_index()
        items = db.get("items", [])
        
        # Find season by id in any series item
        for it in items:
            for s in (it.get("seasons") or []):
                if str(s.get("id")) == str(sid):
                    return jsonify({"season": s})
        
        return jsonify({"error": "not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

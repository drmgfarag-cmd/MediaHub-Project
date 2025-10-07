from flask import Blueprint, jsonify, request
import os, json, time
from datetime import datetime
from pathlib import Path

discovery_advanced_bp = Blueprint("discovery_advanced", __name__)

# Storage paths
STORAGE_DIR = Path("storage/config")
SEARCH_HISTORY_FILE = STORAGE_DIR / "search_history.json"
VISUAL_SEARCH_INDEX = STORAGE_DIR / "visual_search_index.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize files if they don't exist
if not SEARCH_HISTORY_FILE.exists():
    SEARCH_HISTORY_FILE.write_text(json.dumps({"searches": []}, indent=2))

if not VISUAL_SEARCH_INDEX.exists():
    VISUAL_SEARCH_INDEX.write_text(json.dumps({"index": []}, indent=2))

# Sample data for demonstration - In production, this would query actual media database
SAMPLE_MEDIA_DATABASE = [
    {
        "id": 1, "title": "The Matrix", "type": "movie", "year": 1999, "genre": ["Sci-Fi", "Action"],
        "rating": 8.7, "director": "Wachowski Sisters", "actors": ["Keanu Reeves", "Laurence Fishburne"],
        "resolution": "4K", "codec": "HEVC", "audio": "Dolby Atmos", "size_gb": 15.2,
        "tags": ["cyberpunk", "philosophy", "simulation"], "awards": ["Oscar", "BAFTA"],
        "language": ["English"], "subtitles": ["English", "Spanish", "French"]
    },
    {
        "id": 2, "title": "The Lord of the Rings: The Fellowship of the Ring", "type": "movie",
        "year": 2001, "genre": ["Fantasy", "Adventure"], "rating": 8.8,
        "director": "Peter Jackson", "actors": ["Elijah Wood", "Ian McKellen"],
        "resolution": "4K", "codec": "HEVC", "audio": "DTS-HD", "size_gb": 18.5,
        "tags": ["epic", "quest", "tolkien"], "awards": ["Oscar", "Golden Globe"],
        "language": ["English"], "subtitles": ["English", "Spanish", "German"]
    },
    {
        "id": 3, "title": "Breaking Bad", "type": "tv", "year": 2008, "genre": ["Drama", "Crime"],
        "rating": 9.5, "creator": "Vince Gilligan", "actors": ["Bryan Cranston", "Aaron Paul"],
        "resolution": "1080p", "codec": "x264", "audio": "AC3", "size_gb": 45.0,
        "tags": ["antihero", "chemistry", "cartel"], "awards": ["Emmy", "Golden Globe"],
        "language": ["English"], "subtitles": ["English", "Spanish"]
    },
    {
        "id": 4, "title": "Dune", "type": "book", "year": 1965, "genre": ["Sci-Fi", "Fantasy"],
        "rating": 8.6, "author": "Frank Herbert", "pages": 688, "format": "EPUB",
        "size_mb": 2.4, "tags": ["desert", "politics", "spice"], "awards": ["Hugo", "Nebula"],
        "language": ["English"]
    },
    {
        "id": 5, "title": "Dark Side of the Moon", "type": "album", "year": 1973,
        "genre": ["Rock", "Progressive"], "rating": 9.2, "artist": "Pink Floyd",
        "tracks": 10, "format": "FLAC", "bitrate": "1411 kbps", "size_mb": 320,
        "tags": ["psychedelic", "concept album"], "awards": ["Grammy"],
        "language": ["English"]
    },
    {
        "id": 6, "title": "Inception", "type": "movie", "year": 2010, "genre": ["Sci-Fi", "Thriller"],
        "rating": 8.8, "director": "Christopher Nolan", "actors": ["Leonardo DiCaprio", "Tom Hardy"],
        "resolution": "4K", "codec": "HEVC", "audio": "Dolby Atmos", "size_gb": 16.8,
        "tags": ["dreams", "heist", "mind-bending"], "awards": ["Oscar", "BAFTA"],
        "language": ["English"], "subtitles": ["English", "French", "Japanese"]
    },
    {
        "id": 7, "title": "Game of Thrones", "type": "tv", "year": 2011, "genre": ["Fantasy", "Drama"],
        "rating": 9.3, "creator": "David Benioff", "actors": ["Emilia Clarke", "Kit Harington"],
        "resolution": "4K", "codec": "HEVC", "audio": "DTS-HD", "size_gb": 120.0,
        "tags": ["medieval", "politics", "dragons"], "awards": ["Emmy", "Golden Globe"],
        "language": ["English"], "subtitles": ["English", "Spanish", "German"]
    },
    {
        "id": 8, "title": "1984", "type": "book", "year": 1949, "genre": ["Dystopian", "Fiction"],
        "rating": 8.7, "author": "George Orwell", "pages": 328, "format": "PDF",
        "size_mb": 1.8, "tags": ["surveillance", "totalitarian", "classic"],
        "language": ["English"]
    },
    {
        "id": 9, "title": "Abbey Road", "type": "album", "year": 1969, "genre": ["Rock", "Pop"],
        "rating": 9.0, "artist": "The Beatles", "tracks": 17, "format": "FLAC",
        "bitrate": "1411 kbps", "size_mb": 280, "tags": ["classic rock", "60s"],
        "awards": ["Grammy"], "language": ["English"]
    },
    {
        "id": 10, "title": "Interstellar", "type": "movie", "year": 2014, "genre": ["Sci-Fi", "Drama"],
        "rating": 8.6, "director": "Christopher Nolan", "actors": ["Matthew McConaughey", "Anne Hathaway"],
        "resolution": "4K", "codec": "HEVC", "audio": "Dolby Atmos", "size_gb": 19.2,
        "tags": ["space", "time", "relativity"], "awards": ["Oscar"],
        "language": ["English"], "subtitles": ["English", "Spanish", "Chinese"]
    }
]

@discovery_advanced_bp.route("/api/discovery/search", methods=["GET"])
def advanced_search():
    """Universal cross-category search with faceted filtering"""
    query = request.args.get("q", "").lower()
    media_type = request.args.get("type", "")  # movie, tv, book, album, or empty for all
    genre = request.args.get("genre", "")
    year_min = request.args.get("year_min", "")
    year_max = request.args.get("year_max", "")
    rating_min = request.args.get("rating_min", "")
    resolution = request.args.get("resolution", "")
    codec = request.args.get("codec", "")
    audio = request.args.get("audio", "")
    language = request.args.get("language", "")
    tags = request.args.get("tags", "")
    sort_by = request.args.get("sort", "relevance")  # relevance, rating, year, title

    # Start with all items
    filtered_items = SAMPLE_MEDIA_DATABASE.copy()

    # Apply text search
    if query:
        filtered_items = [
            item for item in filtered_items
            if query in item["title"].lower() or
               query in str(item.get("director", "")).lower() or
               query in str(item.get("author", "")).lower() or
               query in str(item.get("artist", "")).lower() or
               any(query in actor.lower() for actor in item.get("actors", [])) or
               any(query in tag.lower() for tag in item.get("tags", []))
        ]

    # Apply faceted filters
    if media_type:
        filtered_items = [item for item in filtered_items if item["type"] == media_type]

    if genre:
        filtered_items = [item for item in filtered_items if genre in item.get("genre", [])]

    if year_min:
        filtered_items = [item for item in filtered_items if item["year"] >= int(year_min)]

    if year_max:
        filtered_items = [item for item in filtered_items if item["year"] <= int(year_max)]

    if rating_min:
        filtered_items = [item for item in filtered_items if item["rating"] >= float(rating_min)]

    if resolution:
        filtered_items = [item for item in filtered_items if item.get("resolution", "") == resolution]

    if codec:
        filtered_items = [item for item in filtered_items if item.get("codec", "") == codec]

    if audio:
        filtered_items = [item for item in filtered_items if item.get("audio", "") == audio]

    if language:
        filtered_items = [item for item in filtered_items if language in item.get("language", [])]

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",")]
        filtered_items = [
            item for item in filtered_items
            if any(tag in [t.lower() for t in item.get("tags", [])] for tag in tag_list)
        ]

    # Sort results
    if sort_by == "rating":
        filtered_items.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "year":
        filtered_items.sort(key=lambda x: x["year"], reverse=True)
    elif sort_by == "title":
        filtered_items.sort(key=lambda x: x["title"])

    # Save to search history
    if query or media_type or genre:
        save_search_history(query, {
            "type": media_type, "genre": genre, "year_min": year_min,
            "year_max": year_max, "rating_min": rating_min
        })

    # Calculate facets for the current result set
    facets = calculate_facets(filtered_items)

    return jsonify({
        "results": filtered_items,
        "count": len(filtered_items),
        "facets": facets,
        "query": query
    })

@discovery_advanced_bp.route("/api/discovery/facets", methods=["GET"])
def get_facets():
    """Get available facets for filtering"""
    facets = calculate_facets(SAMPLE_MEDIA_DATABASE)
    return jsonify(facets)

def calculate_facets(items):
    """Calculate available facets from current result set"""
    facets = {
        "types": {},
        "genres": {},
        "years": {},
        "ratings": {},
        "resolutions": {},
        "codecs": {},
        "audio": {},
        "languages": {},
        "tags": {}
    }

    for item in items:
        # Type facet
        item_type = item.get("type", "unknown")
        facets["types"][item_type] = facets["types"].get(item_type, 0) + 1

        # Genre facet
        for genre in item.get("genre", []):
            facets["genres"][genre] = facets["genres"].get(genre, 0) + 1

        # Year facet (grouped by decade)
        year = item.get("year", 0)
        decade = f"{(year // 10) * 10}s"
        facets["years"][decade] = facets["years"].get(decade, 0) + 1

        # Rating facet (grouped)
        rating = item.get("rating", 0)
        rating_group = f"{int(rating)}-{int(rating)+1}"
        facets["ratings"][rating_group] = facets["ratings"].get(rating_group, 0) + 1

        # Technical facets
        if "resolution" in item:
            res = item["resolution"]
            facets["resolutions"][res] = facets["resolutions"].get(res, 0) + 1

        if "codec" in item:
            codec = item["codec"]
            facets["codecs"][codec] = facets["codecs"].get(codec, 0) + 1

        if "audio" in item:
            audio = item["audio"]
            facets["audio"][audio] = facets["audio"].get(audio, 0) + 1

        # Language facet
        for lang in item.get("language", []):
            facets["languages"][lang] = facets["languages"].get(lang, 0) + 1

        # Tags facet
        for tag in item.get("tags", []):
            facets["tags"][tag] = facets["tags"].get(tag, 0) + 1

    return facets

@discovery_advanced_bp.route("/api/discovery/visual_search", methods=["POST"])
def visual_search():
    """Visual search using uploaded image"""
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files["image"]
    
    # In a real implementation, this would:
    # 1. Use computer vision (e.g., OpenCV, TensorFlow) to extract image features
    # 2. Compare against indexed media posters/covers
    # 3. Return similar items based on visual similarity
    
    # For demonstration, return sample results
    # Simulating image analysis delay
    time.sleep(0.5)
    
    # Return movies/shows with similar visual themes
    results = [item for item in SAMPLE_MEDIA_DATABASE if item["type"] in ["movie", "tv"]][:5]
    
    return jsonify({
        "results": results,
        "method": "visual_similarity",
        "confidence": 0.85
    })

@discovery_advanced_bp.route("/api/discovery/query_builder", methods=["POST"])
def query_builder():
    """Advanced query builder for complex searches"""
    data = request.json
    conditions = data.get("conditions", [])
    operator = data.get("operator", "AND")  # AND or OR
    
    # Start with all items
    if operator == "AND":
        results = SAMPLE_MEDIA_DATABASE.copy()
        for condition in conditions:
            results = apply_condition(results, condition)
    else:  # OR
        results = []
        seen_ids = set()
        for condition in conditions:
            condition_results = apply_condition(SAMPLE_MEDIA_DATABASE.copy(), condition)
            for item in condition_results:
                if item["id"] not in seen_ids:
                    results.append(item)
                    seen_ids.add(item["id"])
    
    return jsonify({
        "results": results,
        "count": len(results),
        "query": {"conditions": conditions, "operator": operator}
    })

def apply_condition(items, condition):
    """Apply a single query condition"""
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")
    
    if not field or not operator:
        return items
    
    filtered = []
    for item in items:
        item_value = item.get(field)
        
        if operator == "equals":
            if item_value == value:
                filtered.append(item)
        elif operator == "contains":
            if value.lower() in str(item_value).lower():
                filtered.append(item)
        elif operator == "greater_than":
            if isinstance(item_value, (int, float)) and item_value > float(value):
                filtered.append(item)
        elif operator == "less_than":
            if isinstance(item_value, (int, float)) and item_value < float(value):
                filtered.append(item)
        elif operator == "in":
            if isinstance(item_value, list) and value in item_value:
                filtered.append(item)
    
    return filtered

@discovery_advanced_bp.route("/api/discovery/search_history", methods=["GET"])
def get_search_history():
    """Get user's search history"""
    try:
        with open(SEARCH_HISTORY_FILE, "r") as f:
            data = json.load(f)
        
        # Return last 50 searches
        searches = data.get("searches", [])[-50:]
        searches.reverse()  # Most recent first
        
        return jsonify({"searches": searches})
    except Exception as e:
        return jsonify({"searches": [], "error": str(e)})

@discovery_advanced_bp.route("/api/discovery/search_history", methods=["DELETE"])
def clear_search_history():
    """Clear search history"""
    try:
        SEARCH_HISTORY_FILE.write_text(json.dumps({"searches": []}, indent=2))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def save_search_history(query, filters):
    """Save search to history"""
    try:
        with open(SEARCH_HISTORY_FILE, "r") as f:
            data = json.load(f)
        
        searches = data.get("searches", [])
        
        # Add new search
        searches.append({
            "query": query,
            "filters": filters,
            "timestamp": datetime.now().isoformat(),
            "count": len([item for item in SAMPLE_MEDIA_DATABASE if query.lower() in item["title"].lower()])
        })
        
        # Keep only last 100 searches
        if len(searches) > 100:
            searches = searches[-100:]
        
        data["searches"] = searches
        
        with open(SEARCH_HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving search history: {e}")

@discovery_advanced_bp.route("/api/discovery/suggestions", methods=["GET"])
def get_suggestions():
    """Get search suggestions based on partial query"""
    partial = request.args.get("q", "").lower()
    
    if len(partial) < 2:
        return jsonify({"suggestions": []})
    
    suggestions = []
    seen = set()
    
    # Suggest titles
    for item in SAMPLE_MEDIA_DATABASE:
        title = item["title"]
        if partial in title.lower() and title not in seen:
            suggestions.append({
                "text": title,
                "type": "title",
                "category": item["type"]
            })
            seen.add(title)
    
    # Suggest genres
    for item in SAMPLE_MEDIA_DATABASE:
        for genre in item.get("genre", []):
            if partial in genre.lower() and genre not in seen:
                suggestions.append({
                    "text": genre,
                    "type": "genre"
                })
                seen.add(genre)
    
    # Suggest tags
    for item in SAMPLE_MEDIA_DATABASE:
        for tag in item.get("tags", []):
            if partial in tag.lower() and tag not in seen:
                suggestions.append({
                    "text": tag,
                    "type": "tag"
                })
                seen.add(tag)
    
    return jsonify({"suggestions": suggestions[:10]})

@discovery_advanced_bp.route("/api/discovery/trending", methods=["GET"])
def get_trending():
    """Get trending searches and content"""
    # In production, this would track actual user behavior
    trending = {
        "searches": ["matrix", "sci-fi", "4K", "christopher nolan"],
        "content": [item for item in SAMPLE_MEDIA_DATABASE if item["rating"] >= 9.0]
    }
    return jsonify(trending)

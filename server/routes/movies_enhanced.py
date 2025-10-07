from flask import Blueprint, jsonify, request
import os, json
from datetime import datetime
from pathlib import Path

movies_enhanced_bp = Blueprint("movies_enhanced", __name__)

# Storage paths
STORAGE_DIR = Path("storage/config")
MOVIES_DATA_FILE = STORAGE_DIR / "movies_data.json"
COLLECTIONS_FILE = STORAGE_DIR / "movie_collections.json"
WATCHLIST_FILE = STORAGE_DIR / "movie_watchlist.json"
WATCH_HISTORY_FILE = STORAGE_DIR / "watch_history.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize files
if not MOVIES_DATA_FILE.exists():
    MOVIES_DATA_FILE.write_text(json.dumps({"movies": []}, indent=2))

if not COLLECTIONS_FILE.exists():
    COLLECTIONS_FILE.write_text(json.dumps({"collections": []}, indent=2))

if not WATCHLIST_FILE.exists():
    WATCHLIST_FILE.write_text(json.dumps({"watchlist": []}, indent=2))

if not WATCH_HISTORY_FILE.exists():
    WATCH_HISTORY_FILE.write_text(json.dumps({"history": []}, indent=2))

# ===== COLLECTION MANAGEMENT =====

@movies_enhanced_bp.route("/api/movies/collections", methods=["GET", "POST"])
def manage_collections():
    """Manage movie collections (franchises, custom sets)"""
    if request.method == "GET":
        with open(COLLECTIONS_FILE, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "collections": data.get("collections", [])})
    
    else:  # POST
        collection = request.json
        
        with open(COLLECTIONS_FILE, "r") as f:
            data = json.load(f)
        
        if "collections" not in data:
            data["collections"] = []
        
        new_collection = {
            "id": len(data["collections"]) + 1,
            "name": collection.get("name", "Untitled Collection"),
            "type": collection.get("type", "custom"),  # franchise, custom, genre, decade
            "description": collection.get("description", ""),
            "movies": collection.get("movies", []),
            "poster": collection.get("poster", ""),
            "backdrop": collection.get("backdrop", ""),
            "created_at": datetime.now().isoformat()
        }
        
        data["collections"].append(new_collection)
        
        with open(COLLECTIONS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "collection": new_collection})

@movies_enhanced_bp.route("/api/movies/collections/<int:collection_id>", methods=["GET", "PUT", "DELETE"])
def manage_collection(collection_id):
    """Get, update, or delete a specific collection"""
    with open(COLLECTIONS_FILE, "r") as f:
        data = json.load(f)
    
    collections = data.get("collections", [])
    collection = next((c for c in collections if c.get("id") == collection_id), None)
    
    if not collection:
        return jsonify({"error": "Collection not found"}), 404
    
    if request.method == "GET":
        return jsonify({"success": True, "collection": collection})
    
    elif request.method == "PUT":
        updates = request.json
        collection.update(updates)
        
        with open(COLLECTIONS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "collection": collection})
    
    else:  # DELETE
        collections.remove(collection)
        data["collections"] = collections
        
        with open(COLLECTIONS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "message": "Collection deleted"})

@movies_enhanced_bp.route("/api/movies/collections/auto-generate", methods=["POST"])
def auto_generate_collections():
    """Auto-generate collections by genre, decade, or quality"""
    data = request.json
    criteria = data.get("criteria", "genre")  # genre, decade, quality, director, actor
    
    # Simulate auto-generation
    generated_collections = []
    
    if criteria == "genre":
        genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror"]
        for genre in genres:
            generated_collections.append({
                "name": f"{genre} Movies",
                "type": "genre",
                "criteria": genre,
                "count": 25
            })
    
    elif criteria == "decade":
        decades = ["1980s", "1990s", "2000s", "2010s", "2020s"]
        for decade in decades:
            generated_collections.append({
                "name": f"{decade} Movies",
                "type": "decade",
                "criteria": decade,
                "count": 30
            })
    
    elif criteria == "quality":
        qualities = ["4K UHD", "1080p", "720p"]
        for quality in qualities:
            generated_collections.append({
                "name": f"{quality} Movies",
                "type": "quality",
                "criteria": quality,
                "count": 40
            })
    
    return jsonify({
        "success": True,
        "criteria": criteria,
        "generated_collections": generated_collections
    })

# ===== WATCH HISTORY & PROGRESS =====

@movies_enhanced_bp.route("/api/movies/watch-history", methods=["GET", "POST"])
def watch_history():
    """Manage watch history"""
    if request.method == "GET":
        with open(WATCH_HISTORY_FILE, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "history": data.get("history", [])})
    
    else:  # POST
        entry = request.json
        
        with open(WATCH_HISTORY_FILE, "r") as f:
            data = json.load(f)
        
        if "history" not in data:
            data["history"] = []
        
        # Check if movie already in history
        existing = next((h for h in data["history"] if h.get("movie_id") == entry.get("movie_id")), None)
        
        if existing:
            existing["progress"] = entry.get("progress", 0)
            existing["last_watched"] = datetime.now().isoformat()
        else:
            data["history"].append({
                "movie_id": entry.get("movie_id"),
                "title": entry.get("title", ""),
                "progress": entry.get("progress", 0),
                "completed": entry.get("completed", False),
                "last_watched": datetime.now().isoformat()
            })
        
        with open(WATCH_HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True})

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/progress", methods=["GET", "PUT"])
def movie_progress(movie_id):
    """Get or update movie progress"""
    with open(WATCH_HISTORY_FILE, "r") as f:
        data = json.load(f)
    
    history = data.get("history", [])
    entry = next((h for h in history if h.get("movie_id") == movie_id), None)
    
    if request.method == "GET":
        if entry:
            return jsonify({"success": True, "progress": entry.get("progress", 0)})
        else:
            return jsonify({"success": True, "progress": 0})
    
    else:  # PUT
        progress = request.json.get("progress", 0)
        
        if entry:
            entry["progress"] = progress
            entry["last_watched"] = datetime.now().isoformat()
        else:
            history.append({
                "movie_id": movie_id,
                "progress": progress,
                "last_watched": datetime.now().isoformat()
            })
        
        data["history"] = history
        
        with open(WATCH_HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "progress": progress})

# ===== WATCHLIST & FAVORITES =====

@movies_enhanced_bp.route("/api/movies/watchlist", methods=["GET", "POST"])
def watchlist():
    """Manage watchlist"""
    if request.method == "GET":
        with open(WATCHLIST_FILE, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "watchlist": data.get("watchlist", [])})
    
    else:  # POST
        movie = request.json
        
        with open(WATCHLIST_FILE, "r") as f:
            data = json.load(f)
        
        if "watchlist" not in data:
            data["watchlist"] = []
        
        # Check if already in watchlist
        if not any(m.get("movie_id") == movie.get("movie_id") for m in data["watchlist"]):
            data["watchlist"].append({
                "movie_id": movie.get("movie_id"),
                "title": movie.get("title", ""),
                "year": movie.get("year", ""),
                "poster": movie.get("poster", ""),
                "added_at": datetime.now().isoformat()
            })
            
            with open(WATCHLIST_FILE, "w") as f:
                json.dump(data, f, indent=2)
            
            return jsonify({"success": True, "message": "Added to watchlist"})
        else:
            return jsonify({"success": False, "message": "Already in watchlist"})

@movies_enhanced_bp.route("/api/movies/watchlist/<int:movie_id>", methods=["DELETE"])
def remove_from_watchlist(movie_id):
    """Remove movie from watchlist"""
    with open(WATCHLIST_FILE, "r") as f:
        data = json.load(f)
    
    watchlist = data.get("watchlist", [])
    watchlist = [m for m in watchlist if m.get("movie_id") != movie_id]
    data["watchlist"] = watchlist
    
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({"success": True, "message": "Removed from watchlist"})

# ===== RATINGS & REVIEWS =====

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/rating", methods=["GET", "POST"])
def movie_rating(movie_id):
    """Get or set movie rating"""
    with open(MOVIES_DATA_FILE, "r") as f:
        data = json.load(f)
    
    movies = data.get("movies", [])
    movie = next((m for m in movies if m.get("id") == movie_id), None)
    
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    
    if request.method == "GET":
        return jsonify({
            "success": True,
            "rating": movie.get("user_rating", 0),
            "review": movie.get("user_review", "")
        })
    
    else:  # POST
        rating_data = request.json
        movie["user_rating"] = rating_data.get("rating", 0)
        movie["user_review"] = rating_data.get("review", "")
        movie["rated_at"] = datetime.now().isoformat()
        
        with open(MOVIES_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True})

# ===== RECOMMENDATIONS =====

@movies_enhanced_bp.route("/api/movies/recommendations", methods=["GET"])
def get_recommendations():
    """Get personalized movie recommendations"""
    user_id = request.args.get("user_id", "default")
    count = int(request.args.get("count", 10))
    
    # Simulate recommendation engine
    recommendations = []
    for i in range(count):
        recommendations.append({
            "id": i + 1,
            "title": f"Recommended Movie {i + 1}",
            "year": 2024,
            "rating": 8.5,
            "reason": "Based on your watch history",
            "poster": f"/assets/posters/movie_{i + 1}.jpg"
        })
    
    return jsonify({
        "success": True,
        "recommendations": recommendations,
        "count": len(recommendations)
    })

# ===== METADATA & MEDIA =====

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/posters", methods=["GET"])
def get_movie_posters(movie_id):
    """Get multiple poster options for a movie"""
    posters = [
        {"url": f"/assets/posters/movie_{movie_id}_1.jpg", "type": "primary", "language": "en"},
        {"url": f"/assets/posters/movie_{movie_id}_2.jpg", "type": "alternative", "language": "en"},
        {"url": f"/assets/posters/movie_{movie_id}_3.jpg", "type": "alternative", "language": "en"}
    ]
    
    return jsonify({
        "success": True,
        "movie_id": movie_id,
        "posters": posters
    })

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/backdrops", methods=["GET"])
def get_movie_backdrops(movie_id):
    """Get multiple backdrop options for a movie"""
    backdrops = [
        {"url": f"/assets/backdrops/movie_{movie_id}_1.jpg", "type": "primary"},
        {"url": f"/assets/backdrops/movie_{movie_id}_2.jpg", "type": "alternative"},
        {"url": f"/assets/backdrops/movie_{movie_id}_3.jpg", "type": "alternative"}
    ]
    
    return jsonify({
        "success": True,
        "movie_id": movie_id,
        "backdrops": backdrops
    })

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/trailers", methods=["GET"])
def get_movie_trailers(movie_id):
    """Get trailers for a movie"""
    trailers = [
        {"name": "Official Trailer", "url": "https://youtube.com/watch?v=example1", "type": "Trailer"},
        {"name": "Teaser", "url": "https://youtube.com/watch?v=example2", "type": "Teaser"}
    ]
    
    return jsonify({
        "success": True,
        "movie_id": movie_id,
        "trailers": trailers
    })

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/cast", methods=["GET"])
def get_movie_cast(movie_id):
    """Get detailed cast information"""
    cast = [
        {"name": "Actor 1", "character": "Character 1", "profile_path": "/assets/actors/actor1.jpg"},
        {"name": "Actor 2", "character": "Character 2", "profile_path": "/assets/actors/actor2.jpg"}
    ]
    
    return jsonify({
        "success": True,
        "movie_id": movie_id,
        "cast": cast
    })

@movies_enhanced_bp.route("/api/movies/<int:movie_id>/crew", methods=["GET"])
def get_movie_crew(movie_id):
    """Get detailed crew information"""
    crew = [
        {"name": "Director Name", "job": "Director", "department": "Directing"},
        {"name": "Writer Name", "job": "Writer", "department": "Writing"}
    ]
    
    return jsonify({
        "success": True,
        "movie_id": movie_id,
        "crew": crew
    })

# ===== PARENTAL CONTROLS =====

@movies_enhanced_bp.route("/api/movies/parental-controls", methods=["GET", "POST"])
def parental_controls():
    """Manage parental control settings"""
    if request.method == "GET":
        settings = {
            "enabled": True,
            "max_rating": "PG-13",
            "blocked_genres": ["Horror", "Adult"],
            "require_pin": True,
            "pin": "****"
        }
        return jsonify({"success": True, "settings": settings})
    
    else:  # POST
        settings = request.json
        # Save settings logic here
        return jsonify({"success": True, "settings": settings})

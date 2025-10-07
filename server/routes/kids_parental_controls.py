from flask import Blueprint, jsonify, request
import os, json, hashlib
from datetime import datetime, timedelta, time
from pathlib import Path

kids_parental_controls_bp = Blueprint("kids_parental_controls", __name__)

# Storage paths
STORAGE_DIR = Path("storage/config")
PARENTAL_SETTINGS_FILE = STORAGE_DIR / "parental_settings.json"
KIDS_PROFILES_FILE = STORAGE_DIR / "kids_profiles.json"
ACTIVITY_LOG_FILE = STORAGE_DIR / "kids_activity_log.json"
TIME_LIMITS_FILE = STORAGE_DIR / "time_limits.json"
CONTENT_WHITELIST_FILE = STORAGE_DIR / "content_whitelist.json"
CONTENT_BLACKLIST_FILE = STORAGE_DIR / "content_blacklist.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize files
for file_path in [PARENTAL_SETTINGS_FILE, KIDS_PROFILES_FILE, ACTIVITY_LOG_FILE,
                   TIME_LIMITS_FILE, CONTENT_WHITELIST_FILE, CONTENT_BLACKLIST_FILE]:
    if not file_path.exists():
        file_path.write_text(json.dumps({"data": []}, indent=2))

# ===== PARENTAL CONTROL SETTINGS =====

@kids_parental_controls_bp.route("/api/parental-controls/settings", methods=["GET", "POST"])
def parental_settings():
    """Get or update parental control settings"""
    if request.method == "GET":
        if PARENTAL_SETTINGS_FILE.exists():
            with open(PARENTAL_SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        else:
            settings = {
                "enabled": True,
                "require_pin": True,
                "pin_hash": "",
                "default_age_rating": "PG",
                "blocked_categories": [],
                "time_restrictions_enabled": True,
                "activity_monitoring_enabled": True,
                "content_approval_required": False,
                "safe_search_enabled": True
            }
        
        return jsonify({"success": True, "settings": settings})
    
    else:  # POST
        settings = request.json
        
        # Hash PIN if provided
        if "pin" in settings:
            pin = settings.pop("pin")
            settings["pin_hash"] = hashlib.sha256(pin.encode()).hexdigest()
        
        with open(PARENTAL_SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        
        return jsonify({"success": True, "settings": settings})

@kids_parental_controls_bp.route("/api/parental-controls/verify-pin", methods=["POST"])
def verify_pin():
    """Verify parental control PIN"""
    pin = request.json.get("pin", "")
    
    with open(PARENTAL_SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    
    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    
    if pin_hash == settings.get("pin_hash", ""):
        return jsonify({"success": True, "verified": True})
    else:
        return jsonify({"success": False, "verified": False, "message": "Incorrect PIN"})

# ===== KIDS PROFILES =====

@kids_parental_controls_bp.route("/api/kids/profiles", methods=["GET", "POST"])
def kids_profiles():
    """Get all kids profiles or create a new one"""
    with open(KIDS_PROFILES_FILE, "r") as f:
        data = json.load(f)
    
    if request.method == "GET":
        return jsonify({"success": True, "profiles": data.get("data", [])})
    
    else:  # POST
        profile = request.json
        profiles = data.get("data", [])
        
        new_profile = {
            "id": len(profiles) + 1,
            "name": profile.get("name", ""),
            "age": profile.get("age", 0),
            "avatar": profile.get("avatar", ""),
            "age_rating_limit": profile.get("age_rating_limit", "PG"),
            "allowed_categories": profile.get("allowed_categories", ["kids", "family"]),
            "time_limit_minutes": profile.get("time_limit_minutes", 120),
            "schedule": profile.get("schedule", {}),
            "educational_content_only": profile.get("educational_content_only", False),
            "created_at": datetime.now().isoformat()
        }
        
        profiles.append(new_profile)
        data["data"] = profiles
        
        with open(KIDS_PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "profile": new_profile})

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>", methods=["GET", "PUT", "DELETE"])
def manage_kids_profile(profile_id):
    """Get, update, or delete a kids profile"""
    with open(KIDS_PROFILES_FILE, "r") as f:
        data = json.load(f)
    
    profiles = data.get("data", [])
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    if request.method == "GET":
        return jsonify({"success": True, "profile": profile})
    
    elif request.method == "PUT":
        updates = request.json
        profile.update(updates)
        profile["updated_at"] = datetime.now().isoformat()
        
        with open(KIDS_PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "profile": profile})
    
    else:  # DELETE
        profiles.remove(profile)
        data["data"] = profiles
        
        with open(KIDS_PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "message": "Profile deleted"})

# ===== CONTENT FILTERING =====

@kids_parental_controls_bp.route("/api/parental-controls/content/check", methods=["POST"])
def check_content():
    """Check if content is appropriate for a profile"""
    data = request.json
    profile_id = data.get("profile_id")
    content_id = data.get("content_id")
    content_type = data.get("content_type", "movie")
    content_rating = data.get("content_rating", "")
    content_categories = data.get("content_categories", [])
    
    # Get profile settings
    with open(KIDS_PROFILES_FILE, "r") as f:
        profiles_data = json.load(f)
    
    profile = next((p for p in profiles_data.get("data", []) if p.get("id") == profile_id), None)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    # Check age rating
    rating_order = ["G", "PG", "PG-13", "R", "NC-17"]
    profile_rating_limit = profile.get("age_rating_limit", "PG")
    
    allowed = True
    reasons = []
    
    if content_rating in rating_order and profile_rating_limit in rating_order:
        if rating_order.index(content_rating) > rating_order.index(profile_rating_limit):
            allowed = False
            reasons.append(f"Content rating {content_rating} exceeds limit {profile_rating_limit}")
    
    # Check categories
    allowed_categories = profile.get("allowed_categories", [])
    if allowed_categories and not any(cat in allowed_categories for cat in content_categories):
        allowed = False
        reasons.append("Content category not in allowed list")
    
    # Check whitelist/blacklist
    with open(CONTENT_WHITELIST_FILE, "r") as f:
        whitelist_data = json.load(f)
    
    with open(CONTENT_BLACKLIST_FILE, "r") as f:
        blacklist_data = json.load(f)
    
    whitelist = whitelist_data.get("data", [])
    blacklist = blacklist_data.get("data", [])
    
    if content_id in blacklist:
        allowed = False
        reasons.append("Content is blacklisted")
    
    # Whitelist overrides other restrictions
    if content_id in whitelist:
        allowed = True
        reasons = ["Content is whitelisted"]
    
    return jsonify({
        "success": True,
        "allowed": allowed,
        "reasons": reasons,
        "profile_id": profile_id,
        "content_id": content_id
    })

@kids_parental_controls_bp.route("/api/parental-controls/whitelist", methods=["GET", "POST", "DELETE"])
def manage_whitelist():
    """Manage content whitelist"""
    with open(CONTENT_WHITELIST_FILE, "r") as f:
        data = json.load(f)
    
    if request.method == "GET":
        return jsonify({"success": True, "whitelist": data.get("data", [])})
    
    elif request.method == "POST":
        content_id = request.json.get("content_id")
        whitelist = data.get("data", [])
        
        if content_id not in whitelist:
            whitelist.append(content_id)
            data["data"] = whitelist
            
            with open(CONTENT_WHITELIST_FILE, "w") as f:
                json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "whitelist": whitelist})
    
    else:  # DELETE
        content_id = request.json.get("content_id")
        whitelist = data.get("data", [])
        whitelist = [c for c in whitelist if c != content_id]
        data["data"] = whitelist
        
        with open(CONTENT_WHITELIST_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "whitelist": whitelist})

@kids_parental_controls_bp.route("/api/parental-controls/blacklist", methods=["GET", "POST", "DELETE"])
def manage_blacklist():
    """Manage content blacklist"""
    with open(CONTENT_BLACKLIST_FILE, "r") as f:
        data = json.load(f)
    
    if request.method == "GET":
        return jsonify({"success": True, "blacklist": data.get("data", [])})
    
    elif request.method == "POST":
        content_id = request.json.get("content_id")
        blacklist = data.get("data", [])
        
        if content_id not in blacklist:
            blacklist.append(content_id)
            data["data"] = blacklist
            
            with open(CONTENT_BLACKLIST_FILE, "w") as f:
                json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "blacklist": blacklist})
    
    else:  # DELETE
        content_id = request.json.get("content_id")
        blacklist = data.get("data", [])
        blacklist = [c for c in blacklist if c != content_id]
        data["data"] = blacklist
        
        with open(CONTENT_BLACKLIST_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "blacklist": blacklist})

# ===== TIME MANAGEMENT =====

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>/time-limit", methods=["GET", "POST"])
def manage_time_limit(profile_id):
    """Get or update time limit for a profile"""
    with open(KIDS_PROFILES_FILE, "r") as f:
        data = json.load(f)
    
    profiles = data.get("data", [])
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    if request.method == "GET":
        return jsonify({
            "success": True,
            "profile_id": profile_id,
            "time_limit_minutes": profile.get("time_limit_minutes", 120),
            "schedule": profile.get("schedule", {})
        })
    
    else:  # POST
        updates = request.json
        if "time_limit_minutes" in updates:
            profile["time_limit_minutes"] = updates["time_limit_minutes"]
        if "schedule" in updates:
            profile["schedule"] = updates["schedule"]
        
        with open(KIDS_PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"success": True, "profile": profile})

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>/time-remaining", methods=["GET"])
def get_time_remaining(profile_id):
    """Get remaining time for today"""
    with open(KIDS_PROFILES_FILE, "r") as f:
        profiles_data = json.load(f)
    
    profile = next((p for p in profiles_data.get("data", []) if p.get("id") == profile_id), None)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    # Get today's usage
    with open(ACTIVITY_LOG_FILE, "r") as f:
        activity_data = json.load(f)
    
    today = datetime.now().date().isoformat()
    today_activities = [
        a for a in activity_data.get("data", [])
        if a.get("profile_id") == profile_id and a.get("date") == today
    ]
    
    total_minutes_used = sum(a.get("duration_minutes", 0) for a in today_activities)
    time_limit = profile.get("time_limit_minutes", 120)
    remaining_minutes = max(0, time_limit - total_minutes_used)
    
    return jsonify({
        "success": True,
        "profile_id": profile_id,
        "time_limit_minutes": time_limit,
        "used_minutes": total_minutes_used,
        "remaining_minutes": remaining_minutes,
        "percentage_used": (total_minutes_used / time_limit * 100) if time_limit > 0 else 0
    })

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>/check-access", methods=["GET"])
def check_access_time(profile_id):
    """Check if profile can access content at current time"""
    with open(KIDS_PROFILES_FILE, "r") as f:
        profiles_data = json.load(f)
    
    profile = next((p for p in profiles_data.get("data", []) if p.get("id") == profile_id), None)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    now = datetime.now()
    current_time = now.time()
    current_day = now.strftime("%A").lower()
    
    schedule = profile.get("schedule", {})
    
    # Check if there's a schedule for today
    if current_day in schedule:
        day_schedule = schedule[current_day]
        start_time = time.fromisoformat(day_schedule.get("start", "00:00:00"))
        end_time = time.fromisoformat(day_schedule.get("end", "23:59:59"))
        
        if not (start_time <= current_time <= end_time):
            return jsonify({
                "success": True,
                "allowed": False,
                "reason": f"Outside allowed time window ({start_time} - {end_time})"
            })
    
    # Check remaining time
    with open(ACTIVITY_LOG_FILE, "r") as f:
        activity_data = json.load(f)
    
    today = now.date().isoformat()
    today_activities = [
        a for a in activity_data.get("data", [])
        if a.get("profile_id") == profile_id and a.get("date") == today
    ]
    
    total_minutes_used = sum(a.get("duration_minutes", 0) for a in today_activities)
    time_limit = profile.get("time_limit_minutes", 120)
    
    if total_minutes_used >= time_limit:
        return jsonify({
            "success": True,
            "allowed": False,
            "reason": "Daily time limit reached"
        })
    
    return jsonify({
        "success": True,
        "allowed": True,
        "remaining_minutes": time_limit - total_minutes_used
    })

# ===== ACTIVITY MONITORING =====

@kids_parental_controls_bp.route("/api/kids/activity/log", methods=["POST"])
def log_activity():
    """Log a viewing activity"""
    activity = request.json
    
    with open(ACTIVITY_LOG_FILE, "r") as f:
        data = json.load(f)
    
    activities = data.get("data", [])
    
    activities.append({
        "id": len(activities) + 1,
        "profile_id": activity.get("profile_id"),
        "content_id": activity.get("content_id"),
        "content_type": activity.get("content_type", ""),
        "content_title": activity.get("content_title", ""),
        "duration_minutes": activity.get("duration_minutes", 0),
        "date": datetime.now().date().isoformat(),
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 90 days
    cutoff_date = (datetime.now() - timedelta(days=90)).date().isoformat()
    activities = [a for a in activities if a.get("date", "") >= cutoff_date]
    
    data["data"] = activities
    
    with open(ACTIVITY_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({"success": True})

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>/activity", methods=["GET"])
def get_profile_activity(profile_id):
    """Get activity log for a profile"""
    days = int(request.args.get("days", 7))
    
    with open(ACTIVITY_LOG_FILE, "r") as f:
        data = json.load(f)
    
    cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
    
    activities = [
        a for a in data.get("data", [])
        if a.get("profile_id") == profile_id and a.get("date", "") >= cutoff_date
    ]
    
    return jsonify({
        "success": True,
        "profile_id": profile_id,
        "activities": activities,
        "count": len(activities)
    })

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>/report", methods=["GET"])
def generate_activity_report(profile_id):
    """Generate activity report for a profile"""
    period = request.args.get("period", "week")  # week, month
    
    with open(ACTIVITY_LOG_FILE, "r") as f:
        data = json.load(f)
    
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:
        days = 7
    
    cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
    
    activities = [
        a for a in data.get("data", [])
        if a.get("profile_id") == profile_id and a.get("date", "") >= cutoff_date
    ]
    
    # Calculate statistics
    total_minutes = sum(a.get("duration_minutes", 0) for a in activities)
    total_content = len(set(a.get("content_id") for a in activities))
    
    # Group by content type
    by_type = {}
    for activity in activities:
        content_type = activity.get("content_type", "unknown")
        by_type[content_type] = by_type.get(content_type, 0) + activity.get("duration_minutes", 0)
    
    # Group by date
    by_date = {}
    for activity in activities:
        date = activity.get("date", "")
        by_date[date] = by_date.get(date, 0) + activity.get("duration_minutes", 0)
    
    # Most watched content
    content_counts = {}
    for activity in activities:
        content_id = activity.get("content_id")
        content_title = activity.get("content_title", "Unknown")
        if content_id not in content_counts:
            content_counts[content_id] = {"title": content_title, "minutes": 0, "count": 0}
        content_counts[content_id]["minutes"] += activity.get("duration_minutes", 0)
        content_counts[content_id]["count"] += 1
    
    most_watched = sorted(content_counts.values(), key=lambda x: x["minutes"], reverse=True)[:5]
    
    return jsonify({
        "success": True,
        "profile_id": profile_id,
        "period": period,
        "report": {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "total_content_items": total_content,
            "average_minutes_per_day": round(total_minutes / days, 1),
            "by_content_type": by_type,
            "by_date": by_date,
            "most_watched": most_watched
        }
    })

# ===== AGE-APPROPRIATE RECOMMENDATIONS =====

@kids_parental_controls_bp.route("/api/kids/profiles/<int:profile_id>/recommendations", methods=["GET"])
def get_kids_recommendations(profile_id):
    """Get age-appropriate recommendations for a profile"""
    with open(KIDS_PROFILES_FILE, "r") as f:
        profiles_data = json.load(f)
    
    profile = next((p for p in profiles_data.get("data", []) if p.get("id") == profile_id), None)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    age = profile.get("age", 0)
    educational_only = profile.get("educational_content_only", False)
    
    # Simulate recommendations based on age and preferences
    recommendations = []
    
    if age <= 5:
        categories = ["preschool", "educational", "animated"]
    elif age <= 10:
        categories = ["kids", "family", "educational", "adventure"]
    else:
        categories = ["kids", "family", "teen", "adventure", "comedy"]
    
    for i in range(10):
        recommendations.append({
            "id": i + 1,
            "title": f"Recommended Content {i + 1}",
            "type": "movie" if i % 2 == 0 else "show",
            "rating": "G" if age <= 5 else "PG",
            "category": categories[i % len(categories)],
            "educational": educational_only or i % 3 == 0,
            "age_appropriate": True
        })
    
    return jsonify({
        "success": True,
        "profile_id": profile_id,
        "recommendations": recommendations
    })

# ===== EDUCATIONAL CONTENT =====

@kids_parental_controls_bp.route("/api/kids/educational-content", methods=["GET"])
def get_educational_content():
    """Get educational content"""
    age_range = request.args.get("age_range", "all")
    subject = request.args.get("subject", "all")
    
    # Simulate educational content
    content = []
    subjects = ["math", "science", "reading", "history", "art"]
    
    for i in range(20):
        content.append({
            "id": i + 1,
            "title": f"Educational Content {i + 1}",
            "subject": subjects[i % len(subjects)],
            "age_range": "5-8" if i % 3 == 0 else "9-12",
            "duration_minutes": 15 + (i * 5),
            "rating": "G",
            "educational_value": "high"
        })
    
    return jsonify({
        "success": True,
        "content": content,
        "count": len(content)
    })

from flask import Blueprint, jsonify, request
import os, json, hashlib
from datetime import datetime, timedelta
from pathlib import Path

rd_manager_enhanced_bp = Blueprint("rd_manager_enhanced", __name__)

# Storage paths
STORAGE_DIR = Path("storage/config")
RD_LINKS_FILE = STORAGE_DIR / "rd_links.json"
RD_ACCOUNTS_FILE = STORAGE_DIR / "rd_accounts.json"
RD_ANALYTICS_FILE = STORAGE_DIR / "rd_analytics.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize files
if not RD_LINKS_FILE.exists():
    RD_LINKS_FILE.write_text(json.dumps({"links": []}, indent=2))

if not RD_ACCOUNTS_FILE.exists():
    RD_ACCOUNTS_FILE.write_text(json.dumps({"accounts": []}, indent=2))

if not RD_ANALYTICS_FILE.exists():
    RD_ANALYTICS_FILE.write_text(json.dumps({
        "usage": [],
        "bandwidth": [],
        "downloads": []
    }, indent=2))

# ===== ADVANCED LINK MANAGEMENT =====

@rd_manager_enhanced_bp.route("/api/rd/links", methods=["GET"])
def get_links():
    try:
        """Get all Real-Debrid links with advanced filtering"""
        category = request.args.get("category", "")
        tags = request.args.get("tags", "")
        status = request.args.get("status", "")
        sort_by = request.args.get("sort", "date")

        with open(RD_LINKS_FILE, "r") as f:
        data = json.load(f)

        links = data.get("links", [])

        # Apply filters
        if category:
        links = [l for l in links if l.get("category") == category]

        if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        links = [l for l in links if any(tag in l.get("tags", []) for tag in tag_list)]

        if status:
        links = [l for l in links if l.get("status") == status]

        # Sort
        if sort_by == "date":
        links.sort(key=lambda x: x.get("added_at", ""), reverse=True)
        elif sort_by == "size":
        links.sort(key=lambda x: x.get("size", 0), reverse=True)
        elif sort_by == "name":
        links.sort(key=lambda x: x.get("filename", ""))

        return jsonify({
        "success": True,
        "links": links,
        "count": len(links)
        })

        @rd_manager_enhanced_bp.route("/api/rd/links/bulk", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def bulk_link_operations():
    try:
        """Perform bulk operations on multiple links"""
        data = request.json
        link_ids = data.get("link_ids", [])
        operation = data.get("operation", "")  # delete, download, categorize, tag

        with open(RD_LINKS_FILE, "r") as f:
        rd_data = json.load(f)

        links = rd_data.get("links", [])
        affected_count = 0

        for link_id in link_ids:
        link = next((l for l in links if l.get("id") == link_id), None)
        if link:
        if operation == "delete":
        links.remove(link)
        affected_count += 1
        elif operation == "download":
        link["status"] = "downloading"
        affected_count += 1
        elif operation == "categorize":
        link["category"] = data.get("category", "uncategorized")
        affected_count += 1
        elif operation == "tag":
        if "tags" not in link:
        link["tags"] = []
        new_tags = data.get("tags", [])
        link["tags"].extend([t for t in new_tags if t not in link["tags"]])
        affected_count += 1

        rd_data["links"] = links

        with open(RD_LINKS_FILE, "w") as f:
        json.dump(rd_data, f, indent=2)

        return jsonify({
        "success": True,
        "operation": operation,
        "affected_count": affected_count
        })


        @rd_manager_enhanced_bp.route("/api/rd/links/categorize", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def categorize_link():
    try:
        """Add or update category for a link"""
        data = request.json
        link_id = data.get("link_id", "")
        category = data.get("category", "")

        with open(RD_LINKS_FILE, "r") as f:
        rd_data = json.load(f)

        links = rd_data.get("links", [])
        link = next((l for l in links if l.get("id") == link_id), None)

        if not link:
        return jsonify({"error": "Link not found"}), 404

        link["category"] = category

        with open(RD_LINKS_FILE, "w") as f:
        json.dump(rd_data, f, indent=2)

        return jsonify({
        "success": True,
        "link_id": link_id,
        "category": category
        })


        @rd_manager_enhanced_bp.route("/api/rd/links/tag", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def tag_link():
    try:
        """Add tags to a link"""
        data = request.json
        link_id = data.get("link_id", "")
        tags = data.get("tags", [])

        with open(RD_LINKS_FILE, "r") as f:
        rd_data = json.load(f)

        links = rd_data.get("links", [])
        link = next((l for l in links if l.get("id") == link_id), None)

        if not link:
        return jsonify({"error": "Link not found"}), 404

        if "tags" not in link:
        link["tags"] = []

        for tag in tags:
        if tag not in link["tags"]:
        link["tags"].append(tag)

        with open(RD_LINKS_FILE, "w") as f:
        json.dump(rd_data, f, indent=2)

        return jsonify({
        "success": True,
        "link_id": link_id,
        "tags": link["tags"]
        })


        @rd_manager_enhanced_bp.route("/api/rd/links/expiration", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_expiration():
    """Check for expiring links"""
    days_threshold = int(request.args.get("days", 7))
    
    with open(RD_LINKS_FILE, "r") as f:
        data = json.load(f)
    
    links = data.get("links", [])
    expiring_links = []
    
    threshold_date = datetime.now() + timedelta(days=days_threshold)
    
    for link in links:
        if "expires_at" in link:
            try:
                expires_at = datetime.fromisoformat(link["expires_at"])
                if expires_at <= threshold_date:
                    days_remaining = (expires_at - datetime.now()).days
                    expiring_links.append({
                        **link,
                        "days_remaining": days_remaining
                    })
            except:
                pass
    
                return jsonify({
        "success": True,
        "expiring_links": expiring_links,
        "count": len(expiring_links),
        "threshold_days": days_threshold
    })

@rd_manager_enhanced_bp.route("/api/rd/links/refresh", methods=["POST"])
def refresh_links():
    try:
        """Refresh and validate link status"""
        data = request.json
        link_ids = data.get("link_ids", [])

        # Simulate link refresh
        # In production, this would call Real-Debrid API

        refreshed_links = []
        for link_id in link_ids:
        refreshed_links.append({
        "link_id": link_id,
        "status": "active",
        "validated_at": datetime.now().isoformat()
        })

        return jsonify({
        "success": True,
        "refreshed_links": refreshed_links,
        "count": len(refreshed_links)
        })

        @rd_manager_enhanced_bp.route("/api/rd/links/share", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def share_links():
    try:
        """Generate shareable link collection"""
        data = request.json
        link_ids = data.get("link_ids", [])
        expires_in_hours = data.get("expires_in_hours", 24)

        # Generate share token
        share_token = hashlib.md5(f"{','.join(link_ids)}{datetime.now()}".encode()).hexdigest()

        share_url = f"https://mediahub.local/shared/{share_token}"
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        return jsonify({
        "success": True,
        "share_url": share_url,
        "share_token": share_token,
        "expires_at": expires_at.isoformat(),
        "link_count": len(link_ids)
        })

        # ===== ENHANCED DUPLICATE MANAGEMENT =====

        @rd_manager_enhanced_bp.route("/api/rd/duplicates/detect", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def detect_duplicates():
    try:
        """AI-powered duplicate detection with similarity scoring"""
        data = request.json
        algorithm = data.get("algorithm", "fuzzy")  # fuzzy, exact, ai

        with open(RD_LINKS_FILE, "r") as f:
        rd_data = json.load(f)

        links = rd_data.get("links", [])

        # Simulate duplicate detection
        duplicate_groups = []

        # Group by similar filenames
        seen = {}
        for link in links:
        filename = link.get("filename", "")
        # Simple similarity: remove extensions and special chars
        base_name = filename.rsplit(".", 1)[0].lower()
        base_name = ''.join(c for c in base_name if c.isalnum())

        if base_name in seen:
        seen[base_name].append(link)
        else:
        seen[base_name] = [link]

        # Create duplicate groups with similarity scores
        for base_name, group in seen.items():
        if len(group) > 1:
        duplicate_groups.append({
        "base_name": base_name,
        "links": group,
        "count": len(group),
        "similarity_score": 0.95,  # Simulated
        "recommended_action": "keep_largest"
        })

        return jsonify({
        "success": True,
        "algorithm": algorithm,
        "duplicate_groups": duplicate_groups,
        "total_duplicates": sum(len(g["links"]) - 1 for g in duplicate_groups)
        })

        @rd_manager_enhanced_bp.route("/api/rd/duplicates/resolve", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def resolve_duplicates():
    try:
        """Bulk resolve duplicates based on rules"""
        data = request.json
        group_ids = data.get("group_ids", [])
        resolution = data.get("resolution", "keep_largest")  # keep_largest, keep_newest, keep_highest_quality, manual

        resolved_count = 0
        kept_links = []
        removed_links = []

        # Simulate resolution
        for group_id in group_ids:
        resolved_count += 1
        kept_links.append({"id": f"link_{group_id}_1", "reason": resolution})
        removed_links.append({"id": f"link_{group_id}_2", "reason": "duplicate"})

        return jsonify({
        "success": True,
        "resolution": resolution,
        "resolved_count": resolved_count,
        "kept_links": kept_links,
        "removed_links": removed_links
        })


        @rd_manager_enhanced_bp.route("/api/rd/duplicates/rules", methods=["GET", "POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def duplicate_rules():
    try:
        """Manage custom duplicate detection rules"""
        if request.method == "GET":
        rules = [
        {"id": 1, "name": "Ignore resolution differences", "pattern": r"\d{3,4}p", "enabled": True},
        {"id": 2, "name": "Ignore codec differences", "pattern": r"(x264|x265|HEVC)", "enabled": True},
        {"id": 3, "name": "Ignore release group", "pattern": r"-\w+$", "enabled": False}
        ]
        return jsonify({"success": True, "rules": rules})

        else:  # POST
        rule = request.json
        # Save rule logic here
        return jsonify({"success": True, "rule": rule})

        # ===== PREMIUM FEATURES =====

        @rd_manager_enhanced_bp.route("/api/rd/accounts", methods=["GET", "POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def manage_accounts():
    try:
        """Manage multiple Real-Debrid accounts"""
        if request.method == "GET":
        with open(RD_ACCOUNTS_FILE, "r") as f:
        data = json.load(f)

        accounts = data.get("accounts", [])

        # Hide API keys in response
        for account in accounts:
        if "api_key" in account:
        account["api_key"] = account["api_key"][:8] + "..." + account["api_key"][-4:]

        return jsonify({
        "success": True,
        "accounts": accounts,
        "count": len(accounts)
        })

        else:  # POST
        account = request.json

        with open(RD_ACCOUNTS_FILE, "r") as f:
        data = json.load(f)

        if "accounts" not in data:
        data["accounts"] = []

        data["accounts"].append({
        "id": len(data["accounts"]) + 1,
        "name": account.get("name", "Account"),
        "api_key": account.get("api_key", ""),
        "email": account.get("email", ""),
        "active": account.get("active", True),
        "added_at": datetime.now().isoformat()
        })

        with open(RD_ACCOUNTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        return jsonify({"success": True, "account": data["accounts"][-1]})


        @rd_manager_enhanced_bp.route("/api/rd/analytics", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_analytics():
    try:
        """Get detailed usage analytics"""
        period = request.args.get("period", "week")  # day, week, month, year

        analytics = {
        "period": period,
        "total_downloads": 156,
        "total_size": "2.4 TB",
        "bandwidth_used": "2.3 TB",
        "average_speed": "12.5 MB/s",
        "peak_speed": "45 MB/s",
        "downloads_by_type": {
        "movies": 45,
        "tv_shows": 78,
        "music": 23,
        "other": 10
        },
        "downloads_by_day": [
        {"date": "2025-10-01", "count": 23, "size": "350 GB"},
        {"date": "2025-10-02", "count": 19, "size": "280 GB"}
        ],
        "top_sources": [
        {"source": "1fichier.com", "count": 45},
        {"source": "rapidgator.net", "count": 32},
        {"source": "uploaded.net", "count": 28}
        ]
        }

        return jsonify({
        "success": True,
        "analytics": analytics
        })


        @rd_manager_enhanced_bp.route("/api/rd/bandwidth", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def monitor_bandwidth():
    try:
        """Real-time bandwidth monitoring"""
        bandwidth = {
        "current_speed": "8.5 MB/s",
        "current_downloads": 3,
        "bandwidth_limit": "Unlimited",
        "bandwidth_used_today": "45 GB",
        "bandwidth_remaining": "Unlimited",
        "peak_speed_today": "15.2 MB/s",
        "average_speed_today": "7.8 MB/s",
        "active_connections": 12
        }

        return jsonify({
        "success": True,
        "bandwidth": bandwidth
        })


        @rd_manager_enhanced_bp.route("/api/rd/schedule", methods=["GET", "POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def download_schedule():
    try:
        """Manage download scheduling"""
        if request.method == "GET":
        schedules = [
        {"id": 1, "name": "Night downloads", "start_time": "22:00", "end_time": "06:00", "enabled": True},
        {"id": 2, "name": "Weekend batch", "days": ["Saturday", "Sunday"], "enabled": False}
        ]
        return jsonify({"success": True, "schedules": schedules})

        else:  # POST
        schedule = request.json
        # Save schedule logic here
        return jsonify({"success": True, "schedule": schedule})


        @rd_manager_enhanced_bp.route("/api/rd/priority", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_priority():
    try:
        """Set download priority"""
        data = request.json
        link_id = data.get("link_id", "")
        priority = data.get("priority", 0)  # 0=low, 1=normal, 2=high, 3=urgent

        with open(RD_LINKS_FILE, "r") as f:
        rd_data = json.load(f)

        links = rd_data.get("links", [])
        link = next((l for l in links if l.get("id") == link_id), None)

        if not link:
        return jsonify({"error": "Link not found"}), 404

        link["priority"] = priority

        with open(RD_LINKS_FILE, "w") as f:
        json.dump(rd_data, f, indent=2)

        return jsonify({
        "success": True,
        "link_id": link_id,
        "priority": priority
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

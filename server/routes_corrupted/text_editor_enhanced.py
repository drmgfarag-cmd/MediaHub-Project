from flask import Blueprint, jsonify, request
import os, json, re
from datetime import datetime
from pathlib import Path

text_editor_enhanced_bp = Blueprint("text_editor_enhanced", __name__)

# Storage paths
STORAGE_DIR = Path("storage/config")
EDITOR_SESSIONS_FILE = STORAGE_DIR / "editor_sessions.json"
EDITOR_MACROS_FILE = STORAGE_DIR / "editor_macros.json"
EDITOR_PLUGINS_FILE = STORAGE_DIR / "editor_plugins.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize files
if not EDITOR_SESSIONS_FILE.exists():
    EDITOR_SESSIONS_FILE.write_text(json.dumps({"sessions": []}, indent=2))

if not EDITOR_MACROS_FILE.exists():
    EDITOR_MACROS_FILE.write_text(json.dumps({"macros": []}, indent=2))

if not EDITOR_PLUGINS_FILE.exists():
    EDITOR_PLUGINS_FILE.write_text(json.dumps({"plugins": []}, indent=2))

# ===== ADVANCED EDITING FEATURES =====

@text_editor_enhanced_bp.route("/api/editor/sessions", methods=["GET", "POST"])
def manage_sessions():
    try:
        """Manage multi-document editing sessions"""
        if request.method == "GET":
        with open(EDITOR_SESSIONS_FILE, "r") as f:
        data = json.load(f)
        return jsonify({"success": True, "sessions": data.get("sessions", [])})

        else:  # POST
        session = request.json

        with open(EDITOR_SESSIONS_FILE, "r") as f:
        data = json.load(f)

        if "sessions" not in data:
        data["sessions"] = []

        new_session = {
        "id": len(data["sessions"]) + 1,
        "name": session.get("name", "Untitled Session"),
        "files": session.get("files", []),
        "active_file": session.get("active_file", ""),
        "cursor_positions": session.get("cursor_positions", {}),
        "bookmarks": session.get("bookmarks", {}),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
        }

        data["sessions"].append(new_session)

        with open(EDITOR_SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        return jsonify({"success": True, "session": new_session})


        @text_editor_enhanced_bp.route("/api/editor/sessions/<int:session_id>", methods=["PUT", "DELETE"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_session(session_id):
    try:
        """Update or delete a session"""
        with open(EDITOR_SESSIONS_FILE, "r") as f:
        data = json.load(f)

        sessions = data.get("sessions", [])
        session = next((s for s in sessions if s.get("id") == session_id), None)

        if not session:
        return jsonify({"error": "Session not found"}), 404

        if request.method == "PUT":
        updates = request.json
        session.update(updates)
        session["updated_at"] = datetime.now().isoformat()

        with open(EDITOR_SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        return jsonify({"success": True, "session": session})

        else:  # DELETE
        sessions.remove(session)
        data["sessions"] = sessions

        with open(EDITOR_SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        return jsonify({"success": True, "message": "Session deleted"})


        @text_editor_enhanced_bp.route("/api/editor/compare", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def compare_files():
    try:
        """Compare two files side-by-side"""
        data = request.json
        file1 = data.get("file1", "")
        file2 = data.get("file2", "")

        # Simulate file comparison
        # In production, use difflib or similar

        differences = [
        {"line": 10, "type": "modified", "file1": "old content", "file2": "new content"},
        {"line": 25, "type": "added", "file1": "", "file2": "added line"},
        {"line": 42, "type": "deleted", "file1": "deleted line", "file2": ""}
        ]

        return jsonify({
        "success": True,
        "file1": file1,
        "file2": file2,
        "differences": differences,
        "total_changes": len(differences)
        })

        @text_editor_enhanced_bp.route("/api/editor/macros", methods=["GET", "POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def manage_macros():
    try:
        """Manage macro recording and playback"""
        if request.method == "GET":
        with open(EDITOR_MACROS_FILE, "r") as f:
        data = json.load(f)
        return jsonify({"success": True, "macros": data.get("macros", [])})

        else:  # POST
        macro = request.json

        with open(EDITOR_MACROS_FILE, "r") as f:
        data = json.load(f)

        if "macros" not in data:
        data["macros"] = []

        new_macro = {
        "id": len(data["macros"]) + 1,
        "name": macro.get("name", "Untitled Macro"),
        "description": macro.get("description", ""),
        "actions": macro.get("actions", []),
        "shortcut": macro.get("shortcut", ""),
        "created_at": datetime.now().isoformat()
        }

        data["macros"].append(new_macro)

        with open(EDITOR_MACROS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        return jsonify({"success": True, "macro": new_macro})


        @text_editor_enhanced_bp.route("/api/editor/macros/<int:macro_id>/execute", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def execute_macro(macro_id):
    try:
        """Execute a recorded macro"""
        with open(EDITOR_MACROS_FILE, "r") as f:
        data = json.load(f)

        macros = data.get("macros", [])
        macro = next((m for m in macros if m.get("id") == macro_id), None)

        if not macro:
        return jsonify({"error": "Macro not found"}), 404

        # Simulate macro execution
        actions_executed = len(macro.get("actions", []))

        return jsonify({
        "success": True,
        "macro_id": macro_id,
        "macro_name": macro.get("name"),
        "actions_executed": actions_executed
        })

        @text_editor_enhanced_bp.route("/api/editor/plugins", methods=["GET", "POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def manage_plugins():
    try:
        """Manage editor plugins"""
        if request.method == "GET":
        with open(EDITOR_PLUGINS_FILE, "r") as f:
        data = json.load(f)
        return jsonify({"success": True, "plugins": data.get("plugins", [])})

        else:  # POST
        plugin = request.json

        with open(EDITOR_PLUGINS_FILE, "r") as f:
        data = json.load(f)

        if "plugins" not in data:
        data["plugins"] = []

        new_plugin = {
        "id": len(data["plugins"]) + 1,
        "name": plugin.get("name", "Untitled Plugin"),
        "description": plugin.get("description", ""),
        "version": plugin.get("version", "1.0.0"),
        "author": plugin.get("author", ""),
        "enabled": plugin.get("enabled", True),
        "settings": plugin.get("settings", {}),
        "installed_at": datetime.now().isoformat()
        }

        data["plugins"].append(new_plugin)

        with open(EDITOR_PLUGINS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        return jsonify({"success": True, "plugin": new_plugin})


        @text_editor_enhanced_bp.route("/api/editor/fold", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def code_folding():
    try:
        """Get code folding regions"""
        data = request.json
        content = data.get("content", "")
        language = data.get("language", "")

        # Simulate code folding detection
        # In production, parse code structure

        fold_regions = [
        {"start_line": 5, "end_line": 15, "type": "function"},
        {"start_line": 20, "end_line": 45, "type": "class"},
        {"start_line": 50, "end_line": 60, "type": "block"}
        ]

        return jsonify({
        "success": True,
        "language": language,
        "fold_regions": fold_regions
        })


        @text_editor_enhanced_bp.route("/api/editor/autocomplete", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def advanced_autocomplete():
    try:
        """Context-aware auto-completion"""
        data = request.json
        content = data.get("content", "")
        cursor_position = data.get("cursor_position", 0)
        language = data.get("language", "")

        # Simulate auto-completion
        suggestions = [
        {"text": "function", "type": "keyword", "description": "Function declaration"},
        {"text": "for", "type": "keyword", "description": "For loop"},
        {"text": "forEach", "type": "method", "description": "Array iteration method"}
        ]

        return jsonify({
        "success": True,
        "suggestions": suggestions
        })

        # ===== TEXT MANIPULATION TOOLS =====

        @text_editor_enhanced_bp.route("/api/editor/transform/case", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def transform_case():
    try:
        """Transform text case"""
        data = request.json
        text = data.get("text", "")
        transformation = data.get("transformation", "uppercase")  # uppercase, lowercase, titlecase, camelcase, snakecase

        if transformation == "uppercase":
        result = text.upper()
        elif transformation == "lowercase":
        result = text.lower()
        elif transformation == "titlecase":
        result = text.title()
        elif transformation == "camelcase":
        words = re.sub(r'[^a-zA-Z0-9]', ' ', text).split()
        result = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
        elif transformation == "snakecase":
        result = re.sub(r'[^a-zA-Z0-9]', '_', text).lower()
        else:
        result = text

        return jsonify({
        "success": True,
        "original": text,
        "transformed": result,
        "transformation": transformation
        })


        @text_editor_enhanced_bp.route("/api/editor/transform/encoding", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def transform_encoding():
    try:
        """Detect and convert text encoding"""
        data = request.json
        text = data.get("text", "")
        target_encoding = data.get("target_encoding", "utf-8")

        # Simulate encoding detection and conversion
        detected_encoding = "utf-8"

        return jsonify({
        "success": True,
        "detected_encoding": detected_encoding,
        "target_encoding": target_encoding,
        "converted": True
        })


        @text_editor_enhanced_bp.route("/api/editor/regex/builder", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def regex_builder():
    """Build and test regular expressions"""
    data = request.json
    pattern = data.get("pattern", "")
    test_string = data.get("test_string", "")
    flags = data.get("flags", "")
    
    try:
        # Compile regex
        regex_flags = 0
        if 'i' in flags:
            regex_flags |= re.IGNORECASE
        if 'm' in flags:
            regex_flags |= re.MULTILINE
        if 's' in flags:
            regex_flags |= re.DOTALL
        
        compiled_pattern = re.compile(pattern, regex_flags)
        matches = compiled_pattern.findall(test_string)
        
        return jsonify({
            "success": True,
            "pattern": pattern,
            "matches": matches,
            "match_count": len(matches),
            "valid": True
        })
    
    except re.error as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "valid": False
        })

@text_editor_enhanced_bp.route("/api/editor/stats", methods=["POST"])
def text_statistics():
    try:
        """Calculate text statistics"""
        data = request.json
        text = data.get("text", "")

        words = text.split()
        lines = text.split('\n')
        characters = len(text)
        characters_no_spaces = len(text.replace(' ', ''))

        # Simple readability score (Flesch Reading Ease approximation)
        sentences = len(re.split(r'[.!?]+', text))
        syllables = sum(len(re.findall(r'[aeiou]', word.lower())) for word in words)

        if sentences > 0 and len(words) > 0:
        readability = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))
        else:
        readability = 0

        stats = {
        "characters": characters,
        "characters_no_spaces": characters_no_spaces,
        "words": len(words),
        "lines": len(lines),
        "sentences": sentences,
        "paragraphs": len([p for p in text.split('\n\n') if p.strip()]),
        "average_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0,
        "readability_score": round(readability, 2)
        }

        return jsonify({
        "success": True,
        "stats": stats
        })


        @text_editor_enhanced_bp.route("/api/editor/column", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def column_mode():
    try:
        """Enable column mode editing"""
        data = request.json
        text = data.get("text", "")
        start_column = data.get("start_column", 0)
        end_column = data.get("end_column", 10)
        operation = data.get("operation", "select")  # select, insert, delete

        lines = text.split('\n')
        result_lines = []

        if operation == "select":
        for line in lines:
        if len(line) >= start_column:
        selected = line[start_column:min(end_column, len(line))]
        result_lines.append(selected)

        elif operation == "insert":
        insert_text = data.get("insert_text", "")
        for line in lines:
        new_line = line[:start_column] + insert_text + line[start_column:]
        result_lines.append(new_line)

        elif operation == "delete":
        for line in lines:
        if len(line) >= start_column:
        new_line = line[:start_column] + line[min(end_column, len(line)):]
        result_lines.append(new_line)
        else:
        result_lines.append(line)

        return jsonify({
        "success": True,
        "operation": operation,
        "result": '\n'.join(result_lines)
        })

        # ===== PROGRAMMING SUPPORT =====

        @text_editor_enhanced_bp.route("/api/editor/languages", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_supported_languages():
    try:
        """Get list of supported programming languages"""
        languages = [
        {"id": "javascript", "name": "JavaScript", "extensions": [".js", ".jsx"]},
        {"id": "python", "name": "Python", "extensions": [".py"]},
        {"id": "java", "name": "Java", "extensions": [".java"]},
        {"id": "csharp", "name": "C#", "extensions": [".cs"]},
        {"id": "cpp", "name": "C++", "extensions": [".cpp", ".h"]},
        {"id": "php", "name": "PHP", "extensions": [".php"]},
        {"id": "ruby", "name": "Ruby", "extensions": [".rb"]},
        {"id": "go", "name": "Go", "extensions": [".go"]},
        {"id": "rust", "name": "Rust", "extensions": [".rs"]},
        {"id": "typescript", "name": "TypeScript", "extensions": [".ts", ".tsx"]},
        {"id": "html", "name": "HTML", "extensions": [".html", ".htm"]},
        {"id": "css", "name": "CSS", "extensions": [".css", ".scss", ".sass"]},
        {"id": "json", "name": "JSON", "extensions": [".json"]},
        {"id": "xml", "name": "XML", "extensions": [".xml"]},
        {"id": "yaml", "name": "YAML", "extensions": [".yml", ".yaml"]},
        {"id": "markdown", "name": "Markdown", "extensions": [".md"]},
        {"id": "sql", "name": "SQL", "extensions": [".sql"]},
        {"id": "bash", "name": "Bash", "extensions": [".sh"]},
        {"id": "powershell", "name": "PowerShell", "extensions": [".ps1"]},
        {"id": "swift", "name": "Swift", "extensions": [".swift"]}
        ]

        return jsonify({
        "success": True,
        "languages": languages,
        "count": len(languages)
        })

        @text_editor_enhanced_bp.route("/api/editor/format", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def format_code():
    try:
        """Format/beautify code"""
        data = request.json
        code = data.get("code", "")
        language = data.get("language", "")

        # Simulate code formatting
        # In production, use language-specific formatters

        formatted_code = code  # Placeholder

        return jsonify({
        "success": True,
        "language": language,
        "formatted_code": formatted_code
        })


        @text_editor_enhanced_bp.route("/api/editor/validate", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def validate_code():
    try:
        """Validate code and highlight errors"""
        data = request.json
        code = data.get("code", "")
        language = data.get("language", "")

        # Simulate code validation
        errors = []
        warnings = []

        # Example error
        if "undefined" in code:
        errors.append({
        "line": 10,
        "column": 5,
        "message": "Variable 'undefined' is not defined",
        "severity": "error"
        })

        return jsonify({
        "success": True,
        "language": language,
        "errors": errors,
        "warnings": warnings,
        "valid": len(errors) == 0
        })

        @text_editor_enhanced_bp.route("/api/editor/functions", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def extract_functions():
    try:
        """Extract function list for navigation"""
        data = request.json
        code = data.get("code", "")
        language = data.get("language", "")

        # Simulate function extraction
        functions = [
        {"name": "main", "line": 1, "type": "function"},
        {"name": "processData", "line": 15, "type": "function"},
        {"name": "validateInput", "line": 30, "type": "function"}
        ]

        return jsonify({
        "success": True,
        "language": language,
        "functions": functions
        })


        @text_editor_enhanced_bp.route("/api/editor/brackets", methods=["POST"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def match_brackets():
    try:
        """Find matching brackets"""
        data = request.json
        code = data.get("code", "")
        position = data.get("position", 0)

        # Simulate bracket matching
        matching_position = position + 10  # Placeholder

        return jsonify({
        "success": True,
        "position": position,
        "matching_position": matching_position,
        "bracket_type": "curly"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

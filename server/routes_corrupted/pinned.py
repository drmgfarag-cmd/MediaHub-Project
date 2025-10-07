
from flask import Blueprint, jsonify, request
import os, json

pin_bp = Blueprint('pin', __name__)
STO = os.environ.get('MH_STORAGE','storage')
CFG = os.path.join(STO, 'pinned.json')

DEFAULTS = {
  "Movies": ["Documentaries", "Stand-Up"],
  "TV": ["Documentaries", "Stand-Up"],
  "Books": ["eBooks", "Comics", "Manga", "Audiobooks"],
  "Audio": []
}

# Map a pinned rail name to a lightweight query string the UI can pass to /api/ui/search
QUERIES = {
  "Documentaries": "type:any tag:Documentary OR token:Documentary|Docs|Docu",
  "Stand-Up": "type:any token:Standup|Stand-up|Comedy.Special|Special",
  "eBooks": "type:book ext:epub|pdf -cbz -cbr",
  "Comics": "type:book ext:cbz|cbr -manga",
  "Manga": "type:book (ext:cbz|cbr) token:Manga",
  "Audiobooks": "type:book ext:m4b|mp3 folder:Audiobooks"
}

def _load():
  if not os.path.exists(CFG):
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    with open(CFG,'w',encoding='utf-8') as f: json.dump(DEFAULTS, f, indent=2)
    return DEFAULTS.copy()
  try:
      return json.load(open(CFG,'r',encoding='utf-8'))
  except:
      return DEFAULTS.copy()

def _save(d): 
  os.makedirs(os.path.dirname(CFG), exist_ok=True)
  with open(CFG,'w',encoding='utf-8') as f: json.dump(d, f, indent=2)

@pin_bp.route('/api/pinned/list')
def list_pinned():
  try:
      cat = request.args.get('cat','Movies')
      cfg = _load()
      names = cfg.get(cat, DEFAULTS.get(cat, []))
      rails = [{"title": n, "q": QUERIES.get(n,"") } for n in names]
      return jsonify({"ok": True, "category": cat, "rails": rails})


      @pin_bp.route('/api/pinned/toggle', methods=['POST'])
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}), 500

def toggle_pinned():
  try:
      js = request.get_json(force=True) or {}
      cat = js.get('cat','Movies')
      name = js.get('name')
      on = bool(js.get('on', True))
      if not name: return jsonify({"ok": False, "error":"missing name"}), 400
      cfg = _load()
      arr = cfg.get(cat, [])
      if on and name not in arr:
      arr.append(name)
      if not on and name in arr:
      arr.remove(name)
      cfg[cat] = arr
      _save(cfg)
      return jsonify({"ok": True, "category": cat, "pinned": arr})
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}), 500

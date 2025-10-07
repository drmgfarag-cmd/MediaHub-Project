from flask import Blueprint, jsonify, request
import os, json, re, time

ui_bp = Blueprint('ui', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
LIB=os.path.join(STO,'library_index.json')
RCF=os.path.join(STO,'ui_rails.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default

def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@ui_bp.route('/api/ui/search', methods=['POST'])
def search():
    try:
        js=request.get_json(silent=True) or {}
        q=(js.get('q') or '').strip().lower()
        types=js.get('types') or []  # movie|series|book|audio
        limit=int(js.get('limit') or 25)
        data=_load(LIB, [])
        out=[]
        for it in data:
        if types and (it.get('type') not in types): continue
        t=(it.get('title') or '').lower()
        p=(os.path.basename(it.get('path') or '')).lower()
        if not q or (q in t or q in p):
        out.append({"title": it.get('title') or os.path.basename(it.get('path') or ''),
        "type": it.get('type') or "other",
        "year": it.get('year') or "",
        "path": it.get('path') or ""})
        if len(out)>=limit: break
        return jsonify({"items": out})


        @ui_bp.route('/api/ui/palette_get')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def palette_get():
    try:
        # Static + conditional commands; client navigates based on "href" or runs simple GETs
        cmds=[
        {"id":"goto_home","label":"Go to Home","href":"/home.html"},
        {"id":"goto_discovery","label":"Go to Discovery","href":"/discovery.html"},
        {"id":"goto_downloader","label":"Go to Downloader","href":"/downloader.html"},
        {"id":"goto_wanted","label":"Go to Wanted Tracker","href":"/wanted.html"},
        {"id":"goto_tools","label":"Open Tools","href":"/tools.html"},
        {"id":"run_auto_refresh","label":"Smart Rails: Refresh Auto Picks","href":"/api/auto/rails_refresh","method":"POST"}
        ]
        return jsonify({"commands": cmds})


        @ui_bp.route('/api/ui/rails_config_get')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rails_get():
    try:
        return jsonify(_load(RCF, {}))

        @ui_bp.route('/api/ui/rails_config_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rails_set():
    try:
        js=request.get_json(silent=True) or {}
        cur=_load(RCF, {})
        for k,v in js.items():
        cur[k]=v
        _save(RCF, cur)
        return jsonify({"ok":True,"ui_rails":cur})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

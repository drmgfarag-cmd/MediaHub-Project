from flask import Blueprint, jsonify, request
import os, json

i18n_bp = Blueprint('i18n', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
DIR=os.path.join(STO,'i18n')

def _ensure():
    os.makedirs(DIR, exist_ok=True)
    base=os.path.join(DIR,'EN.json')
    if not os.path.exists(base):
        json.dump({
            "home": "Home", "tools": "Tools", "settings": "Settings",
            "downloads": "Downloads", "collections": "Collections",
            "smart_playlists": "Smart Playlists", "discovery": "Discovery",
            "profiles": "Profiles", "playlists": "Playlists", "editor": "Editor"
        }, open(base,'w',encoding='utf-8'), indent=2)

@i18n_bp.route('/api/i18n/get')
def get_():
    _ensure()
    lang=(request.args.get('lang') or 'EN').upper()
    path=os.path.join(DIR, f'{lang}.json')
    if not os.path.exists(path):
        path=os.path.join(DIR,'EN.json')
    try:
        return jsonify(json.load(open(path,'r',encoding='utf-8')))
    except Exception:
        return jsonify({})

@i18n_bp.route('/api/i18n/set', methods=['POST'])
def set_():
    _ensure()
    js=request.get_json(silent=True) or {}
    lang=(js.get('lang') or 'EN').upper()
    data=js.get('data') or {}
    path=os.path.join(DIR, f'{lang}.json')
    tmp=path+'.tmp'; json.dump(data, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)
        return jsonify({'ok':True})

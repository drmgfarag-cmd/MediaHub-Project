from flask import Blueprint, jsonify, request
import os, json, time
ed_bp = Blueprint('ed', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
EDS=os.path.join(STO,'editor.json')
SMP=os.path.join(STO,'samples')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@ed_bp.route('/api/editor/monaco_update', methods=['POST'])
def monaco_update():
    ed=_load(EDS, {}); ed['monaco_version']='fallback'; ed['updated_at']=int(time.time()); _save(EDS, ed)
    return jsonify({'ok':True,'monaco_version': ed['monaco_version']})

@ed_bp.route('/api/editor/open')
def open_file():
    path=(request.args.get('path') or '').strip()
    if not path: return jsonify({'error':'path'}), 400
    # Restrict to storage/samples for safety
    if not path.startswith('storage/samples/'): return jsonify({'error':'restricted'}), 403
    ab=os.path.join(ROOT, path)
    try: txt=open(ab,'r',encoding='utf-8', errors='ignore').read()
    except Exception: txt=''
    return jsonify({'path': path, 'content': txt})

@ed_bp.route('/api/editor/save', methods=['POST'])
def save_file():
    js=request.get_json(silent=True) or {}
    path=(js.get('path') or '').strip()
    txt=js.get('content') or ''
    if not path or not path.startswith('storage/samples/'): return jsonify({'error':'restricted'}), 403
    ab=os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(ab), exist_ok=True)
    open(ab,'w',encoding='utf-8').write(txt)
    return jsonify({'ok':True})

from flask import Blueprint, jsonify, request
import os, json

editor_bp = Blueprint('ed', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
    except Exception: return {}

@editor_bp.route('/api/editor/settings_get')
def get():
    return jsonify(_cfg().get('editor',{}))

@editor_bp.route('/api/editor/settings_set', methods=['POST'])
def set_():
    js=request.get_json(silent=True) or {}
    cfg=_cfg(); cfg['editor']=cfg.get('editor',{})
    for k in ('engine','encoding','language','wrap','show_line_numbers'):
        if k in js: cfg['editor'][k]=js[k]
    json.dump(cfg, open(CFG,'w',encoding='utf-8'), indent=2)
    return jsonify({'ok':True})

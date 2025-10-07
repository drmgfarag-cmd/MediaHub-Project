from flask import Blueprint, jsonify, request
import os, json
feat_bp = Blueprint('feat', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
CFG=os.path.join(ROOT,'storage','config.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@feat_bp.route('/api/features/get')
def get_():
    try:
        return jsonify((_load(CFG, {})).get('features',{}))

        @feat_bp.route('/api/features/set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_():
    try:
        js=request.get_json(silent=True) or {}
        cfg=_load(CFG, {}); f=cfg.get('features',{}); f.update(js); cfg['features']=f; _save(CFG, cfg); return jsonify({'ok':True,'features': f})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

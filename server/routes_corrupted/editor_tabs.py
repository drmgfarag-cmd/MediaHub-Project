from flask import Blueprint, jsonify, request
import os, json, time
tb_bp = Blueprint('tabs', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
TABS=os.path.join(STO,'editor_tabs.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@tb_bp.route('/api/editor/tabs')
def tabs_get():
    try:
        return jsonify(_load(TABS, {'tabs': [], 'active': ''}))

        @tb_bp.route('/api/editor/tabs_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def tabs_set():
    try:
        js=request.get_json(silent=True) or {}
        _save(TABS, js); return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

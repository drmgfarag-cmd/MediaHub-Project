from flask import Blueprint, jsonify, request
import os, json, time
cat_bp = Blueprint('cat', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CAT=os.path.join(STO,'lists_catalog.json')

def _load(): 
    try: return json.load(open(CAT,'r',encoding='utf-8'))
        except Exception: return {'lists':[], 'refresh_sec': 86400}

def _save(obj):
    json.dump(obj, open(CAT+'.tmp','w',encoding='utf-8'), indent=2); os.replace(CAT+'.tmp', CAT)

@cat_bp.route('/api/lists/catalog')
def get_():
    try:
        return jsonify(_load())

        @cat_bp.route('/api/lists/catalog_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_():
    try:
        js=request.get_json(silent=True) or {}
        db=_load()
        if 'refresh_sec' in js: db['refresh_sec']=int(js['refresh_sec'])
        if 'lists' in js: db['lists']=js['lists']
        db['ts']=int(time.time()); _save(db)
        return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

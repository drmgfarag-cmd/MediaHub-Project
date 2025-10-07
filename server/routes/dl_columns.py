from flask import Blueprint, jsonify, request
import os, json

col_bp = Blueprint('col', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CF=os.path.join(STO,'dl_columns.json')

JD_DEFAULT = ["Name","Size","Progress","Speed","ETA","Status","Save To","Added","Priority","Attempts"]

def _load():
    try: return json.load(open(CF,'r',encoding='utf-8'))
    except Exception: return {'order': JD_DEFAULT, 'hidden': []}

def _save(obj):
    tmp=CF+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, CF)

@col_bp.route('/api/dl/columns_get')
def get():
    return jsonify(_load())

@col_bp.route('/api/dl/columns_set', methods=['POST'])
def set_():
    js=request.get_json(silent=True) or {}
    dat=_load()
    if 'order' in js: dat['order'] = [c for c in js.get('order') if isinstance(c, str)]
    if 'hidden' in js: dat['hidden'] = [c for c in js.get('hidden') if isinstance(c, str)]
    _save(dat); return jsonify({'ok':True})

@col_bp.route('/api/dl/columns_preset', methods=['POST'])
def preset():
    js=request.get_json(silent=True) or {}
    name=(js.get('name') or '').lower()
    dat=_load()
    if name in ('jd','default','jd_default'):
        dat={'order': JD_DEFAULT, 'hidden': []}
    _save(dat); return jsonify({'ok':True,'applied': name})

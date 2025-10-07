from flask import Blueprint, jsonify, request
import os, json, re
from .lib import load_index

sp_bp = Blueprint('smartpl', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
PL=os.path.join(STO,'smart_playlists.json')

def _load():
    try: return json.load(open(PL,'r',encoding='utf-8'))
        except Exception: return {'lists': []}

def _save(obj):
    tmp=PL+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, PL)

@sp_bp.route('/api/smartplaylists/list')
def list_():
try:
    return jsonify(_load())

    @sp_bp.route('/api/smartplaylists/set', methods=['POST'])
except Exception as e:
    return jsonify({'success': False, 'error': str(e)}), 500

def set_():
    try:
        js=request.get_json(silent=True) or {'lists':[]}
        _save(js); return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _match(it, r):
    # r: {name, rules: [{field, op, value}], type: movie|series|ebook|comic|manga|audiobook|audio}
        if r.get('type') and it.get('type')!=r['type']: return False
    for cond in r.get('rules', []):
        f=cond.get('field'); op=cond.get('op'); val=cond.get('value')
        tv=(it.get(f) if f in it else (it.get('meta',{}) or {}).get(f))
        t=(tv or '')
        if f=='path_re':
        if not re.search(val or '', it.get('path',''), re.I): return False
            continue
        if f=='genre':
            gs=[g.lower() for g in (it.get('genres') or [])]
            want=[w.strip().lower() for w in (val or '').split(',') if w.strip()]
        if op=='has_any' and not any(w in gs for w in want): return False
            if op=='has_all' and not all(w in gs for w in want): return False
            if op=='not_any' and any(w in gs for w in want): return False
            continue
        if f=='year':
            y=it.get('year') or 0
            if op=='>=' and not (y>=int(val)): return False
            if op=='<=' and not (y<=int(val)): return False
            if op=='between':
                a,b=[int(x) for x in (val or '0,9999').split(',')[:2]]
                if not (a<=y<=b): return False
            continue
        if f=='is_kids':
            want=bool(val) if isinstance(val,bool) else str(val).lower() in ('1','true','yes')
            if bool(it.get('is_kids'))!=want: return False
            continue
        # generic contains/not contains on title/path
        if f in ('title','path'):
            s=(val or '').lower()
            t=(it.get(f) or '').lower()
            if op=='contains' and s not in t: return False
            if op=='not_contains' and s in t: return False
            continue
    return True

def _items():
    # prefer JSON index (compat); could be swapped to SQLite later
    try: return json.load(open(os.path.join(STO,'library_index.json'),'r',encoding='utf-8'))
        except Exception: return []

@sp_bp.route('/api/smartplaylists/eval')
def eval_():
    try:
        name=request.args.get('name','')
        db=_load()
        for l in db.get('lists',[]):
        if l.get('name')==name:
        items=[it for it in _items() if _match(it,l)]
        return jsonify({'ok':True,'items':items[:500]})
        return jsonify({'error':'not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

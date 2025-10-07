from flask import Blueprint, jsonify, request
import os, json, re
col_bp = Blueprint('collections', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); STO=os.path.join(ROOT,'storage'); LIB=os.path.join(STO,'library_index.json'); COL=os.path.join(STO,'collections.json')
def _load(p,d): 
    try: return json.load(open(p,'r',encoding='utf-8'))
    except: return d
@col_bp.route('/api/collections/list')
def list_col(): return jsonify(_load(COL, {"rules":[]}))
@col_bp.route('/api/collections/run')
def run():
    rules=_load(COL, {"rules":[]}).get('rules',[]); lib=_load(LIB,[])
    out=[]
    for r in rules:
        name=r.get('name','Collection')
        rx=re.compile(r.get('path_re','.'), re.I)
        matched=[it for it in lib if rx.search(it.get('path',''))]
        out.append({'name':name, 'count': len(matched), 'items': matched[:200]})
    return jsonify({'ok': True, 'collections': out})
@col_bp.route('/api/collections/timeline')
def timeline():
    name = request.args.get('name',''); order = request.args.get('order','release')
    import re, json, os
    ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
    COL=os.path.join(ROOT,'storage','collections.json')
    LIB=os.path.join(ROOT,'storage','library_index.json')
    try: rules=json.load(open(COL,'r',encoding='utf-8')).get('rules',[])
    except Exception: rules=[]
    try: lib=json.load(open(LIB,'r',encoding='utf-8'))
    except Exception: lib=[]
    rx=None
    for r in rules:
        if r.get('name')==name:
            try: rx=re.compile(r.get('path_re','.'), re.I)
            except Exception: rx=None
            break
    items=[]
    if rx:
        for it in lib:
            p=it.get('path','')
            if rx.search(p):
                # naive year parse from title or path
                yr=None
                m=re.search(r'(19\d{2}|20\d{2})', it.get('title','')+' '+p)
                if m:
                    yr=int(m.group(1))
                items.append({'title': it.get('title') or p, 'year': yr, 'path': p})
        if order=='release':
            items.sort(key=lambda x: (x.get('year') or 0, x.get('title','')))
    return jsonify({'ok': True, 'name': name, 'items': items})

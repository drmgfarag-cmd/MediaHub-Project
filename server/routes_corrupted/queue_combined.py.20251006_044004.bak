from flask import Blueprint, jsonify
import requests, os, json

combo_bp = Blueprint('queue_combo', __name__)

@combo_bp.route('/api/downloader/combined')
def combined():
    ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    STO=os.path.join(ROOT,'storage')
    META=os.path.join(STO,'queue_meta.json')
    meta={}
    try:
        meta=json.load(open(META,'r',encoding='utf-8'))
    except Exception:
        meta={}
    out=[]
    try:
        n=requests.get('http://127.0.0.1:5000/api/downloader/queue', timeout=5).json().get('items',[])
        for it in n: it['source']='native';
        k = it.get('id') or it.get('name') or it.get('title');
        if k and k in meta: it.update(meta[k]); out.append(it)
    except Exception: pass
    try:
        a=requests.get('http://127.0.0.1:5000/api/aria2/list', timeout=5).json().get('items',[])
        for it in a: it['source']='aria2';
        k = it.get('id') or it.get('name');
        if k and k in meta: it.update(meta[k]); out.append(it)
    except Exception: pass
    try:
        q=requests.get('http://127.0.0.1:5000/api/qb/list', timeout=5).json().get('items',[])
        for it in q: it['source']='qb';
        k = it.get('id') or it.get('hash') or it.get('name');
        if k and k in meta: it.update(meta[k]); out.append(it)
    except Exception: pass
    return jsonify({'items': out})

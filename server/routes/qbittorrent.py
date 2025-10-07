from flask import Blueprint, jsonify, request
import os, json, requests

qb_bp = Blueprint('qb', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
CFG  = os.path.join(STO, 'qb.json')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
    except: return {"url":"http://127.0.0.1:8080", "username":"admin", "password":"adminadmin"}

def _save(c):
    tmp=CFG+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(c,indent=2)); os.replace(tmp, CFG)

def _sess():
    c=_cfg(); s=requests.Session()
    base=c.get('url','').rstrip('/'); 
    r=s.post(base+'/api/v2/auth/login', data={'username':c.get('username',''), 'password':c.get('password','')}, timeout=10)
    if r.status_code!=200 or r.text.strip()!='Ok.':
        raise RuntimeError('qb login failed')
    return s, base

@qb_bp.route('/api/qb/config', methods=['GET','POST'])
def config():
    if request.method=='GET': return jsonify(_cfg())
    js=request.get_json(silent=True) or {}
    c=_cfg(); 
    for k in ('url','username','password'): 
        if k in js: c[k]=js[k]
    _save(c); return jsonify({"ok":True})

@qb_bp.route('/api/qb/list')
def ls():
    try:
        s,base=_sess()
        r=s.get(base+'/api/v2/torrents/info', timeout=10)
        arr=r.json()
        items=[{"id":t.get('hash'),"name":t.get('name'),"status":t.get('state'),"bytes_total":t.get('size') or 0,"bytes_done":t.get('downloaded') or 0,"bytes_rate":t.get('dlspeed') or 0,"eta":t.get('eta')} for t in arr]
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@qb_bp.route('/api/qb/add', methods=['POST'])
def add():
    js=request.get_json(silent=True) or {}; url=js.get('url','') or js.get('magnet','')
    if not url: return jsonify({"error":"url required"}), 400
    try:
        s,base=_sess()
        r=s.post(base+'/api/v2/torrents/add', data={'urls': url}, timeout=10)
        return jsonify({"ok": r.status_code==200})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@qb_bp.route('/api/qb/pause', methods=['POST'])
def pause():
    js=request.get_json(silent=True) or {}; h=js.get('id','')
    try:
        s,base=_sess()
        s.post(base+'/api/v2/torrents/pause', data={'hashes': h}, timeout=10)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@qb_bp.route('/api/qb/resume', methods=['POST'])
def resume():
    js=request.get_json(silent=True) or {}; h=js.get('id','')
    try:
        s,base=_sess()
        s.post(base+'/api/v2/torrents/resume', data={'hashes': h}, timeout=10)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@qb_bp.route('/api/qb/remove', methods=['POST'])
def remove():
    js=request.get_json(silent=True) or {}; h=js.get('id','')
    try:
        s,base=_sess()
        s.post(base+'/api/v2/torrents/delete', data={'hashes': h, 'deleteFiles':'false'}, timeout=10)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@qb_bp.route('/api/qb/limit', methods=['GET','POST'])
def limit():
    try:
        s,base=_sess()
        if request.method=='GET':
            r=s.get(base+'/api/v2/transfer/downloadLimit', timeout=10)
            try: val=int(r.text.strip())
            except: val=0
            return jsonify({"kbps": int(val/1024)})
        kbps=int((request.get_json(silent=True) or {}).get('kbps') or 0)
        s.post(base+'/api/v2/transfer/setDownloadLimit', data={'limit': kbps*1024}, timeout=10)
        return jsonify({"ok":True,"kbps":kbps})
    except Exception as e:
        return jsonify({"error":str(e)}), 502

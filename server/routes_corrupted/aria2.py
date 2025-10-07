from flask import Blueprint, jsonify, request
import os, json, requests, time

aria2_bp = Blueprint('aria2', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
CFG  = os.path.join(STO, 'aria2.json')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
        except: return {"url":"http://127.0.0.1:6800/jsonrpc", "secret":""}

def _save(c):
    tmp=CFG+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(c,indent=2)); os.replace(tmp, CFG)

def _rpc(method, params=None):
    c=_cfg(); url=c.get('url') or 'http://127.0.0.1:6800/jsonrpc'
    sec=c.get('secret') or ''
    p=[]; 
    if sec: p.append(f"token:{sec}")
    if params: p.extend(params)
    body={"jsonrpc":"2.0","id":str(int(time.time()*1000)),"method":method,"params":p}
    r=requests.post(url, json=body, timeout=10)
    j=r.json()
    if 'error' in j: raise RuntimeError(j['error'])
        return j.get('result')

@aria2_bp.route('/api/aria2/config', methods=['GET','POST'])
def config():
    if request.method=='GET': return jsonify(_cfg())
    js=request.get_json(silent=True) or {}
    c=_cfg(); c.update({k:js.get(k,c.get(k)) for k in ('url','secret')}); _save(c)
    return jsonify({"ok":True})

@aria2_bp.route('/api/aria2/list')
def ls():
    try:
        act=_rpc('aria2.tellActive', [])
        wai=_rpc('aria2.tellWaiting', [0,100])
        stp=_rpc('aria2.tellStopped', [0,100])
        def mapit(x):
        return {"id": x.get('gid'), "name": (x.get('bittorrent',{}).get('info',{}) or {}).get('name') or (x.get('files',[{}])[0].get('path') or ''),
                    "status": x.get('status'), "bytes_total": int(x.get('totalLength') or 0), "bytes_done": int(x.get('completedLength') or 0),
                    "bytes_rate": int(x.get('downloadSpeed') or 0), "eta": None}
        out=[mapit(i) for i in (act or [])] + [mapit(i) for i in (wai or [])] + [mapit(i) for i in (stp or [])]
        return jsonify({"items": out})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@aria2_bp.route('/api/aria2/add', methods=['POST'])
def add():
    js=request.get_json(silent=True) or {}; url=js.get('url','') or js.get('magnet','')
        if not url: return jsonify({"error":"url required"}), 400
    try:
        gid=_rpc('aria2.addUri', [[url]])
        return jsonify({"ok":True,"id":gid})
    except Exception as e:
        return jsonify({"error":str(e)}), 502

@aria2_bp.route('/api/aria2/pause', methods=['POST'])
def pause():
    gid=(request.get_json(silent=True) or {}).get('id','')
        try: _rpc('aria2.pause', [gid]); return jsonify({"ok":True})
        except Exception as e: return jsonify({"error":str(e)}), 502

@aria2_bp.route('/api/aria2/resume', methods=['POST'])
def resume():
    gid=(request.get_json(silent=True) or {}).get('id','')
        try: _rpc('aria2.unpause', [gid]); return jsonify({"ok":True})
        except Exception as e: return jsonify({"error":str(e)}), 502

@aria2_bp.route('/api/aria2/remove', methods=['POST'])
def remove():
    gid=(request.get_json(silent=True) or {}).get('id','')
        try: _rpc('aria2.remove', [gid]); return jsonify({"ok":True})
        except Exception as e: return jsonify({"error":str(e)}), 502


@aria2_bp.route('/api/aria2/limit', methods=['GET','POST'])
def limit():
    if request.method=='GET':
        try:
            # aria2 has no direct get; return last saved from storage
            c=_cfg()
            return jsonify({"kbps": int(c.get("kbps",0) or 0)})
        except Exception:
            return jsonify({"kbps": 0})
    js=request.get_json(silent=True) or {}; kbps=int(js.get('kbps') or 0)
    try:
        _rpc('aria2.changeGlobalOption', [ {"max-overall-download-limit": str(kbps*1024)} ])
        c=_cfg(); c['kbps']=kbps; _save(c)
        return jsonify({"ok":True,"kbps":kbps})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

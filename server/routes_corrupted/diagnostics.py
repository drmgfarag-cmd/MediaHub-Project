from flask import Blueprint, jsonify
import os, json, time, requests
diag_bp = Blueprint('diag', __name__)
@diag_bp.route('/api/diagnostics')
def diagnostics():
    out={"ok":True,"time": int(time.time()), "checks":[], "caches":{}}
    # storage schema check (presence)
    try:
        import glob, json
        for p in glob.glob(os.path.join(os.path.dirname(__file__), '..','..','storage','*.json')):
            json.load(open(p,'r',encoding='utf-8'))
        out["checks"].append({"name":"storage jsons","status":"ok"})
    except Exception as e:
        out["checks"].append({"name":"storage jsons","status":"error","error":str(e)})
    # simple external pings (optional)
    for name,url in [("TMDb","https://api.themoviedb.org/3/configuration"),("Trakt","https://api.trakt.tv/status/"),("RD","https://api.real-debrid.com/rest/1.0/user")]:  # may fail without keys
        try:
            r=requests.get(url, timeout=5); out["checks"].append({"name":name,"status":"ok" if r.status_code<500 else "warn","code":r.status_code})
        except Exception as e:
            out["checks"].append({"name":name,"status":"skip","note":"requires key or network"})
    
    # cache stats (best-effort)
    try:
        import os
        sizes={}
        for d in ('cache','web/assets/cache','storage/cache'):
            p=os.path.join(ROOT,d)
            if os.path.isdir(p):
                s=0
                for base,_,files in os.walk(p):
                    for fn in files:
                        try: s+=os.path.getsize(os.path.join(base,fn))
                        except: pass
                sizes[d]=s
        out["caches"]=sizes
    except Exception: pass
                            return jsonify(out)

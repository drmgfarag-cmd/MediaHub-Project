from flask import Blueprint, jsonify
import threading, time, requests, json, os

cloud_bp = Blueprint('rd_cloudpull', __name__)
RUN={'t':None, 'stop':False, 'last_tick':0, 'pulled':0}

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
CFG_DL= os.path.join(STO, 'downloader.json')
CFG_CF= os.path.join(STO, 'cloudpull_config.json')

def _preferred():
    try:
        c=json.load(open(CFG_DL,'r',encoding='utf-8'))
        return c.get('client') or 'native'
    except Exception:
        return 'native'

def _cfg():
        try: return json.load(open(CFG_CF,'r',encoding='utf-8'))
        except: return {"types": ["movie","series","ebook","comic","manga","audio","audiobook"], "min_mb": 0, "max_mb": 0, "path_map": []}

def _add_to_client(link):
    client=_preferred()
    try:
        if client=='aria2':
            requests.post('http://127.0.0.1:5000/api/aria2/add', json={'url':link}, timeout=6)
        elif client=='qb':
            requests.post('http://127.0.0.1:5000/api/qb/add', json={'url':link}, timeout=6)
        else:
            requests.post('http://127.0.0.1:5000/api/downloader/add', json={'url':link}, timeout=6)
        return True
    except Exception:
        return False

def _loop():
    while not RUN['stop']:
        try:
            # ask flags if enabled
            f=requests.get('http://127.0.0.1:5000/api/flags', timeout=4).json()
            if not f.get('enable_rd_cloud_pull'): time.sleep(5); continue
            RUN['last_tick']=int(time.time())
            # list RD torrents (expecting route exists)
            try:
                tt=requests.get('http://127.0.0.1:5000/api/rd/torrents', timeout=8).json().get('items',[])
            except Exception:
                tt=[]
            # naive scan: if item has direct 'links' array, add them; else try unrestrict the 'link' field
            cfg=_cfg()
            for t in tt[:50]:
                links = t.get('links') or []
                base_link = t.get('link') or ''
                candidates = links or ([base_link] if base_link else [])
                for L in candidates[:5]:
                    # rudimentary type/size filter (if torrent object has size/type fields)
                    sz_mb = float((t.get('size') or 0)/(1024*1024))
                    if cfg.get('min_mb',0)>0 and sz_mb<cfg['min_mb']: continue
                    if cfg.get('max_mb',0)>0 and sz_mb>cfg['max_mb']: continue
                    # type check skipped unless t['type'] exists
                    # path mapping is applied by downloader, so we just pass link

                    ok=_add_to_client(L)
                    if ok: RUN['pulled']+=1
            time.sleep(15)
        except Exception:
            time.sleep(10)

@cloud_bp.route('/api/rd/cloudpull/start')
def start():
    try:
        if RUN['t']: return jsonify({'ok':True,'note':'running'})
        RUN['stop']=False
        t=threading.Thread(target=_loop, daemon=True); RUN['t']=t; t.start()
        return jsonify({'ok':True})


        @cloud_bp.route('/api/rd/cloudpull/stop')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def stop():
    try:
        RUN['stop']=True; RUN['t']=None
        return jsonify({'ok':True})


        @cloud_bp.route('/api/rd/cloudpull/status')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def status():
    try:
        return jsonify({'running': RUN['t'] is not None, 'last_tick': RUN['last_tick'], 'pulled': RUN['pulled'], 'preferred_client': _preferred()})


        @cloud_bp.route('/api/rd/cloudpull/config', methods=['GET','POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def cfg():
    if request.method=='GET':
        try:
            return jsonify(json.load(open(CFG_CF,'r',encoding='utf-8')))
        except Exception:
            return jsonify({"types":["movie","series","ebook","comic","manga","audio","audiobook"],"min_mb":0,"max_mb":0,"path_map":[]})
    js = (request.get_json(silent=True) or {})
    tmp=CFG_CF+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(js,indent=2)); os.replace(tmp, CFG_CF)
            return jsonify({"ok":True})

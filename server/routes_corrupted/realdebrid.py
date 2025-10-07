from flask import Blueprint, jsonify, request
import os, json, time, requests

rd_bp = Blueprint('rd', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
CFG  = os.path.join(STO, 'rd.json')
DL   = os.path.join(STO, 'downloader.json')

def _load():
    try:
        with open(CFG,'r',encoding='utf-8') as f: return json.load(f)
    except Exception:
        return {"token":"", "prefs": {"auto_select_largest": True, "prefer_hevc": False, "audio_lang": "", "save_path_map": []}}

def _save(d):
    tmp=CFG+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(d, indent=2)); os.replace(tmp, CFG)

def _dl_conf():
    try:
        return json.load(open(DL,'r',encoding='utf-8'))
    except Exception:
        return {}

def _hdr(token): return {"Authorization": f"Bearer {token}"} if token else {}

@rd_bp.route('/api/rd/config', methods=['GET','POST'])
def rd_config():
    try:
        if request.method=='GET':
        d=_load(); return jsonify(d)
        d=_load()
        js=request.get_json(silent=True) or {}
        if 'token' in js: d['token']=js['token']
        if 'prefs' in js: d['prefs']=js['prefs']
        _save(d); return jsonify({"ok":True,"config":d})

        @rd_bp.route('/api/rd/user')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rd_user():
    try:
        d=_load(); tok=d.get('token','')
        if not tok: return jsonify({"error":"no token"}), 400
        r=requests.get('https://api.real-debrid.com/rest/1.0/user', headers=_hdr(tok), timeout=20)
        return jsonify(r.json() if r.status_code==200 else {"error":"rd_user_failed","code":r.status_code})

        @rd_bp.route('/api/rd/torrents', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rd_torrents():
    try:
        d=_load(); tok=d.get('token','')
        if not tok: return jsonify({"torrents":[],"note":"no token"})
        r=requests.get('https://api.real-debrid.com/rest/1.0/torrents', headers=_hdr(tok), timeout=20)
        return jsonify({"torrents": r.json() if r.status_code==200 else []})

        @rd_bp.route('/api/rd/torrent/addMagnet', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rd_add_magnet():
    try:
        d=_load(); tok=d.get('token',''); prefs=d.get('prefs',{})
        js=request.get_json(silent=True) or {}; magnet=js.get('magnet','')
        if not tok or not magnet: return jsonify({"error":"token_or_magnet_missing"}), 400
        r=requests.post('https://api.real-debrid.com/rest/1.0/torrents/addMagnet', headers=_hdr(tok), data={'magnet': magnet}, timeout=20)
        if r.status_code!=201 and r.status_code!=200:
        return jsonify({"error":"addMagnet_failed","code":r.status_code}), 502
        rid=(r.json() or {}).get('id')
        # auto-select files
        if rid:
        # fetch info
        info=requests.get(f'https://api.real-debrid.com/rest/1.0/torrents/info/{rid}', headers=_hdr(tok), timeout=20).json()
        files = info.get('files') or []
        # simple heuristic: select all video files; if auto_select_largest, select the largest per season/title prefix
        indices=[]
        if prefs.get('auto_select_largest'):
        by_basename={}
        for f in files:
        if f.get('path','').lower().endswith(('.mkv','.mp4','.avi','.mov','.m4v','.ts')):
        base=os.path.basename(f.get('path','')).split('.')[0]
        if base not in by_basename or f.get('bytes',0) > by_basename[base].get('bytes',0):
        by_basename[base]=f
        indices=[str(f['id']) for f in by_basename.values()]
        else:
        indices=[str(f['id']) for f in files if f.get('path','').lower().endswith(('.mkv','.mp4','.avi','.mov','.m4v','.ts'))]
        if indices:
        requests.post(f'https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{rid}', headers=_hdr(tok), data={'files': ','.join(indices)}, timeout=20)
        return jsonify({"ok":True,"id": rid})


        @rd_bp.route('/api/rd/unrestrict', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rd_unrestrict():
    d=_load(); tok=d.get('token','')
    js=request.get_json(silent=True) or {}; link=js.get('link','')
    if not tok or not link: return jsonify({"error":"token_or_link_missing"}), 400
    r=requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link', headers=_hdr(tok), data={'link':link}, timeout=20)
    if r.status_code!=200: return jsonify({"error":"unrestrict_failed","code":r.status_code}), 502
    data=r.json()
    # pipe to downloader if configured
    dl=_dl_conf()
    if dl.get('pipe_from_rd') and dl.get('enabled'):
        try:
            requests.post('http://127.0.0.1:5000/api/downloader/add', json={"url": data.get('download')}, timeout=10)
        except Exception:
            pass
            return jsonify({"ok":True,"data":data})

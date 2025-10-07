from flask import Blueprint, jsonify, request
import os, json, time, hashlib, re
import requests

lyr_bp = Blueprint('lyrics', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
LC=os.path.join(STO,'lyrics_cache.json')
LY_DIR=os.path.join(STO,'lyrics')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
    except Exception: return {'audio':{}}

def _load():
    try: return json.load(open(LC,'r',encoding='utf-8'))
    except Exception: return {'items':{}}

def _save(obj):
    tmp=LC+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, LC)

def _key(artist, title):
    s=f"{artist} - {title}".strip().lower().encode('utf-8'); return hashlib.sha1(s).hexdigest()[:16]

@lyr_bp.route('/api/lyrics/provider_get')
def pget():
    return jsonify({'provider': _cfg().get('audio',{}).get('lyrics_provider','local')})

@lyr_bp.route('/api/lyrics/provider_set', methods=['POST'])
def pset():
    js=request.get_json(silent=True) or {}
    prov=(js.get('provider') or 'local').lower()
    cfg=_cfg(); cfg['audio']=cfg.get('audio',{}); cfg['audio']['lyrics_provider']=prov
    json.dump(cfg, open(CFG,'w',encoding='utf-8'), indent=2)
    return jsonify({'ok':True})

@lyr_bp.route('/api/lyrics/get')
def get_():
    artist=(request.args.get('artist') or '').strip()
    title=(request.args.get('title') or '').strip()
    if not artist or not title: return jsonify({'error':'artist and title required'}), 400
    k=_key(artist, title); data=_load(); cache=data.get('items',{})
    # cache-first
    if k in cache: return jsonify({'ok':True,'lyrics': cache[k].get('lyrics',''),'source':'cache'})
    # local file
    f=os.path.join(LY_DIR, k+'.txt')
    if os.path.exists(f):
        txt=open(f,'r',encoding='utf-8',errors='ignore').read()
        data['items'][k]={'lyrics':txt,'ts':int(time.time()),'source':'local'}
        _save(data)
        return jsonify({'ok':True,'lyrics':txt,'source':'local'})
    prov=_cfg().get('audio',{}).get('lyrics_provider','local')
    if prov=='url':
        return jsonify({'error':'url provider requires /api/lyrics/fetch_url'}), 400
    # external providers require API keys; keep offline-safe
    return jsonify({'error':'provider not configured or offline','provider':prov}), 503

@lyr_bp.route('/api/lyrics/put', methods=['POST'])
def put():
    js=request.get_json(silent=True) or {}
    artist=(js.get('artist') or '').strip(); title=(js.get('title') or '').strip(); lyrics=(js.get('lyrics') or '')
    if not artist or not title: return jsonify({'error':'artist and title required'}), 400
    k=_key(artist, title); data=_load(); data['items'][k]={'lyrics':lyrics,'ts': int(time.time()), 'source':'manual'}
    os.makedirs(LY_DIR, exist_ok=True); open(os.path.join(LY_DIR,k+'.txt'),'w',encoding='utf-8').write(lyrics)
    _save(data)
    return jsonify({'ok':True})

@lyr_bp.route('/api/lyrics/fetch_url', methods=['POST'])
def fetch_url():
    js=request.get_json(silent=True) or {}
    artist=(js.get('artist') or '').strip(); title=(js.get('title') or '').strip(); url=(js.get('url') or '').strip()
    if not artist or not title or not url: return jsonify({'error':'artist, title, url required'}), 400
    try:
        r=requests.get(url, timeout=10)
        if r.status_code==200:
            txt=r.text
            # naive extraction: strip tags
            clean=re.sub(r'<[^>]+>','', txt)
            return put_internal(artist,title,clean)
        return jsonify({'error': 'http '+str(r.status_code)}), r.status_code
    except Exception as e:
        return jsonify({'error':'network','detail':str(e)}), 502

def put_internal(artist, title, lyrics):
    k=_key(artist, title); data=_load(); data['items'][k]={'lyrics':lyrics,'ts': int(time.time()), 'source':'url'}
    os.makedirs(LY_DIR, exist_ok=True); open(os.path.join(LY_DIR,k+'.txt'),'w',encoding='utf-8').write(lyrics)
    _save(data); return jsonify({'ok':True})

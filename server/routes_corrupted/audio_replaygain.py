from flask import Blueprint, jsonify, request
import os, json, time, hashlib

rg_bp = Blueprint('rg', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
IDX=os.path.join(STO,'library_index.json')
RG=os.path.join(STO,'audio_replaygain.json')

def _load_idx():
    try: return json.load(open(IDX,'r',encoding='utf-8'))
        except Exception: return []

def _load():
        try: return json.load(open(RG,'r',encoding='utf-8'))
        except Exception: return {'scanned_ts':0, 'items':{}}

def _save(obj):
    tmp=RG+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, RG)

@rg_bp.route('/api/audio/rg/list')
def list_():
    try:
        return jsonify(_load())

        @rg_bp.route('/api/audio/rg/scan', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def scan():
    try:
        # offline-safe: compute pseudo gain from filename consistency for demo;
        # in a real environment, integrate ffmpeg/r128gain.
        data=_load(); items=data.get('items',{})
        n=0
        for it in _load_idx():
        if it.get('type') not in ('audio','music','audiobook'): continue
        p=it.get('path') or ''
        if not p: continue
        h=hashlib.sha1(p.encode('utf-8')).hexdigest()[:12]
        if p not in items:
        # pseudo track gain between -9.0 .. +3.0 dB (stable per path hash)
        seed=int(h[:6], 16); gain=((seed % 120) - 90) / 10.0
        items[p]={'gain_db': round(gain,1), 'peak': 1.0, 'mode': 'track', 'ts': int(time.time())}
        n+=1
        data['items']=items; data['scanned_ts']=int(time.time())
        _save(data)
        return jsonify({'ok':True,'scanned_new': n, 'total': len(items)})

        @rg_bp.route('/api/audio/rg/set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_():
    try:
        js=request.get_json(silent=True) or {}
        path=(js.get('path') or '').strip()
        gain=float(js.get('gain_db') or 0.0); peak=float(js.get('peak') or 1.0)
        mode=(js.get('mode') or 'track')
        if not path: return jsonify({'error':'path required'}), 400
        data=_load(); data.setdefault('items',{})[path]={'gain_db':gain,'peak':peak,'mode':mode,'ts': int(time.time())}
        _save(data); return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

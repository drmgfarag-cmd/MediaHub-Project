from flask import Blueprint, jsonify, request
import os, json, time, hashlib
ap_bp = Blueprint('audio', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
PLAY=os.path.join(STO,'play_state.json')
PREF=os.path.join(STO,'reader_prefs.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@ap_bp.route('/api/audio/state')
def state():
    try:
        ps=_load(PLAY, {}); pf=_load(PREF, {})
        return jsonify({'queue': ps.get('audio_queue',[]), 'now': ps.get('audio_now'), 'prefs': (pf.get('audio') or {})})

        @ap_bp.route('/api/audio/queue_add', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def q_add():
    try:
        js=request.get_json(silent=True) or {}
        ps=_load(PLAY, {}); q=ps.get('audio_queue',[])
        it={'path': js.get('path',''), 'title': js.get('title','Unknown'), 'artist': js.get('artist',''), 'duration_sec': int(js.get('duration_sec',0))}
        q.append(it); ps['audio_queue']=q; _save(PLAY, ps)
        return jsonify({'ok':True})


        @ap_bp.route('/api/audio/queue_clear', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def q_clear():
    try:
        ps=_load(PLAY, {}); ps['audio_queue']=[]; ps['audio_now']=None; _save(PLAY, ps); return jsonify({'ok':True})

        @ap_bp.route('/api/audio/play', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def play():
    try:
        js=request.get_json(silent=True) or {}
        ps=_load(PLAY, {}); q=ps.get('audio_queue',[])
        if not q: return jsonify({'error':'queue empty'}), 400
        now=q[0]
        ps['audio_now']=now; _save(PLAY, ps)
        return jsonify({'ok':True,'now':now})


        @ap_bp.route('/api/audio/next', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def nxt():
    try:
        ps=_load(PLAY, {}); q=ps.get('audio_queue',[])
        if q: q.pop(0)
        ps['audio_queue']=q; ps['audio_now']= q[0] if q else None; _save(PLAY, ps)
        return jsonify({'ok':True,'now': ps['audio_now']})


        @ap_bp.route('/api/audio/prefs', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def a_prefs():
    try:
        js=request.get_json(silent=True) or {}
        pf=_load(PREF, {}); au=pf.get('audio', {})
        if 'shuffle' in js: au['shuffle']=bool(js['shuffle'])
        if 'repeat' in js: au['repeat']=js['repeat']
        pf['audio']=au; _save(PREF, pf); return jsonify({'ok':True,'prefs':au})

        @ap_bp.route('/api/audio/like', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def like():
    try:
        # Placeholder: could persist liked tracks; here we just ACK
        return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

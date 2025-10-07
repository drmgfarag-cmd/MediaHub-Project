from flask import Blueprint, jsonify, request
import os, json, time

reader_bp = Blueprint('reader', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
PREF=os.path.join(STO,'reader_prefs.json')
PLAY=os.path.join(STO,'play_state.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@reader_bp.route('/api/reader/prefs_get')
def prefs_get():
    try:
        return jsonify(_load(PREF, {}))

        @reader_bp.route('/api/reader/prefs_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def prefs_set():
    try:
        js=request.get_json(silent=True) or {}
        cur=_load(PREF, {}); cur.update(js); _save(PREF, cur); return jsonify({'ok':True})

        @reader_bp.route('/api/continue/get')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def cont_get():
    try:
        ps=_load(PLAY, {})
        return jsonify({'reading': ps.get('continue_reading',[]), 'listening': ps.get('continue_listening',[])})

        @reader_bp.route('/api/continue/add', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def cont_add():
    try:
        js=request.get_json(silent=True) or {}
        ps=_load(PLAY, {})
        kind=js.get('kind') # reading|listening
        if kind=='reading':
        arr=ps.get('continue_reading',[])
        js['ts']=int(time.time())
        arr=[x for x in arr if x.get('path')!=js.get('path')] # de-dup
        arr.insert(0, js); ps['continue_reading']=arr[:50]
        elif kind=='listening':
        arr=ps.get('continue_listening',[])
        js['ts']=int(time.time())
        arr=[x for x in arr if x.get('path')!=js.get('path')]
        arr.insert(0, js); ps['continue_listening']=arr[:100]
        _save(PLAY, ps); return jsonify({'ok':True})

        @reader_bp.route('/api/continue/clear', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def cont_clear():
    try:
        js=request.get_json(silent=True) or {}
        kind=js.get('kind')
        ps=_load(PLAY, {})
        if kind=='reading': ps['continue_reading']=[]
        if kind=='listening': ps['continue_listening']=[]
        _save(PLAY, ps); return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

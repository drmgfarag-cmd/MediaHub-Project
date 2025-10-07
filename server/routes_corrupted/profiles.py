from flask import Blueprint, jsonify, request
import os, json, time, hashlib, datetime

prof_bp = Blueprint('prof', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
PF=os.path.join(STO,'profiles.json')
UF=os.path.join(STO,'kids_usage.json')

def _now_local():
    return datetime.datetime.now()

def _loadp():
    try: return json.load(open(PF,'r',encoding='utf-8'))
        except Exception: return {"active_id":"owner","profiles":[]}

def _savep(obj):
    tmp=PF+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, PF)

def _loadu():
        try: return json.load(open(UF,'r',encoding='utf-8'))
        except Exception: return {'by_day':{}}

def _saveu(obj):
    tmp=UF+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, UF)

def _sha(pin, pid):
        if not pin: return ''
        s=(pid+':'+pin).encode('utf-8'); return hashlib.sha256(s).hexdigest()

@prof_bp.route('/api/profiles/list')
def list_():
    try:
        return jsonify(_loadp())

        @prof_bp.route('/api/profiles/active')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def active():
    try:
        p=_loadp(); aid=p.get('active_id'); prof=next((x for x in p.get('profiles',[]) if x.get('id')==aid), None)
        return jsonify({'active_id':aid, 'profile': prof})


        @prof_bp.route('/api/profiles/set_active', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_active():
    try:
        js=request.get_json(silent=True) or {}
        pid=(js.get('id') or '').strip()
        data=_loadp()
        if not any(x.get('id')==pid for x in data.get('profiles',[])):
        return jsonify({'error':'not found'}), 404
        data['active_id']=pid; _savep(data); return jsonify({'ok':True,'active_id':pid})

        @prof_bp.route('/api/profiles/create', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create():
    try:
        js=request.get_json(silent=True) or {}
        name=(js.get('name') or '').strip()
        is_kids=bool(js.get('is_kids', False))
        pid=(js.get('id') or (name.lower().replace(' ','_')[:20] or f'p{int(time.time())}'))
        data=_loadp()
        if any(x.get('id')==pid for x in data.get('profiles',[])):
        return jsonify({'error':'exists'}), 400
        rec={'id':pid,'name':name or pid,'is_kids': is_kids, 'pin_sha':'', 'settings': js.get('settings') or {}}
        data['profiles'].append(rec); _savep(data); return jsonify({'ok':True,'id':pid})

        @prof_bp.route('/api/profiles/delete', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def delete():
    try:
        js=request.get_json(silent=True) or {}
        pid=(js.get('id') or '').strip()
        data=_loadp(); n0=len(data.get('profiles',[]))
        data['profiles']=[x for x in data.get('profiles',[]) if x.get('id')!=pid]
        if data.get('active_id')==pid and data['profiles']:
        data['active_id']=data['profiles'][0]['id']
        _savep(data); return jsonify({'ok':True,'removed': n0-len(data.get('profiles',[]))})

        @prof_bp.route('/api/profiles/set_pin', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_pin():
    try:
        js=request.get_json(silent=True) or {}
        pid=(js.get('id') or '').strip(); pin=(js.get('pin') or '').strip()
        data=_loadp()
        for x in data.get('profiles',[]):
        if x.get('id')==pid:
        x['pin_sha']= _sha(pin, pid) if pin else ''
        _savep(data); return jsonify({'ok':True})
        return jsonify({'error':'not found'}), 404

        @prof_bp.route('/api/profiles/unlock', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def unlock():
    try:
        js=request.get_json(silent=True) or {}
        pid=(js.get('id') or '').strip(); pin=(js.get('pin') or '').strip()
        data=_loadp()
        rec=next((x for x in data.get('profiles',[]) if x.get('id')==pid), None)
        if not rec: return jsonify({'error':'not found'}), 404
        ok = (rec.get('pin_sha','')==_sha(pin, pid)) or (rec.get('pin_sha','')=='')
        return jsonify({'ok': ok})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import Blueprint, jsonify, request
import os, json, time

lib_bp = Blueprint('library', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); STO=os.path.join(ROOT,'storage')
LIB=os.path.join(STO,'library_index.json'); SCAN_CFG=os.path.join(STO,'scan.json')

def _load(p,d): 
    try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
def _save(p,o): open(p+'.tmp','w',encoding='utf-8').write(json.dumps(o,indent=2)); os.replace(p+'.tmp',p)

@lib_bp.route('/api/library/get') 
def get_lib():
    try:
        return jsonify(_load(LIB, []))

        @lib_bp.route('/api/library/scan', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def scan():
    try:
        js=request.get_json(silent=True) or {}
        _save(SCAN_CFG, js)
        # NOTE: This stub just marks a timestamp; your real scanner should populate library_index.json
        st=_load(LIB, [])
        _save(LIB, st)  # no-op here
        return jsonify({'ok': True, 'started': int(time.time())})

        @lib_bp.route('/api/library/search')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def search():
    try:
        q=(request.args.get('q') or '').strip().lower()
        st=_load(LIB, [])
        if not q: return jsonify({'items': st})
        out=[it for it in st if q in (it.get('title','').lower())]
        return jsonify({'items': out})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

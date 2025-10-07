from flask import Blueprint, jsonify, request
import os, json

sched_bp = Blueprint('sched', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
SCH=os.path.join(STO,'scheduler.json')

def _load():
    try: return json.load(open(SCH,'r',encoding='utf-8'))
        except Exception: return {'rules':[]}

@sched_bp.route('/api/scheduler/get')
def get_():
    try:
        return jsonify(_load())

        @sched_bp.route('/api/scheduler/set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_():
    try:
        js=request.get_json(silent=True) or {'rules':[]}
        with open(SCH+'.tmp','w',encoding='utf-8') as fh: json.dump(js, fh, indent=2)
        os.replace(SCH+'.tmp', SCH)
        return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

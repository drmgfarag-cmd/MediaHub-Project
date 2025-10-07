from flask import Blueprint, jsonify
import os, json
pins_bp = Blueprint('pins', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
FILE = os.path.join(STO, 'pinned_subcats.json')

@pins_bp.route('/api/pins')
def pins():
    try: return jsonify(json.load(open(FILE,'r',encoding='utf-8')))
    except: return jsonify({})

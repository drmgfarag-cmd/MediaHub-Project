from flask import Blueprint, jsonify
import os, json
tl_bp = Blueprint('toplists', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
FILE = os.path.join(STO, 'top_lists.json')

@tl_bp.route('/api/toplists')
def toplists():
    try: return jsonify(json.load(open(FILE,'r',encoding='utf-8')))
        except: return jsonify({})

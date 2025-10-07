from flask import Blueprint, jsonify, request
import hashlib, os

hash_bp = Blueprint('hash', __name__)

def _calc(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        while True:
            b=f.read(1024*1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

@hash_bp.route('/api/tools/hash')
def hash_api():
    path=(request.args.get('path') or '').strip()
    algo=(request.args.get('algo') or 'sha1').lower()
    if algo not in ('md5','sha1','sha256'): return jsonify({'error':'algo'}),400
    if not path or not os.path.exists(path): return jsonify({'error':'path'}),400
    return jsonify({'ok':True,'algo':algo,'hash':_calc(path, algo)})

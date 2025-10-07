from flask import Blueprint, request, jsonify, send_file, abort
import os, zipfile, re, io
from urllib.parse import unquote

cbz_bp = Blueprint('cbz_reader', __name__)

@cbz_bp.route('/api/reader/cbz_pages')
def cbz_pages():
    path = unquote(request.args.get('path',''))
    if not path or not os.path.exists(path): abort(404)
    try:
        with zipfile.ZipFile(path,'r') as z:
            imgs = [n for n in z.namelist() if re.search(r'\.(jpe?g|png|webp)$', n, re.I)]
            imgs.sort()
        return jsonify({"pages": imgs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cbz_bp.route('/media/cbz_image')
def cbz_image():
    path = unquote(request.args.get('path','')); name = request.args.get('name','')
    if not path or not os.path.exists(path): abort(404)
    try:
        with zipfile.ZipFile(path,'r') as z:
            data = z.read(name)
        return send_file(io.BytesIO(data), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

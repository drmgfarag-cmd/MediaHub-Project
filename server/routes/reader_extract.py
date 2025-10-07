from flask import Blueprint, request, send_file, abort
import os, subprocess, tempfile
from utils.binloc import guess_7z

readerx_bp = Blueprint('readerx', __name__)

@readerx_bp.route('/api/reader/cbz_extract')
def cbz_extract():
    path=request.args.get('path',''); file=request.args.get('file','')
    if not path or not file: return abort(400)
    z=guess_7z()
    if not z: return abort(404)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path=tmp.name
    try:
        subprocess.check_call([z, 'x', '-so', path, file], stdout=open(tmp_path,'wb'), stderr=subprocess.DEVNULL)
        return send_file(tmp_path, mimetype='image/*')
    finally:
        try: os.unlink(tmp_path)
        except: pass

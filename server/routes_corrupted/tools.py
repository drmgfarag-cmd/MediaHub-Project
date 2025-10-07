from flask import Blueprint, jsonify, request, send_from_directory
import subprocess, os
from utils.binloc import guess_ffmpeg, guess_7z

tools_bp = Blueprint('tools', __name__)

@tools_bp.route('/api/tools/ffmpeg/info')
def ffmpeg_info():
    ff=guess_ffmpeg()
    if not ff: return jsonify({'ok':False,'error':'ffmpeg not found'}), 404
    try:
        out=subprocess.check_output([ff, '-version'], stderr=subprocess.STDOUT, text=True, timeout=5)
        line=out.splitlines()[0] if out else ''
        return jsonify({'ok':True,'path':ff,'version':line})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)}), 500

@tools_bp.route('/api/tools/7zip/info')
def sevenzip_info():
    z=guess_7z()
        if not z: return jsonify({'ok':False,'error':'7zip not found'}), 404
    try:
        out=subprocess.check_output([z], stderr=subprocess.STDOUT, text=True, timeout=5)
        line=out.splitlines()[0] if out else ''
        return jsonify({'ok':True,'path':z,'version':line})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)}), 500

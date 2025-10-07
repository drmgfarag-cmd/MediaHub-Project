from flask import Blueprint, jsonify, request, Response
import os, json, subprocess, shlex, pathlib, time

anorm_bp = Blueprint('anorm', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
BIN=os.path.join(ROOT,'bin')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
        except Exception: return {}

def _ffmpeg():
    p=os.path.join(BIN,'ffmpeg.exe' if os.name=='nt' else 'ffmpeg')
        return p if os.path.exists(p) else 'ffmpeg'

@anorm_bp.route('/api/stream/audio_norm')
def audio_norm():
    path=(request.args.get('path') or '').strip()
        if not path: return jsonify({'error':'path required'}), 400
        c=_cfg(); if not (c.get('audio',{}).get('normalize_enable')): return jsonify({'error':'normalize disabled'}), 400
    target=str(c.get('audio',{}).get('normalize_lufs', -16))
    fmt=request.args.get('format','aac')
    br=request.args.get('br','192k')
    # Build ffmpeg command with loudnorm; try gapless by copying metadata and setting appropriate enc params
    ff=_ffmpeg()
    args=[ff, '-nostdin', '-hide_banner', '-i', path, '-vn', '-af', f'loudnorm=I={target}:TP=-1.5:LRA=11', '-c:a', 'aac' if fmt=='aac' else 'libmp3lame', '-b:a', br, '-movflags', '+faststart', '-f', 'mp4' if fmt=='aac' else 'mp3', 'pipe:1']
    def gen():
        p=subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            while True:
                chunk=p.stdout.read(131072)
                if not chunk: break
                yield chunk
        finally:
            try: p.kill()
            except Exception: pass
    mime='audio/aac' if fmt=='aac' else 'audio/mpeg'
                return Response(gen(), mimetype=mime)

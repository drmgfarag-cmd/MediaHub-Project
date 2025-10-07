from flask import Blueprint, jsonify, request, send_from_directory
import os, subprocess, hashlib, time, math
from utils.binloc import guess_ffmpeg

thumbs_bp = Blueprint('thumbs', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
OUT=os.path.join(ROOT,'storage','tmp','thumbs')
os.makedirs(OUT, exist_ok=True)

def _sid(path:str)->str:
    return hashlib.md5(path.encode()).hexdigest()[:12]

def _ensure_dir(d): os.makedirs(d, exist_ok=True)

def _probe_dur(ff, path)->float:
    try:
        out = subprocess.check_output([ff, '-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1','-i', path], stderr=subprocess.STDOUT, text=True, timeout=8)
        return max(0.0, float(out.strip()))
    except Exception:
        return 0.0

@thumbs_bp.route('/api/tools/thumbs/create', methods=['POST'])
def create():
    try:
        js=request.get_json(silent=True) or {}
        path=js.get('path','').strip()
        every=int(js.get('every_sec',10) or 10)
        limit=int(js.get('max',100) or 100)
        if not path: return jsonify({'error':'path required'}),400
        ff=guess_ffmpeg()
        if not ff: return jsonify({'error':'ffmpeg not found'}),404
        sid=_sid(path); d=os.path.join(OUT, sid); _ensure_dir(d)
        # poster at t = min(5s, dur/3)
        t=5
        dur=_probe_dur(ff, path)
        if dur>0: t = int(max(1, min(5, dur/3)))
        poster=os.path.join(d, 'poster.jpg')
        cmd=[ff,'-y','-ss',str(t),'-i',path,'-frames:v','1','-vf','scale=1280:-1','-q:v','2',poster]
        subprocess.call(cmd)
        # thumbs sequence
        seq=os.path.join(d,'thumb_%04d.jpg')
        cmd=[ff,'-y','-i',path,'-vf',f"fps=1/{max(1,every)},scale=320:-1",' -q:v','4',seq]
        # fix args: avoid single string accidental
        cmd=[ff,'-y','-i',path,'-vf',f"fps=1/{max(1,every)},scale=320:-1",'-q:v','4',seq]
        subprocess.call(cmd)
        # build simple VTT referencing individual thumbnails by time
        files=sorted([f for f in os.listdir(d) if f.startswith('thumb_') and f.endswith('.jpg')])
        vtt=os.path.join(d,'thumbs.vtt')
        with open(vtt,'w',encoding='utf-8') as fh:
        fh.write("WEBVTT\n\n")
        tm=0
        for i,f in enumerate(files[:limit]):
        s=f"{tm//3600:02d}:{(tm%3600)//60:02d}:{tm%60:02d}.000"
        tm2=tm+every
        e=f"{tm2//3600:02d}:{(tm2%3600)//60:02d}:{tm2%60:02d}.000"
        fh.write(f"{s} --> {e}\n/thumbs/{sid}/{f}\n\n")
        tm=tm2
        return jsonify({'ok':True,'id':sid,'poster':f'/thumbs/{sid}/poster.jpg','vtt':f'/thumbs/{sid}/thumbs.vtt','dir':f'/thumbs/{sid}/'})


        @thumbs_bp.route('/thumbs/<sid>/<path:p>')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def serve(sid,p):
    try:
        d=os.path.join(OUT, sid)
        if not os.path.exists(os.path.join(d,p)): return ('Not Found',404)
        return send_from_directory(d, p)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

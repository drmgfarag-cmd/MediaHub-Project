from flask import Blueprint, jsonify, request, send_from_directory
import os, subprocess, time, hashlib, threading
from utils.binloc import guess_ffmpeg
import json, os

stream_bp = Blueprint('stream', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
TMP = os.path.join(ROOT,'storage','tmp','hls')
os.makedirs(TMP, exist_ok=True)

jobs={}
def _spawn_hls(src, level='medium'):
    # load encoder prefs
    ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
    CFG=os.path.join(ROOT,'storage','config.json')
    try:
        tr=json.load(open(CFG,'r',encoding='utf-8')).get('transcode',{})
    except Exception:
        tr={}
    vcodec=tr.get('video_encoder','h264') or 'h264'
    ff=guess_ffmpeg()
    if not ff: raise RuntimeError('ffmpeg not found')
    os.makedirs(TMP, exist_ok=True)
    sid = hashlib.md5((src+str(time.time())).encode()).hexdigest()[:12]
    out_dir = os.path.join(TMP, sid); os.makedirs(out_dir, exist_ok=True)
    # simple levels
    v='2000k' if level=='high' else ('800k' if level=='low' else '1200k')
    a='128k'
    cmd=[ff, '-nostdin', '-hide_banner', '-y', '-i', src,
         '-c:v',vcodec,'-b:v',v,'-c:a','aac','-b:a',a,
         '-f','hls','-hls_time','4','-hls_list_size','6','-hls_flags','delete_segments',
         os.path.join(out_dir,'index.m3u8')]
    p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    jobs[sid]={'pid':p.pid,'dir':out_dir,'start':int(time.time()),'src':src,'level':level}
        return sid

@stream_bp.route('/api/stream/hls', methods=['POST'])
def hls():
    js=request.get_json(silent=True) or {}; src=js.get('path'); level=js.get('level','medium')
    if not src: return jsonify({'error':'path required'}),400
    try:
        sid=_spawn_hls(src, level)
        return jsonify({'ok':True,'id':sid,'url':f'/stream/{sid}/index.m3u8'})
    except Exception as e:
        return jsonify({'error':str(e)}),500

@stream_bp.route('/api/stream/status')
def status():
    try:
        sid=request.args.get('id','')
        j=jobs.get(sid); 
        if not j: return jsonify({'error':'not found'}),404
        return jsonify({'ok':True, **j})


        @stream_bp.route('/stream/<sid>/<path:p>')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def serve(sid,p):
    try:
        d=jobs.get(sid,{}).get('dir')
        if not d or not os.path.exists(os.path.join(d,p)): return ('Not Found',404)
        return send_from_directory(d, p)


        from flask import Response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _iter_ffmpeg(cmd):
    import subprocess
    p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=4096)
    try:
        while True:
            chunk=p.stdout.read(4096)
            if not chunk: break
            yield chunk
    finally:
        try: p.terminate()
        except: pass

@stream_bp.route('/api/stream/audio')
def audio_prog():
    try:
        path=request.args.get('path','').strip()
        fmt=(request.args.get('format','mp3') or 'mp3').lower()
        br=str(int(request.args.get('br','192') or 192))+'k'
        ff=guess_ffmpeg()
        if not path or not ff: return ('Missing path or ffmpeg', 400)
        if fmt=='mp3':
        cmd=[ff,'-nostdin','-hide_banner','-i',path,'-vn','-c:a','libmp3lame','-b:a',br,'-f','mp3','pipe:1']
        mime='audio/mpeg'
        else:
        cmd=[ff,'-nostdin','-hide_banner','-i',path,'-vn','-c:a','aac','-b:a',br,'-f','adts','pipe:1']
        mime='audio/aac'
        return Response(_iter_ffmpeg(cmd), mimetype=mime)


        @stream_bp.route('/api/stream/auto')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def auto():
    try:
        # For now just return an HLS job using preferred encoders
        path=request.args.get('path',''); level=request.args.get('level','medium')
        if not path: return jsonify({'error':'path required'}),400
        sid=_spawn_hls(path, level)
        return jsonify({'ok':True,'id':sid,'url':f'/stream/{sid}/index.m3u8'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

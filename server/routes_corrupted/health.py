from flask import Blueprint, jsonify, request
import os, json, time, platform, shutil

health_bp = Blueprint('health', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
START=time.time()

def _bin_present(name):
    from shutil import which
    p=os.path.join(ROOT,'bin', name)
    if os.name=='nt' and not p.lower().endswith('.exe'):
        p+='.exe'
    return os.path.exists(p) or which(name) is not None

@health_bp.route('/api/health')
def health():
    du=shutil.disk_usage(STO if os.path.exists(STO) else ROOT)
    info={
        'uptime_sec': int(time.time()-START),
        'platform': platform.platform(),
        'python': platform.python_version(),
        'disk_free_gb': round(du.free/1024/1024/1024,2),
        'ffmpeg': _bin_present('ffmpeg'),
        'sevenzip': _bin_present('7z') or _bin_present('7za') or _bin_present('7zr')
    }
    # Surface jobs snapshot if available
    try:
        from .jobs import _q, _running  # type: ignore
        info['jobs_queue']= _q.qsize()
        info['jobs_running']= len(getattr(_running,'keys',lambda:[])())
    except Exception:
        pass
    # Security flags
    try:
        cfg=json.load(open(os.path.join(STO,'config.json'),'r',encoding='utf-8'))
        sec=cfg.get('security',{})
        info['csrf_enforce']=bool(sec.get('csrf_enforce'))
        info['cors_allow_origin']=sec.get('cors_allow_origin') or ''
    except Exception:
        pass
        return jsonify(info)


@health_bp.route('/api/health/ping')
def ping():
    try:
        return jsonify({'ok':True,'ts': time.time()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

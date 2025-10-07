from flask import Blueprint, jsonify, request
import os, json, io, tarfile, shutil, requests

hls_bp = Blueprint('hls', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
WEB=os.path.join(ROOT,'web')
DST=os.path.join(WEB,'assets','hls')
VER=os.path.join(DST,'version.txt')

def _installed_version():
    try:
        if os.path.exists(os.path.join(DST,'hls.min.js')):
            return (open(VER,'r',encoding='utf-8').read().strip() if os.path.exists(VER) else 'unknown')
    except Exception:
        pass
    return None

@hls_bp.route('/api/hls/status')
def status():
    v=_installed_version()
    return jsonify({'ok':True, 'installed': bool(v), 'version': v or ''})

@hls_bp.route('/api/hls/fetch', methods=['POST'])
def fetch():
    want=(request.args.get('version') or 'latest').strip()
    meta_url=f'https://registry.npmjs.org/hls.js/{want}'
    r=requests.get(meta_url, timeout=30)
    if r.status_code!=200:
        return jsonify({'error': f'meta {r.status_code}'}), 502
    meta=r.json()
    ver=meta.get('version') or meta.get('dist-tags',{}).get('latest') or 'latest'
    tarball = meta.get('dist',{}).get('tarball')
    if not tarball:
        r2=requests.get('https://registry.npmjs.org/hls.js/latest', timeout=30)
        ver=r2.json().get('version','latest')
        tarball=r2.json().get('dist',{}).get('tarball','')
    if not tarball:
        return jsonify({'error':'no tarball'}), 502
    t=requests.get(tarball, timeout=60)
    if t.status_code!=200:
        return jsonify({'error': f'dl {t.status_code}'}), 502
    os.makedirs(DST, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(t.content), mode='r:gz') as tf:
        members=[m for m in tf.getmembers() if m.name.endswith('/dist/hls.min.js') or m.name.endswith('/dist/hls.min.js.map')]
        tf.extractall(path=DST, members=members)
    # move to DST root
    pkg=os.path.join(DST,'package','dist','hls.min.js')
    if os.path.exists(pkg):
        shutil.move(pkg, os.path.join(DST,'hls.min.js'))
        mapf=os.path.join(DST,'package','dist','hls.min.js.map')
        if os.path.exists(mapf):
            shutil.move(mapf, os.path.join(DST,'hls.min.js.map'))
        shutil.rmtree(os.path.join(DST,'package'), ignore_errors=True)
    open(VER,'w',encoding='utf-8').write(ver)
    return jsonify({'ok':True,'version':ver})

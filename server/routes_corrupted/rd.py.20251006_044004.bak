from flask import Blueprint, jsonify, request
import os, json
from connectors.rd import RealDebrid

rd_bp = Blueprint('rd', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
CFG  = os.path.join(STO, 'config.json')
CLOUD = os.path.join(STO, 'rd_cloud_index.json')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
    except: return {}

@rd_bp.route('/api/rd/dedup')
def dedup():
    token=_cfg().get('rd',{}).get('token','')
    if token:
        try:
            rd=RealDebrid(token); ts=rd.torrents()
            files=[]
            for t in ts or []:
                for f in t.get('files', []):
                    files.append({'id': f.get('id'), 'filename': f.get('path') or f.get('filename') or t.get('filename'), 'filesize': f.get('bytes') or f.get('filesize') or 0})
            groups = RealDebrid.group_duplicates(files)
            return jsonify({'ok': True, 'groups': groups})
        except Exception:
            pass
    # fallback to stored snapshot
    try: js=json.load(open(CLOUD,'r',encoding='utf-8'))
    except: js={'groups': []}
    return jsonify({'ok': True, **js})

@rd_bp.route('/api/rd/cloudpull', methods=['POST','GET'])
def cloudpull():
    cfg_path = os.path.join(STO, 'rd_cloudpull_cfg.json')
    if request.method=='POST':
        js=request.get_json(silent=True) or {}
        open(cfg_path+'.tmp','w',encoding='utf-8').write(json.dumps(js,indent=2)); os.replace(cfg_path+'.tmp', cfg_path)
        return jsonify({'ok': True})
    try: cfg = json.load(open(cfg_path,'r',encoding='utf-8'))
    except: cfg = {}
    return jsonify({'ok': True, 'config': cfg})

@rd_bp.route('/api/rd/list')
def list_all():
    token=_cfg().get('rd',{}).get('token','')
    out={'torrents':[], 'links':[]}
    if token:
        try:
            rd=RealDebrid(token)
            out['torrents']= rd.torrents() or []
        except Exception: pass
    return jsonify({'ok': True, **out})

@rd_bp.route('/api/rd/add_magnet', methods=['POST'])
def add_magnet():
    token=_cfg().get('rd',{}).get('token','')
    js=request.get_json(silent=True) or {}; mg=js.get('magnet','')
    if not token or not mg: return jsonify({'error':'missing token or magnet'}),400
    try:
        rd=RealDebrid(token); res=rd.add_magnet(mg); return jsonify({'ok': True, 'res': res})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rd_bp.route('/api/rd/delete', methods=['POST'])
def delete_torrent():
    token=_cfg().get('rd',{}).get('token','')
    js=request.get_json(silent=True) or {}; tid=js.get('id','')
    if not token or not tid: return jsonify({'error':'missing token or id'}),400
    try:
        rd=RealDebrid(token); res=rd.del_torrent(tid); return jsonify({'ok': True, 'res': res})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rd_bp.route('/api/rd/unrestrict', methods=['POST'])
def unrestrict():
    token=_cfg().get('rd',{}).get('token','')
    js=request.get_json(silent=True) or {}; link=js.get('link','')
    if not token or not link: return jsonify({'error':'missing token or link'}),400
    try:
        rd=RealDebrid(token); res=rd.unrestrict(link); return jsonify({'ok': True, 'res': res})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rd_bp.route('/api/rd/account')
def account():
    token=_cfg().get('rd',{}).get('token','')
    if not token: return jsonify({'error':'missing token'}), 400
    try:
        rd=RealDebrid(token)
        info=rd.user() if hasattr(rd,'user') else {}
        traffic=rd.traffic() if hasattr(rd,'traffic') else {}
        hosts=rd.hosts() if hasattr(rd,'hosts') else {}
        return jsonify({'ok':True, 'info':info, 'traffic':traffic, 'hosts':hosts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rd_bp.route('/api/rd/torrent_info')
def torrent_info():
    token=_cfg().get('rd',{}).get('token','')
    tid=(request.args.get('id') or '').strip()
    if not token or not tid: return jsonify({'error':'missing token or id'}),400
    try:
        rd=RealDebrid(token)
        info = rd.torrent_info(tid) if hasattr(rd,'torrent_info') else {}
        return jsonify({'ok':True, 'info': info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rd_bp.route('/api/rd/select_files', methods=['POST'])
def select_files():
    token=_cfg().get('rd',{}).get('token','')
    js=request.get_json(silent=True) or {}; tid=js.get('id',''); files=js.get('files',[])
    if not token or not tid: return jsonify({'error':'missing token or id'}),400
    try:
        rd=RealDebrid(token)
        res = rd.select_files(tid, files) if hasattr(rd,'select_files') else {'ok':False}
        return jsonify({'ok':True,'res':res})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

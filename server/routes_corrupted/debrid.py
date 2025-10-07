from flask import Blueprint, jsonify, request
import os, json
from connectors.alldebrid import AllDebrid
from connectors.premiumize import Premiumize
from connectors.rd import RealDebrid as RD  # existing wrapper
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
CFG=os.path.join(ROOT,'storage','config.json')

debrid_bp = Blueprint('debrid', __name__)

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
        except Exception: return {}

def _provider():
    c=_cfg().get('debrid',{})
    prov=(c.get('provider') or 'rd').lower()
    if prov=='alldebrid':
        return AllDebrid((c.get('alldebrid') or {}).get('apikey',''))
    if prov=='premiumize':
        return Premiumize((c.get('premiumize') or {}).get('apikey',''))
    # default RD
        return RD((_cfg().get('rd') or {}).get('token',''))

@debrid_bp.route('/api/debrid/list')
def list_():
    p=_provider()
        try: return jsonify({'ok':True,'items': p.torrents()})
        except Exception as e: return jsonify({'error': str(e)}), 500

@debrid_bp.route('/api/debrid/add_magnet', methods=['POST'])
def add_magnet():
    js=request.get_json(silent=True) or {}; mg=js.get('magnet','')
        if not mg: return jsonify({'error':'magnet required'}),400
    p=_provider()
        try: return jsonify({'ok':True,'res': p.add_magnet(mg)})
        except Exception as e: return jsonify({'error': str(e)}), 500

@debrid_bp.route('/api/debrid/delete', methods=['POST'])
def delete():
    js=request.get_json(silent=True) or {}; tid=js.get('id','')
        if not tid: return jsonify({'error':'id required'}),400
    p=_provider()
        try: return jsonify({'ok':True,'res': p.del_torrent(tid)})
        except Exception as e: return jsonify({'error': str(e)}), 500

@debrid_bp.route('/api/debrid/unrestrict', methods=['POST'])
def unrestrict():
    js=request.get_json(silent=True) or {}; link=js.get('link','')
        if not link: return jsonify({'error':'link required'}),400
    p=_provider()
        try: return jsonify({'ok':True,'res': p.unrestrict(link)})
        except Exception as e: return jsonify({'error': str(e)}), 500

@debrid_bp.route('/api/debrid/account')
def account():
    p=_provider()
        try: return jsonify({'ok':True,'info': p.user()})
        except Exception as e: return jsonify({'error': str(e)}), 500

@debrid_bp.route('/api/debrid/torrent_info')
def torrent_info():
    tid=(request.args.get('id') or '').strip()
        if not tid: return jsonify({'error':'id required'}),400
    p=_provider()
        try: return jsonify({'ok':True,'info': p.torrent_info(tid)})
        except Exception as e: return jsonify({'error': str(e)}), 500

@debrid_bp.route('/api/debrid/select_files', methods=['POST'])
def select_files():
    js=request.get_json(silent=True) or {}; tid=js.get('id',''); files=js.get('files',[])
        if not tid: return jsonify({'error':'id required'}),400
    p=_provider()
        try: return jsonify({'ok':True,'res': p.select_files(tid, files)})
        except Exception as e: return jsonify({'error': str(e)}), 500

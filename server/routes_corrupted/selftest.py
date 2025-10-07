from flask import Blueprint, jsonify
import os, socket, time, json
from utils.binloc import guess_ffmpeg, guess_7z
from connectors.aria2 import Aria2
from connectors.qb import QBit

selftest_bp = Blueprint('selftest', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default

@selftest_bp.route('/api/selftest/run')
def run():
    cfg=_load(CFG,{})
    res={'ffmpeg':False,'sevenzip':False,'aria2':False,'qb':False,'storage_perm':False,'downloads_perm':False}
    res['ffmpeg'] = True if guess_ffmpeg() else False
    res['sevenzip'] = True if guess_7z() else False
    # permissions
    try:
        p=os.path.join(STO,'tmp','_perm.txt'); os.makedirs(os.path.dirname(p), exist_ok=True); open(p,'w').write('ok'); os.remove(p); res['storage_perm']=True
    except Exception: res['storage_perm']=False
    try:
        d=os.path.join(ROOT,'downloads'); os.makedirs(d, exist_ok=True); open(os.path.join(d,'_perm.txt'),'w').write('ok'); os.remove(os.path.join(d,'_perm.txt')); res['downloads_perm']=True
    except Exception: res['downloads_perm']=False
    # aria2
    try:
        if cfg.get('aria2',{}).get('rpc_url'):
            a=Aria2(cfg['aria2']['rpc_url'], cfg['aria2'].get('secret'))
            a.get_version(); res['aria2']=True
    except Exception: res['aria2']=False
    # qbittorrent
    try:
        if cfg.get('qb',{}).get('base_url'):
            q=QBit(cfg['qb']['base_url'], cfg['qb'].get('username',''), cfg['qb'].get('password',''))
            q.version(); res['qb']=True
    except Exception: res['qb']=False
        return jsonify({'ok':True, 'results': res})

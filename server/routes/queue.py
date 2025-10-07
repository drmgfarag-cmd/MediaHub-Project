from flask import Blueprint, jsonify, request
import os, json
from connectors.aria2 import Aria2
from connectors.qb import QBit

q_bp=Blueprint('queue',__name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
    except: return {}

import re, time
@q_bp.route('/api/queue/list')
def _pkgname(n):
    if not n: return '(unknown)'
    m=re.split(r'[\[\(\.]', n)
    return m[0].strip() or n

def q_list():
    cfg=_cfg(); rows=[]
    # aria2
    try:
        a=cfg.get('aria2',{})
        if a.get('rpc_url'):
            ar=Aria2(a['rpc_url'], a.get('secret'))
            for it in (ar.tell_active() + ar.tell_waiting(0,100)):
                rows.append({'name': it.get('bittorrent',{}).get('info',{}).get('name') or (it.get('files',[{}])[0].get('path','') or 'aria2 item'),
                             'status': it.get('status','?').title(),
                             'progress': int(float(it.get('completedLength','0'))*100/max(int(it.get('totalLength','1')),1)),
                             'referrer': it.get('bittorrent',{}).get('announceList',[['']])[0][0] if it.get('bittorrent') else '',
                             'hoster':'aria2','last_try':'','save_path': it.get('dir',''),'description':'', 'package': _pkgname(it.get('bittorrent',{}).get('info',{}).get('name') or (it.get('files',[{}])[0].get('path',''))), 'added': ''})
    except Exception: pass
    # qBittorrent
    try:
        qb=cfg.get('qb',{})
        if qb.get('base_url'):
            q=QBit(qb['base_url'], qb.get('username',''), qb.get('password','')); q.login()
            for t in q.info():
                rows.append({'name': t.get('name','qB item'),'status': t.get('state','queued').title(),
                             'progress': int(float(t.get('progress',0))*100),
                             'referrer':'','hoster':'qBittorrent','last_try':'','save_path': t.get('save_path',''),'description':'', 'package': _pkgname(it.get('bittorrent',{}).get('info',{}).get('name') or (it.get('files',[{}])[0].get('path',''))), 'added': ''})
    except Exception: pass
    return jsonify({'rows': rows or [{'name':'(empty queue)','status':'Idle','progress':0}]})

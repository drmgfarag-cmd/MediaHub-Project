from flask import Blueprint, jsonify, request
import os, io

logs_bp = Blueprint('logs', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
LOG=os.path.join(ROOT,'storage','logs','app.log')

@logs_bp.route('/api/logs/tail')
def tail():
    n=int(request.args.get('n','500') or 500)
    if not os.path.exists(LOG): return jsonify({'ok':True,'lines':[]})
    with open(LOG,'r',encoding='utf-8', errors='ignore') as fh:
        fh.seek(0, os.SEEK_END)
        size=fh.tell()
        fh.seek(max(0,size-200000), os.SEEK_SET)
        data=fh.read()
    lines=data.splitlines()[-n:]
    return jsonify({'ok':True,'lines':lines})

from flask import Blueprint, jsonify, request
import os, json
cfg_bp = Blueprint('config', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json'); GATES=os.path.join(STO,'feature_gates.json'); RSS=os.path.join(STO,'rss_feeds.json'); COL=os.path.join(STO,'collections.json')
def _load(p,d): 
    try: return json.load(open(p,'r',encoding='utf-8'))
    except: return d
def _save(p,o): open(p+'.tmp','w',encoding='utf-8').write(json.dumps(o,indent=2)); os.replace(p+'.tmp',p)

@cfg_bp.route('/api/config/get')
def get_cfg():
    return jsonify(_load(CFG, {"aria2":{"rpc_url":"","secret":""},"qb":{"base_url":"","username":"","password":""},"rd":{"token":""},"tmdb":{"api_key":""},"trakt":{"client_id":""},"rails":{"refresh_sec":30}}))
@cfg_bp.route('/api/config/set',methods=['POST'])
def set_cfg(): js=request.get_json(silent=True) or {}; _save(CFG, js); return jsonify({'ok':True})

@cfg_bp.route('/api/gates/get')
def get_g():
    return jsonify(_load(GATES, {"rails":True,"rd":True,"rss":True,"opds":True,"downloader":True,"editor":True}))
@cfg_bp.route('/api/gates/set',methods=['POST'])
def set_g(): js=request.get_json(silent=True) or {}; _save(GATES, js); return jsonify({'ok':True})

@cfg_bp.route('/api/rss/feeds')
def get_rss():
    return jsonify(_load(RSS, {"feeds":[{"name":"Example TV","url":"https://example.com/rss"}]}))
@cfg_bp.route('/api/rss/feeds/set',methods=['POST'])
def set_rss(): js=request.get_json(silent=True) or {}; _save(RSS, js); return jsonify({'ok':True})

@cfg_bp.route('/api/collections/rules')
def get_col():
    return jsonify(_load(COL, {"rules":[]}))
@cfg_bp.route('/api/collections/rules/set',methods=['POST'])
def set_col(): js=request.get_json(silent=True) or {}; _save(COL, js); return jsonify({'ok':True})

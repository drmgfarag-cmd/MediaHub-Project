from flask import Blueprint, jsonify, request
import os, json, time
rss_feeder_bp = Blueprint('rss', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
RDB=os.path.join(STO,'rss_feeds.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

def _enabled():
        cfg=_load(CFG,{}); return (cfg.get('features',{})).get('rss_feeder', False)

@rss_feeder_bp.route('/api/rss/feeds')
def feeds():
    try:
        if not _enabled(): return jsonify({'enabled': False, 'feeds': []})
        return jsonify({'enabled': True, **_load(RDB, {'feeds': []})})

        @rss_feeder_bp.route('/api/rss/add', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def add():
    try:
        js=request.get_json(silent=True) or {}
        if not _enabled(): return jsonify({'error':'disabled'}), 403
        db=_load(RDB, {'feeds': []}); url=(js.get('url') or '').strip(); tag=(js.get('tag') or '').strip()
        if not url: return jsonify({'error':'url'}), 400
        db['feeds']=[f for f in db['feeds'] if f.get('url')!=url]
        db['feeds'].append({'url': url, 'tag': tag, 'last_refresh': 0, 'items': []})
        _save(RDB, db); return jsonify({'ok':True})

        @rss_feeder_bp.route('/api/rss/remove', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rm():
    try:
        js=request.get_json(silent=True) or {}
        if not _enabled(): return jsonify({'error':'disabled'}), 403
        db=_load(RDB, {'feeds': []}); url=(js.get('url') or '').strip()
        db['feeds']=[f for f in db['feeds'] if f.get('url')!=url]; _save(RDB, db); return jsonify({'ok':True})

        @rss_feeder_bp.route('/api/rss/refresh', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rf():
    try:
        js=request.get_json(silent=True) or {}
        if not _enabled(): return jsonify({'error':'disabled'}), 403
        db=_load(RDB, {'feeds': []}); now=int(time.time())
        # Offline placeholder: just stamp last_refresh; items would come from a real fetcher.
        for f in db['feeds']: f['last_refresh']=now
        _save(RDB, db); return jsonify({'ok':True,'feeds': db['feeds']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import Blueprint, jsonify, request
import os, json, time, re, hashlib, xml.etree.ElementTree as ET

feeds_bp = Blueprint('feeds', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
FF=os.path.join(STO,'feeds.json')
FC=os.path.join(STO,'feeds_cache.json')
QF=os.path.join(STO,'downloader_queue.json')
ST=os.path.join(STO,'search_tasks.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except Exception: return default

def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

@feeds_bp.route('/api/feeds/get')
def get():
    return jsonify(_load(FF, {'feeds':[], 'search_templates':{}}))

@feeds_bp.route('/api/feeds/set', methods=['POST'])
def set_():
    js=request.get_json(silent=True) or {}
    _save(FF, js); return jsonify({'ok':True})

@feeds_bp.route('/api/feeds/add', methods=['POST'])
def add():
    js=request.get_json(silent=True) or {}
    data=_load(FF, {'feeds':[], 'search_templates':{}})
    rec={'id': js.get('id') or str(int(time.time()*1000))[-8:], 'name': js.get('name') or 'Feed', 'type':'rss', 'url': js.get('url') or '', 'enabled': bool(js.get('enabled', True)), 'last_pull':0, 'items_count':0}
    data.setdefault('feeds', []).append(rec); _save(FF, data); return jsonify({'ok':True,'id':rec['id']})

def _parse_rss(xml):
    out=[]
    try:
        root=ET.fromstring(xml)
        for it in root.findall('.//item'):
            title=(it.findtext('title') or '').strip()
            link=(it.findtext('link') or '').strip()
            en=None
            enc=it.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            enclosure=it.find('enclosure')
            if enclosure is not None:
                en=enclosure.get('url')
            pub=(it.findtext('pubDate') or '').strip()
            guid=(it.findtext('guid') or '').strip() or link or title
            if not (title or link): continue
            out.append({'id': hashlib.sha1((guid or title).encode('utf-8')).hexdigest()[:12], 'title': title, 'link': link, 'enclosure': en, 'pubDate': pub})
    except Exception:
        pass
    return out

@feeds_bp.route('/api/feeds/refresh', methods=['POST'])
def refresh():
    js=request.get_json(silent=True) or {}
    fid=(js.get('id') or '').strip()
    mode=(js.get('mode') or 'paste')
    data=_load(FF, {'feeds':[], 'search_templates':{}}); cache=_load(FC, {'items':{}})
    feed=next((f for f in data.get('feeds',[]) if f.get('id')==fid), None)
    if not feed: return jsonify({'error':'feed not found'}), 404
    if mode=='paste':
        xml=(js.get('xml') or '').strip()
        items=_parse_rss(xml)
        cache['items'][fid]=items; feed['last_pull']=int(time.time()); feed['items_count']=len(items)
        _save(FC, cache); _save(FF, data)
        return jsonify({'ok':True,'imported': len(items)})
    return jsonify({'error':'offline mode: only paste supported'}), 400

@feeds_bp.route('/api/feeds/items')
def items():
    fid=(request.args.get('id') or '').strip()
    cache=_load(FC, {'items':{}})
    return jsonify({'items': cache.get('items',{}).get(fid, [])})

@feeds_bp.route('/api/feeds/queue_add', methods=['POST'])
def queue_add():
    js=request.get_json(silent=True) or {}
    title=(js.get('title') or 'New Item').strip()
    link=(js.get('link') or '').strip()
    save_to=(js.get('save_to') or '')
    q=_load(QF, {'packages':[]})
    pkg={'id': str(int(time.time()*1000))[-8:], 'name': title, 'save_to': save_to, 'priority':'Normal', 'added_ts': int(time.time()), 'status':'Queued','speed_kbps':0,'progress':0,'eta_sec':0, 'files':[{'id':'f'+str(int(time.time()*1000))[-6:], 'name': title, 'size':'—', 'progress':0, 'speed_kbps':0, 'eta_sec':0, 'status':'Queued', 'attempts':0, 'referrer': link, 'hoster':'feed', 'save_to': save_to}]}
    q['packages'].append(pkg); _save(QF,q); return jsonify({'ok':True,'id':pkg['id']})

@feeds_bp.route('/api/search/templates_get')
def st_get():
    return jsonify(_load(FF, {'feeds':[], 'search_templates':{}}).get('search_templates', {}))

@feeds_bp.route('/api/search/templates_set', methods=['POST'])
def st_set():
    js=request.get_json(silent=True) or {}
    data=_load(FF, {'feeds':[], 'search_templates':{}})
    data['search_templates']=js
    _save(FF, data); return jsonify({'ok':True})

@feeds_bp.route('/api/search/tasks_add', methods=['POST'])
def tasks_add():
    js=request.get_json(silent=True) or {}
    q=(js.get('q') or '').strip()
    st=_load(ST, {'tasks':[]}); st['tasks'].append({'q': q, 'ts': int(time.time())}); _save(ST, st)
    return jsonify({'ok':True})

@feeds_bp.route('/api/search/tasks_list')
def tasks_list():
    return jsonify(_load(ST, {'tasks':[]}))

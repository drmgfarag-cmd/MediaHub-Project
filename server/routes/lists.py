from flask import Blueprint, jsonify, request
import os, json, re, time, requests

lists_bp = Blueprint('lists', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
IMP=os.path.join(STO,'lists_imports.json')
CAT=os.path.join(STO,'lists_catalog.json')
COL=os.path.join(STO,'collections.json')
IDX=os.path.join(STO,'library_index.json')
SCH=os.path.join(STO,'lists_schedule.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except Exception: return default

def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

def _items():
    return _load(IDX, [])

@lists_bp.route('/api/lists/catalog')
def catalog():
    return jsonify(_load(CAT, {'popular':[]}))

@lists_bp.route('/api/lists/imports')
def imports():
    return jsonify(_load(IMP, {'imports':[]}))

@lists_bp.route('/api/lists/schedule_get')
def schedule_get():
    return jsonify(_load(SCH, {'enabled':True, 'interval_minutes':720}))

@lists_bp.route('/api/lists/schedule_set', methods=['POST'])
def schedule_set():
    js=request.get_json(silent=True) or {}
    en=bool(js.get('enabled', True))
    iv=int(js.get('interval_minutes', 720))
    _save(SCH, {'enabled': en, 'interval_minutes': iv})
    return jsonify({'ok':True})

def _fetch(provider, pid, url):
    # Minimal fetchers; offline-safe. Return list of titles (strings).
    titles=[]
    try:
        if provider=='imdb' and url:
            r=requests.get(url, timeout=10)
            if r.status_code==200:
                # grab table titles up to 250
                titles = re.findall(r'<td class="titleColumn">\s*<a[^>]*>(.*?)</a>', r.text, re.S)[:250]
        elif provider=='tmdb':
            # public trending endpoints require API key; skip network; just note placeholder
            titles = []
        elif provider=='trakt':
            # requires auth; skip network
            titles = []
    except Exception:
        titles=[]
    return titles

def _collection_rules_from_titles(typ, titles):
    rules=[]
    for t in titles:
        # title regex (case-insensitive word boundary)
        safe=re.escape(t)
        rules.append({'type': 'movie' if typ=='movie' else ('series' if typ=='series' else typ),
                      'title_re': f'(?i)\\b{safe}\\b'})
    return rules

@lists_bp.route('/api/lists/import', methods=['POST'])
def do_import():
    js=request.get_json(silent=True) or {}
    provider=(js.get('provider') or '').lower()
    typ=(js.get('type') or 'movie').lower()
    name=(js.get('name') or f'Imported {provider}').strip()
    pid=(js.get('id') or '').strip()
    url=(js.get('url') or '').strip()
    top_n=int(js.get('top_n') or 50)
    data=_load(IMP, {'imports':[]})
    rec={'provider':provider,'type':typ,'name':name,'id':pid,'url':url,'top_n':top_n,'last_refresh':0}
    # Upsert
    data['imports']=[r for r in data['imports'] if r.get('name')!=name]
    data['imports'].append(rec); _save(IMP, data)
    # Try fetching immediately
    titles=_fetch(provider, pid, url)[:top_n]
    coll=_load(COL, {'collections':[]})
    rules=_collection_rules_from_titles(typ, titles) if titles else [{'type': typ, 'title_re': '(?i)^$'}]  # placeholder empty match if offline
    coll['collections']=[c for c in coll['collections'] if c.get('name')!=name]
    coll['collections'].append({'name': name, 'rules': rules, 'source': {'provider':provider,'id':pid,'url':url}, 'ts': int(time.time())})
    _save(COL, coll)
    # Update import timestamp
    data=_load(IMP, {'imports':[]})
    for r in data['imports']:
        if r['name']==name: r['last_refresh']=int(time.time())
    _save(IMP, data)
    return jsonify({'ok':True,'imported': name, 'titles': len(titles)})

@lists_bp.route('/api/lists/refresh', methods=['POST'])
def refresh():
    data=_load(IMP, {'imports':[]})
    coll=_load(COL, {'collections':[]})
    updated=0
    for r in data['imports']:
        titles=_fetch(r.get('provider'), r.get('id'), r.get('url'))[:int(r.get('top_n') or 50)]
        if titles:
            # replace collection with new rules
            coll['collections']=[c for c in coll['collections'] if c.get('name')!=r['name']]
            coll['collections'].append({'name': r['name'], 'rules': _collection_rules_from_titles(r.get('type','movie'), titles), 'source': {'provider':r.get('provider'),'id':r.get('id'),'url':r.get('url')}, 'ts': int(time.time())})
            updated+=1
            r['last_refresh']=int(time.time())
    _save(COL, coll); _save(IMP, data)
    return jsonify({'ok':True,'updated':updated})

@lists_bp.route('/api/lists/top50_templates')
def top50():
    cat=(request.args.get('category') or 'movies').lower()
    items=_items()
    def pick(filter_fn, key='added_ts', n=50):
        arr=[it for it in items if filter_fn(it)]
        arr=sorted(arr, key=lambda x: x.get(key) or 0, reverse=True)[:n]
        return [it.get('title') or it.get('path','') for it in arr]
    if cat=='movies':
        titles=pick(lambda it: it.get('type')=='movie')
        name='Top 50 — Movies (Recently Added)'
        rules=_collection_rules_from_titles('movie', titles)
    elif cat=='tv':
        titles=pick(lambda it: it.get('type') in ('series','episode'))
        name='Top 50 — TV (Recently Added)'
        rules=_collection_rules_from_titles('series', titles)
    elif cat=='books':
        titles=pick(lambda it: it.get('type') in ('ebook','comic','manga'))
        name='Top 50 — Books (Recently Added)'
        rules=_collection_rules_from_titles('ebook', titles)
    else:  # audio
        titles=pick(lambda it: it.get('type') in ('audio','audiobook'))
        name='Top 50 — Audio (Recently Added)'
        rules=_collection_rules_from_titles('audio', titles)
    return jsonify({'name': name, 'rules': rules})

@lists_bp.route('/api/lists/create_template', methods=['POST'])
def create_template():
    js=request.get_json(silent=True) or {}
    name=js.get('name','Top 50')
    rules=js.get('rules') or []
    coll=_load(COL, {'collections':[]})
    coll['collections']=[c for c in coll['collections'] if c.get('name')!=name]
    coll['collections'].append({'name': name, 'rules': rules, 'ts': int(time.time())})
    _save(COL, coll)
    return jsonify({'ok':True})

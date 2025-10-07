from flask import Blueprint, jsonify, request
import os, json, time, hashlib, re

want_bp = Blueprint('want', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
WANT=os.path.join(STO,'wanted.json')
LIB =os.path.join(STO,'library_index.json')
QUE =os.path.join(STO,'downloader_queue.json')
TASK=os.path.join(STO,'search_tasks.json')
COLS=os.path.join(STO,'collections.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except Exception: return default

def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

def _norm(s): return (s or '').strip().lower()

def _in_lib(title):
    lib=_load(LIB, []); t=_norm(title)
    for it in lib:
        cand=_norm(it.get('title') or os.path.basename(it.get('path') or ''))
        if t and t in cand: return True
    return False

def _in_queue(title):
    q=_load(QUE, {'packages':[]}); t=_norm(title)
    for p in q.get('packages',[]):
        if t and t in _norm(p.get('name') or ''): return True
        for f in p.get('files',[]) or []:
            if t and t in _norm(f.get('name') or ''): return True
    return False

def _in_tasks(title):
    ts=_load(TASK, {'tasks':[]}).get('tasks',[]); t=_norm(title)
    for x in ts:
        if t and t in _norm(x.get('q') or ''): return True
    return False

def _status(title):
    if _in_lib(title): return 'Obtained'
    if _in_queue(title): return 'Queued'
    if _in_tasks(title): return 'Searching'
    return 'Wanted'

@want_bp.route('/api/wanted/get')
def get():
    dat=_load(WANT, {'items':[]}); out=[]
    for it in dat.get('items',[]):
        st=_status(it.get('title') or '')
        it2=dict(it); it2['status']=st; out.append(it2)
    return jsonify({'items': out})

@want_bp.route('/api/wanted/add', methods=['POST'])
def add():
    js=request.get_json(silent=True) or {}
    title=(js.get('title') or '').strip()
    if not title: return jsonify({'error':'title required'}), 400
    typ=(js.get('type') or '').strip()
    note=(js.get('note') or '').strip()
    col=(js.get('collection') or '').strip()
    dat=_load(WANT, {'items':[]}); arr=dat.setdefault('items',[])
    if not any(_norm(i.get('title'))==_norm(title) for i in arr):
        arr.append({'id': hashlib.sha1((title+str(time.time())).encode('utf-8')).hexdigest()[:10], 'title': title, 'type': typ, 'note': note, 'collection': col, 'created_ts': int(time.time())})
        _save(WANT, dat)
    return jsonify({'ok':True})

@want_bp.route('/api/wanted/remove', methods=['POST'])
def remove():
    js=request.get_json(silent=True) or {}
    rid=(js.get('id') or '').strip()
    dat=_load(WANT, {'items':[]}); arr=dat.get('items',[])
    arr=[i for i in arr if i.get('id')!=rid]; dat['items']=arr; _save(WANT, dat); return jsonify({'ok':True})

@want_bp.route('/api/wanted/search_task', methods=['POST'])
def search_task():
    js=request.get_json(silent=True) or {}
    title=(js.get('title') or '').strip()
    if not title: return jsonify({'error':'title required'}), 400
    st=_load(TASK, {'tasks':[]}); st['tasks'].append({'q': title, 'ts': int(time.time())}); _save(TASK, st); return jsonify({'ok':True})

@want_bp.route('/api/wanted/auto_queue', methods=['POST'])
def auto_queue():
    js=request.get_json(silent=True) or {}
    title=(js.get('title') or '').strip(); save_to=(js.get('save_to') or '').strip()
    from routes.auto_select import _pool, _load as _aload, RULES, _queue_pkg
    rules=_aload(RULES, {}); pool=_pool(title, rules)
    if not pool: return jsonify({'error':'no candidates'}), 404
    b=pool[0]; pid=_queue_pkg(b.get('title') or title, b.get('link') or '', b.get('kind') or 'auto', save_to)
    return jsonify({'ok':True,'queued_id': pid, 'selected': b})

def _resolve_collection(name):
    cols=_load(COLS, {'collections':[]}).get('collections',[])
    col=next((c for c in cols if c.get('name')==name), None)
    if not col: return []
    rules=col.get('rules') or []; lib=_load(LIB, []); out=[]
    for it in lib:
        t=it.get('title') or os.path.basename(it.get('path') or ''); p=it.get('path') or ''
        ok=False
        for r in rules:
            tre=r.get('title_re'); pre=r.get('path_re')
            if tre and re.search(tre, t, re.I): ok=True
            if pre and re.search(pre, p, re.I): ok=True
            if ok: break
        if ok: out.append(t)
    return out

@want_bp.route('/api/wanted/seed_collection', methods=['POST'])
def seed_collection():
    js=request.get_json(silent=True) or {}
    name=(js.get('name') or '').strip(); maxn=int(js.get('max') or 25)
    if not name: return jsonify({'error':'name required'}), 400
    titles=_resolve_collection(name)[:maxn]
    dat=_load(WANT, {'items':[]}); arr=dat.setdefault('items',[]); add=0
    for t in titles:
        if not any(_norm(i.get('title'))==_norm(t) for i in arr):
            arr.append({'id': hashlib.sha1((t+str(time.time())).encode('utf-8')).hexdigest()[:10], 'title': t, 'type':'movie', 'note':'seeded from '+name, 'collection': name, 'created_ts': int(time.time())})
            add+=1
    _save(WANT, dat); return jsonify({'ok':True,'added': add})

@want_bp.route('/api/wanted/refresh_config_get')
def refresh_cfg_get():
    cfg=_load(os.path.join(STO,'wanted_schedule.json'), {})
    return jsonify(cfg)

@want_bp.route('/api/wanted/refresh_config_set', methods=['POST'])
def refresh_cfg_set():
    js=request.get_json(silent=True) or {}
    cur=_load(os.path.join(STO,'wanted_schedule.json'), {})
    cur.update({
        'enabled': bool(js.get('enabled', cur.get('enabled', True))),
        'interval_min': int(js.get('interval_min', cur.get('interval_min', 60))),
        'auto_action': js.get('auto_action', cur.get('auto_action', 'search_only')),
        'max_per_run': int(js.get('max_per_run', cur.get('max_per_run', 10))),
    })
    now=int(time.time())
    if not cur.get('next_run'):
        cur['next_run']= now + cur.get('interval_min',60)*60
    tmp=os.path.join(STO,'wanted_schedule.json')+'.tmp'; json.dump(cur, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, os.path.join(STO,'wanted_schedule.json'))
    return jsonify({'ok':True})

def _journal_log(kind, title, meta=None):
    J=os.path.join(STO,'wanted_journal.json')
    dat=_load(J, {'events':[]})
    evt={'ts': int(time.time()), 'kind': kind, 'title': title, 'meta': meta or {}}
    dat['events'].append(evt)
    tmp=J+'.tmp'; json.dump(dat, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, J)

@want_bp.route('/api/wanted/journal_get')
def journal_get():
    lim=int(request.args.get('limit') or 200)
    dat=_load(os.path.join(STO,'wanted_journal.json'), {'events':[]})
    arr=sorted(dat.get('events',[]), key=lambda x: x.get('ts',0), reverse=True)[:lim]
    return jsonify({'events': arr})

@want_bp.route('/api/wanted/journal_clear', methods=['POST'])
def journal_clear():
    J=os.path.join(STO,'wanted_journal.json')
    tmp=J+'.tmp'; json.dump({'events':[]}, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, J)
    return jsonify({'ok':True})

def _compute_status_and_journal():
    W=os.path.join(STO,'wanted.json')
    dat=_load(W, {'items':[]}); changed=0
    arr=dat.get('items',[])
    for it in arr:
        title=it.get('title') or ''
        old=it.get('last_status') or 'Wanted'
        new=_status(title)
        if new!=old:
            it['last_status']=new
            _journal_log('status_change', title, {'from': old, 'to': new})
            changed+=1
    tmp=W+'.tmp'; json.dump(dat, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, W)
    return changed

@want_bp.route('/api/wanted/refresh_now', methods=['POST'])
def refresh_now():
    cfg=_load(os.path.join(STO,'wanted_schedule.json'), {})
    WJ={'queued':0,'search_added':0,'conflicts':0,'status_changed':0,'processed':0,'skipped':0}
    # first update statuses & journal transitions
    WJ['status_changed'] = _compute_status_and_journal()
    # process items
    dat=_load(os.path.join(STO,'wanted.json'), {'items':[]})
    maxn=int(cfg.get('max_per_run',10)); cnt=0
    action=(cfg.get('auto_action') or 'search_only').lower()
    for it in dat.get('items',[]):
        if cnt>=maxn: break
        title=(it.get('title') or '').strip()
        st=_status(title)
        if st=='Obtained': WJ['skipped']+=1; continue
        # optional: add search tasks
        if action in ('search_only','queue_best'):
            if not _in_tasks(title):
                stf=_load(os.path.join(STO,'search_tasks.json'), {'tasks':[]})
                stf['tasks'].append({'q': title, 'ts': int(time.time())})
                tmp=os.path.join(STO,'search_tasks.json')+'.tmp'; json.dump(stf, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, os.path.join(STO,'search_tasks.json'))
                _journal_log('search_added', title, {})
                WJ['search_added']+=1
        # optional: auto queue
        if action=='queue_best' and st in ('Wanted','Searching'):
            # conflict check: already in queue or library
            if _in_lib(title) or _in_queue(title):
                WJ['conflicts']+=1
            else:
                from routes.auto_select import _pool, _load as _aload, RULES, _queue_pkg
                rules=_aload(RULES, {}); pool=_pool(title, rules)
                if pool:
                    b=pool[0]; pid=_queue_pkg(b.get('title') or title, b.get('link') or '', b.get('kind') or 'auto', '')
                    _journal_log('auto_queued', title, {'selected': b, 'pkg_id': pid})
                    WJ['queued']+=1
                    cnt+=1
    # update schedule
    now=int(time.time())
    cfg['last_run']=now; cfg['next_run']= now + int(cfg.get('interval_min',60))*60; cfg['last_report']=WJ
    tmp=os.path.join(STO,'wanted_schedule.json')+'.tmp'; json.dump(cfg, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, os.path.join(STO,'wanted_schedule.json'))
    return jsonify({'ok':True,'report': WJ, 'next_run': cfg['next_run']})

# Enhance auto_queue with conflict prompt
@want_bp.route('/api/wanted/auto_queue_checked', methods=['POST'])
def auto_queue_checked():
    js=request.get_json(silent=True) or {}
    title=(js.get('title') or '').strip(); force=bool(js.get('force', False))
    save_to=(js.get('save_to') or '').strip()
    if not title: return jsonify({'error':'title required'}), 400
    if (_in_lib(title) or _in_queue(title)) and not force:
        where = 'library' if _in_lib(title) else 'queue'
        return jsonify({'conflict': True, 'where': where, 'message': f'“{title}” exists in {where}. Force to queue anyway.'}), 200
    from routes.auto_select import _pool, _load as _aload, RULES, _queue_pkg
    rules=_aload(RULES, {}); pool=_pool(title, rules)
    if not pool: return jsonify({'error':'no candidates'}), 404
    b=pool[0]; pid=_queue_pkg(b.get('title') or title, b.get('link') or '', b.get('kind') or 'auto', save_to)
    _journal_log('auto_queued', title, {'selected': b, 'pkg_id': pid, 'forced': force})
    return jsonify({'ok':True,'queued_id': pid, 'selected': b})

@want_bp.route('/api/wanted/resolve_batch', methods=['POST'])
def resolve_batch():
    js=request.get_json(silent=True) or {}
    mode=(js.get('mode') or 'remove').lower() # remove | force_queue
    data=_load(WANT, {'items':[]})
    arr=data.get('items',[])
    kept=[]
    removed=0; forced=0
    for it in arr:
        t=(it.get('title') or '').strip()
        inlib=_in_lib(t); inq=_in_queue(t)
        if inlib or inq:
            if mode=='force_queue' and not inq:
                # try auto-queue
                try:
                    from routes.auto_select import _pool, _load as _aload, RULES, _queue_pkg
                    rules=_aload(RULES, {}); pool=_pool(t, rules)
                    if pool:
                        b=pool[0]; _queue_pkg(b.get('title') or t, b.get('link') or '', b.get('kind') or 'auto', ''); forced+=1
                    else:
                        kept.append(it)
                except Exception:
                    kept.append(it)
            else:
                removed+=1 # remove conflicted from wanted
        else:
            kept.append(it)
    data['items']=kept
    _save(WANT, data)
    return jsonify({'ok':True,'removed': removed, 'forced': forced})

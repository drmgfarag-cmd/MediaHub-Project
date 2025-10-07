from flask import Blueprint, jsonify, request
import os, json, re, time

sr_bp = Blueprint('smart', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
LIB=os.path.join(STO,'library_index.json')
RCFG=os.path.join(STO,'smart_rails_config.json')
RCACHE=os.path.join(STO,'smart_rails_cache.json')
DEBOUNCE_FILE=os.path.join(STO,'smart_rails.last')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
        except Exception: return {}

def _conf():
        try: return json.load(open(RCFG,'r',encoding='utf-8'))
        except Exception: return {'enabled_rails':{}, 'min_items': 6, 'tokens':{}}

def _items():
        try: return json.load(open(LIB,'r',encoding='utf-8'))
        except Exception: return []

def _cache():
        try: return json.load(open(RCACHE,'r',encoding='utf-8'))
        except Exception: return {'last_run':0,'rails':{}}

def _save_cache(obj):
    tmp=RCACHE+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, RCACHE)

def _tok_in(tokens, s):
    s=s or ''
    for t in tokens:
        if t.lower() in s.lower(): return True
        return False

def _is_ext(path, exts):
    lx=os.path.splitext(path or '')[1].lower().lstrip('.')
        return lx in [e.lower() for e in exts]

def _year_decade(y):
    try:
        y=int(y); return f"{(y//10)*10}s"
    except Exception:
        return ''

def _enabled(name, conf):
        return bool(conf.get('enabled_rails',{}).get(name, False))

def _mk_item(it):
        return {'title': it.get('title') or os.path.basename(it.get('path') or ''), 'type': it.get('type',''), 'year': it.get('year') or None, 'path': it.get('path') or ''}

def _compute():
    conf=_conf()
    items=_items()
    rails={}
    tok=conf.get('tokens',{})
    min_items=int(conf.get('min_items',6))

    # Helpers
    def add(name, pred):
        if not _enabled(name, conf): return
        arr=[_mk_item(it) for it in items if pred(it)]
        if len(arr)>=min_items: rails[name]=arr[:200]

    # Movies family
    add('movies_4k_hdr', lambda it: it.get('type')=='movie' and (_tok_in(tok.get('4k',[]), it.get('path','')+it.get('title','')) and _tok_in(tok.get('hdr',[]), it.get('path','')+it.get('title',''))))
    add('movies_dolby_vision', lambda it: it.get('type')=='movie' and _tok_in(tok.get('dv',[]), it.get('path','')+it.get('title','')))
    add('movies_atmos', lambda it: it.get('type')=='movie' and _tok_in(tok.get('atmos',[]), it.get('path','')+it.get('title','')))
    if _enabled('movies_by_genre', conf):
        # group by genre -> flatten into separate rails "movies_genre_Action" ...
        seen=set()
        for it in items:
            if it.get('type')!='movie': continue
            gs=[g for g in (it.get('genres') or []) if g]
            for g in gs:
                key=f"movies_genre_{g}"
                seen.add(key); rails.setdefault(key, []).append(_mk_item(it))
        # prune small ones
        for k in list(rails.keys()):
            if k.startswith('movies_genre_') and len(rails[k])<min_items:
                rails.pop(k, None)
    if _enabled('movies_by_decade', conf):
        buckets={}
        for it in items:
            if it.get('type')!='movie': continue
            dec=_year_decade(it.get('year'))
            if dec: buckets.setdefault(dec, []).append(_mk_item(it))
        for dec, arr in buckets.items():
            if len(arr)>=min_items:
                rails[f"movies_decade_{dec}"]=arr[:200]

    # TV
    add('tv_ongoing', lambda it: it.get('type') in ('episode','series') and int(it.get('added_ts') or 0) >= int(time.time())-90*24*3600)
    # naive series episode counting
    if _enabled('tv_miniseries', conf) or _enabled('tv_anthology', conf):
        per_series={}
        for it in items:
            if it.get('type')=='episode':
                ser=it.get('series') or re.sub(r'[ ._]S\d{1,2}.*','', (it.get('title') or ''), flags=re.I)
                per_series.setdefault(ser, 0); per_series[ser]+=1
        if _enabled('tv_miniseries', conf):
            sels=[s for s,c in per_series.items() if c<=8 and s]
            rails['tv_miniseries']=[_mk_item(it) for it in items if (it.get('series') or it.get('title','')).split()[0:2] and (it.get('series') in sels or (it.get('title') or '').startswith(tuple(sels)))][:200]
        if _enabled('tv_anthology', conf):
            rails['tv_anthology']=[_mk_item(it) for it in items if it.get('type')=='series' and re.search(r'anthology', (it.get('title') or it.get('path','')), re.I)]

    # Books
    add('books_ebooks', lambda it: it.get('type') in ('ebook',) or os.path.splitext(it.get('path',''))[1].lower() in ('.epub','.pdf'))
    add('books_comics', lambda it: it.get('type') in ('comic',) or os.path.splitext(it.get('path',''))[1].lower() in ('.cbz','.cbr') and ('manga' not in (it.get('path','').lower())))
    add('books_manga', lambda it: 'manga' in (it.get('path','').lower()) or (os.path.splitext(it.get('path',''))[1].lower() in ('.cbz','.cbr') and 'manga' in (it.get('path','').lower())))
    add('books_audiobooks', lambda it: it.get('type')=='audiobook' or (os.path.splitext(it.get('path',''))[1].lower() in ('.m4b','.mp3') and 'audiobook' in (it.get('path','').lower())))

    # Audio
    add('audio_lossless', lambda it: it.get('type') in ('audio','music') and (os.path.splitext(it.get('path',''))[1].lower().lstrip('.') in [e.lower() for e in tok.get('lossless_ext',[])]))
    add('audio_hires', lambda it: it.get('type') in ('audio','music') and ('96k' in (it.get('path','').lower()) or '192k' in (it.get('path','').lower())))
    add('audio_atmos', lambda it: it.get('type') in ('audio','music') and _tok_in(tok.get('atmos',[]), it.get('path','')+it.get('title','')))
    add('audio_live', lambda it: it.get('type') in ('audio','music') and _tok_in(tok.get('live_audio',[]), it.get('path','')+it.get('title','')))
    add('audio_soundtracks', lambda it: it.get('type') in ('audio','music') and _tok_in(tok.get('soundtrack',[]), it.get('path','')+it.get('title','')))

    # Kids overlay
    if _enabled('kids_overlay', conf):
        rails['kids_movies']=[_mk_item(it) for it in items if (it.get('type')=='movie' and ('kids' in (it.get('path','').lower()) or _tok_in(['Animation','Animated'], it.get('title','')+it.get('path',''))))][:200]
        rails['kids_tv']=[_mk_item(it) for it in items if (it.get('type') in ('series','episode') and ('kids' in (it.get('path','').lower()) or _tok_in(['Animation','Animated'], it.get('title','')+it.get('path',''))))][:200]
        rails['kids_books']=[_mk_item(it) for it in items if (it.get('type') in ('ebook','comic','manga') and ('kids' in (it.get('path','').lower())))][:200]
        rails['kids_audio']=[_mk_item(it) for it in items if (it.get('type') in ('audiobook','audio') and ('kids' in (it.get('path','').lower())))][:200]

    # Others
    add('documentaries', lambda it: _tok_in(['Documentary','Docs','Docu'], it.get('title','')+it.get('path','')) or ('documentary' in [g.lower() for g in (it.get('genres') or [])]))
    add('standup', lambda it: _tok_in(['Standup','Stand-up','Comedy.Special','Special'], it.get('title','')+it.get('path','')))

    cache=_cache(); cache['rails']=rails; cache['last_run']=int(time.time())
    _save_cache(cache)
    open(DEBOUNCE_FILE,'w',encoding='utf-8').write(str(cache['last_run']))
    return cache

def _debounced_allowed():
    c=_cfg().get('smart_rails',{}); db=int(c.get('debounce_sec',10))
    try:
        ts=int(open(DEBOUNCE_FILE,'r',encoding='utf-8').read().strip())
    except Exception:
        ts=0
        return (time.time()-ts) >= db

@sr_bp.route('/api/smart_rails/state')
def state():
    try:
        cache=_cache()
        rails=[{'name':k,'count':len(v)} for k,v in cache.get('rails',{}).items()]
        return jsonify({'last_run': cache.get('last_run',0), 'rails': rails})

        @sr_bp.route('/api/smart_rails/get')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_rail():
    try:
        name=(request.args.get('name') or '').strip()
        cache=_cache()
        return jsonify({'name':name, 'items': cache.get('rails',{}).get(name, [])})

        @sr_bp.route('/api/smart_rails/refresh', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def refresh():
    js=request.get_json(silent=True) or {}
    mode=(js.get('mode') or 'background').lower()
    if mode=='sync':
        if not _debounced_allowed():
        return jsonify({'skipped':'debounced'})
        res=_compute(); return jsonify({'ok':True,'last_run': res.get('last_run')})
    # background via jobs, if available
    try:
        from .jobs import _q  # type: ignore
        _q.put({'id':'smart_'+str(int(time.time()*1000)), 'type':'smart_rails_refresh', 'args':{}, 'status':'queued', 'created': time.time()})
        return jsonify({'ok':True,'queued':True})
    except Exception:
        # fallback to sync
        res=_compute(); return jsonify({'ok':True,'last_run': res.get('last_run'), 'note':'no jobs; ran sync'})
        
@sr_bp.route('/api/smart_rails/config_get')
def cfg_get():
    try:
        return jsonify(_conf())

        @sr_bp.route('/api/smart_rails/config_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def cfg_set():
    try:
        js=request.get_json(silent=True) or {}
        tmp=RCFG+'.tmp'; json.dump(js, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, RCFG)
        return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

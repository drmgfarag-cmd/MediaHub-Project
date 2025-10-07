from flask import Blueprint, jsonify, request
import os, json, re, time

disc_bp = Blueprint('disc', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
IDX=os.path.join(STO,'library_index.json')
CFG=os.path.join(STO,'discovery_config.json')

LANG_TOKENS={'AR':['arabic','ar-','[ar]'],'EN':['english','en-','[en]'],'FR':['french','fr-','[fr]'],'ES':['spanish','es-','[es]'],'DE':['german','de-','[de]'],'IT':['italian','it-','[it]'],'JA':['japanese','ja-','[ja]','jpn'],'KO':['korean','ko-','[ko]','kor'],'ZH':['chinese','zh-','[zh]','chs','cht']}
FMT_TOKENS={'DV':['dolby vision','\.dv','dovi','dolby.vision'],'HDR':['hdr10','hdr\b'],'4K':['2160p','\b4k\b','\buhd\b'],'Atmos':['atmos','eac3\.atmos','truehd\.atmos'],'Lossless':['flac','alac','wav','ape']}
AWARD_TOKENS={'Oscar':['oscar','academy award'],'GoldenGlobe':['golden globe'],'BAFTA':['bafta'],'Cannes':['cannes'],'Venice':['venice film festival','venice'],'Berlinale':['berlin international','berlinale']}

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default

def _items():
        return _load(IDX, [])

def _cfg():
        return _load(CFG, {'enabled': False, 'rails':{}, 'badges':{}})

def _has_token(s, patterns):
        if not s: return False
    sl=s.lower()
    for p in patterns:
        if re.search(p, sl, re.I): return True
        return False

def _guess_lang(it):
    # priority: meta.lang, else path/title tokens
    lang=(it.get('meta',{}) or {}).get('lang') or (it.get('lang') or '')
        if lang: return lang.upper()[:2]
    txt=(it.get('path','')+' '+(it.get('title') or '')).lower()
    for code, toks in LANG_TOKENS.items():
        for t in toks:
            if t in txt: return code
    return 'EN'  # default

def _runtime_bucket(it):
    rt=it.get('runtime') or 0
    if not rt and it.get('meta'): rt=int((it['meta'].get('runtime_min') or 0))
    if not rt: return None
    if rt<=90: return '<=90'
    if 90<rt<=120: return '90-120'
    return '>120'

def _fmt_badges(it):
    txt=(it.get('path','')+' '+(it.get('title') or '')+' '+(' '.join(it.get('badges') or []))).lower()
    out=[]
    for k, pats in FMT_TOKENS.items():
        if _has_token(txt, pats): out.append(k)
    return out

def _award_badges(it):
    txt=(it.get('path','')+' '+(it.get('title') or '')).lower()
    out=[]
    for k, pats in AWARD_TOKENS.items():
        if _has_token(txt, pats): out.append(k)
    return out

@disc_bp.route('/api/discovery/config')
def get_cfg():
    try:
        return jsonify(_cfg())

        @disc_bp.route('/api/discovery/config_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def set_cfg():
    try:
        js=request.get_json(silent=True) or {}
        tmp=CFG+'.tmp'; json.dump(js, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, CFG)
        return jsonify({'ok':True})


        @disc_bp.route('/api/discovery/rails')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rails():
    try:
        c=_cfg()
        if not c.get('enabled'): return jsonify({'rails':[]})
        items=_items()
        rails=[]
        # Language rails
        if c['rails'].get('language',{}).get('enabled'):
        mins=c['rails']['language'].get('min_items',6)
        langs=c['rails']['language'].get('langs',[])
        buckets={k:[] for k in langs}
        for it in items:
        if it.get('type') not in ('movie','series','ebook','comic','manga','audiobook','audio'): continue
        lg=_guess_lang(it)
        if lg in buckets: buckets[lg].append(it)
        for code, arr in buckets.items():
        if len(arr)>=mins: rails.append({'name': f'By Language — {code}', 'key': f'lang_{code}', 'items': arr[:36]})
        # Runtime rails (movies only)
        if c['rails'].get('runtime',{}).get('enabled'):
        mins=c['rails']['runtime'].get('min_items',6)
        buckets={'<=90':[], '90-120':[], '>120':[]}
        for it in items:
        if it.get('type')!='movie': continue
        b=_runtime_bucket(it)
        if b and b in buckets: buckets[b].append(it)
        for k, arr in buckets.items():
        if len(arr)>=mins: rails.append({'name': f'Runtime — {k} min', 'key': f'rt_{k}', 'items': arr[:36]})
        # Remasters/4K
        if c['rails'].get('remasters',{}).get('enabled'):
        toks=c['rails']['remasters'].get('tokens',[]); mins=c['rails']['remasters'].get('min_items',4)
        rem=[]
        for it in items:
        txt=(it.get('path','')+' '+(it.get('title') or '')).lower()
        if any(t.lower() in txt for t in toks): rem.append(it)
        if len(rem)>=mins: rails.append({'name':'Remasters / 4K Upgrades', 'key':'remasters', 'items': rem[:36]})
        # Extras/Featurettes
        if c['rails'].get('extras',{}).get('enabled'):
        toks=c['rails']['extras'].get('tokens',[]); mins=c['rails']['extras'].get('min_items',4)
        ex=[]
        for it in items:
        txt=(it.get('path','')+' '+(it.get('title') or '')).lower()
        if any(t.lower() in txt for t in toks): ex.append(it)
        if len(ex)>=mins: rails.append({'name':'Behind the Scenes / Extras', 'key':'extras', 'items': ex[:36]})
        # Attach badges if enabled
        if c.get('badges',{}).get('format') or c.get('badges',{}).get('awards'):
        for r in rails:
        for it in r['items']:
        b=(it.get('badges') or [])[:]
        if c['badges'].get('format'): b += _fmt_badges(it)
        if c['badges'].get('awards'): b += _award_badges(it)
        it.setdefault('ui',{})['badges']=sorted(list({x for x in b if x}))
        return jsonify({'rails': rails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import Blueprint, jsonify, request
import os, json, re, fnmatch, time, shutil

br_bp = Blueprint('br', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
SAFE_DIRS=[os.path.join(ROOT,'storage'), os.path.join(ROOT,'downloads')]
UNDO=os.path.join(ROOT,'storage','batchrename_undo.json')

TOKENS={'title':'title','year':'year','ext':'ext','season':'season','episode':'episode','series':'series'}

def _safe(p):
    p=os.path.abspath(p)
    for base in SAFE_DIRS:
        if p.startswith(base): return p
    raise ValueError('Path not allowed')

def _collect(paths, include_globs, exclude_globs):
    out=[]
    todo=paths or SAFE_DIRS
    for base in todo:
        base=_safe(base)
        if os.path.isdir(base):
            for root, dirs, files in os.walk(base):
                for f in files:
                    fp=os.path.join(root,f); out.append(fp)
        else:
            out.append(base)
    if include_globs:
        out=[p for p in out if any(fnmatch.fnmatch(p,g) for g in include_globs)]
    if exclude_globs:
        out=[p for p in out if not any(fnmatch.fnmatch(p,g) for g in exclude_globs)]
    return sorted(list(set(out)))

def _tokenize(name, path):
    # naive extraction for tokens based on filename
    base=os.path.basename(path)
    stem, ext=os.path.splitext(base)
    m=re.search(r'\b(S(\d{1,2}))?E(\d{1,3})\b', stem, re.I)
    season = (m.group(2) if m and m.group(2) else '') if m else ''
    episode= (m.group(3) if m and m.group(3) else '') if m else ''
    # try title-year pattern
    t=stem
    y=''
    m2=re.search(r'\(?(19\d{2}|20\d{2})\)?', stem)
    if m2: y=m2.group(1); t=stem.replace(m2.group(0),'').replace('.',' ').replace('_',' ').strip()
    return {'title': t, 'year': y, 'ext': ext.lstrip('.'), 'season': season, 'episode': episode, 'series': name}

def _apply_rule(token_map, fmt):
    out=fmt
    for k,v in token_map.items():
        out=out.replace('{'+k+'}', v or '')
    return out

@br_bp.route('/api/rename/preview', methods=['POST'])
def preview():
    js=request.get_json(silent=True) or {}
    fmt=(js.get('format') or '{title}.{year}.{ext}').strip()
    paths=js.get('paths') or []   # explicit starting paths (optional)
    inc=js.get('include') or []
    exc=js.get('exclude') or []
    res=[]
    files=_collect(paths, inc, exc)
    for p in files:
        try:
            dir=os.path.dirname(p)
            toks=_tokenize('', p)
            new=_apply_rule(toks, fmt)
            if not new: continue
            target=os.path.join(dir, new)
            if target==p: continue
            res.append({'from':p,'to':target})
        except Exception:
            pass
    return jsonify({'ok':True,'plans':res})

@br_bp.route('/api/rename/apply', methods=['POST'])
def apply():
    js=request.get_json(silent=True) or {}
    plans=js.get('plans') or []
    dry=bool(js.get('dry'))
    undo={'ts': time.time(), 'ops': []}; moved=0
    for pl in plans:
        src=pl.get('from'); dst=pl.get('to')
        if not src or not dst: continue
        try:
            s=_safe(src); d=_safe(os.path.dirname(dst))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not dry:
                os.rename(s, dst)
            undo['ops'].append({'from':s,'to':dst})
            moved+=1
        except Exception:
            pass
    if not dry:
        json.dump(undo, open(UNDO,'w',encoding='utf-8'), indent=2)
    return jsonify({'ok':True,'moved':moved,'undo_log': UNDO if not dry else ''})

@br_bp.route('/api/rename/undo', methods=['POST'])
def undo():
    try:
        u=json.load(open(UNDO,'r',encoding='utf-8'))
    except Exception:
        return jsonify({'error':'no undo log'}), 400
    restored=0
    for op in reversed(u.get('ops',[])):   # reverse order
        try:
            if os.path.exists(op['to']):
                os.rename(op['to'], op['from'])
                restored+=1
        except Exception:
            pass
    return jsonify({'ok':True,'restored':restored})

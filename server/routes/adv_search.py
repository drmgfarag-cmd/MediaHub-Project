from flask import Blueprint, jsonify, request
import os, json, re, fnmatch

adv_bp = Blueprint('adv', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
IDX=os.path.join(STO,'library_index.json')

def _items():
    try: return json.load(open(IDX,'r',encoding='utf-8'))
    except Exception: return []

def _parse(q):
    # syntax: key:val, key>=n, key<=n, text tokens (in title/path)
    toks=[]; buf=''; inq=False
    for ch in q:
        if ch=='"': inq=not inq; buf+=ch
        elif ch==' ' and not inq:
            if buf.strip(): toks.append(buf.strip()); buf=''
        else: buf+=ch
    if buf.strip(): toks.append(buf.strip())
    conds={'free':[],'kv':[]}
    for t in toks:
        m=re.match(r'^(\w+)(<=|>=|=|:)(.+)$', t)
        if m:
            k,op,v=m.groups(); v=v.strip().strip('"')
            conds['kv'].append((k.lower(),op,v))
        else:
            conds['free'].append(t.lower())
    return conds

def _match(it, conds):
    # free tokens in title or path
    for tok in conds['free']:
        if tok not in (it.get('title','')+' '+it.get('path','')).lower():
            return False
    for k,op,v in conds['kv']:
        if k in ('type','genre','genres'):
            gs=[g.lower() for g in (it.get('genres') or [])]
            if k=='type':
                if (it.get('type','').lower()!=v.lower()): return False
            else:
                if v.lower() not in gs: return False
        elif k=='year':
            y=int(it.get('year') or 0)
            vv=int(v) if v.isdigit() else 0
            if op=='>=' and not (y>=vv): return False
            if op=='<=' and not (y<=vv): return False
            if op in (':','=') and not (y==vv): return False
        elif k=='path_re':
            if not re.search(v, it.get('path',''), re.I): return False
        elif k=='lang':
            lg=(it.get('meta',{}) or {}).get('lang') or it.get('lang') or ''
            if lg.upper()[:2] != v.upper()[:2]: return False
        else:
            # generic contains on title/path/meta
            s=(str((it.get(k) or (it.get('meta',{}) or {}).get(k) or ''))).lower()
            if v.lower() not in s: return False
    return True

@adv_bp.route('/api/search/advanced')
def search():
    q=(request.args.get('q') or '').strip()
    n=int(request.args.get('n') or 100)
    if not q: return jsonify({'items':[]})
    conds=_parse(q)
    items=_items()
    out=[it for it in items if _match(it, conds)]
    return jsonify({'q':q,'count':len(out),'items': out[:max(1,min(1000,n))]})

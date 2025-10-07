from flask import Blueprint, jsonify, request
import os, json, re, fnmatch, time, shutil

fr_bp = Blueprint('findrep', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
SAFE_DIRS=[os.path.join(ROOT,'storage'), os.path.join(ROOT,'downloads')]
UNDO=os.path.join(ROOT,'storage','findreplace_undo.json')
TEXT_EXTS={'.txt','.srt','.sub','.nfo','.md','.markdown','.json','.yaml','.yml','.xml','.ini','.cfg','.log','.py','.js','.css','.html','.ts','.tsx','.csv'}

def _safe(p):
    p=os.path.abspath(p)
    for base in SAFE_DIRS:
        if p.startswith(base): return p
    raise ValueError('Path not allowed')

def _walk(include_globs, exclude_globs):
    # walk allowed dirs
    out=[]
    for base in SAFE_DIRS:
        for root, dirs, files in os.walk(base):
            for f in files:
                fp=os.path.join(root,f)
                ok=True
                if include_globs:
                    ok=any(fnmatch.fnmatch(fp, g) for g in include_globs)
                if ok and exclude_globs:
                    if any(fnmatch.fnmatch(fp, g) for g in exclude_globs):
                        ok=False
                if not ok: continue
                if os.path.splitext(fp)[1].lower() in TEXT_EXTS:
                    out.append(fp)
    return out

@fr_bp.route('/api/findreplace/preview', methods=['POST'])
def preview():
    js=request.get_json(silent=True) or {}
    find=js.get('find',''); repl=js.get('replace',''); flags=js.get('flags',{})
    inc=js.get('include',[]); exc=js.get('exclude',[])
    regex=bool(flags.get('regex')); ic=bool(flags.get('ignore_case')); ww=bool(flags.get('whole_word'))
    if not find: return jsonify({'error':'find required'}), 400
    files=_walk(inc, exc)
    changes=[]; total=0
    pat=find
    if regex:
        fl=re.MULTILINE|re.DOTALL
        if ic: fl|=re.IGNORECASE
        if ww: pat=r'\b(?:' + pat + r')\b'
        rx=re.compile(pat, fl)
    else:
        if ww: pat=f"\b{re.escape(find)}\b"
        else:  pat=re.escape(find)
        fl=re.IGNORECASE if ic else 0
        rx=re.compile(pat, fl)
    for fp in files:
        try:
            data=open(fp,'r',encoding='utf-8',errors='ignore').read()
            new, cnt = rx.subn(repl, data)
            if cnt>0:
                changes.append({'path':fp,'count':cnt})
                total+=cnt
        except Exception:
            pass
            return jsonify({'ok':True,'total':total,'files':changes})


@fr_bp.route('/api/findreplace/apply', methods=['POST'])
def apply():
    js=request.get_json(silent=True) or {}
    find=js.get('find',''); repl=js.get('replace',''); flags=js.get('flags',{})
    inc=js.get('include',[]); exc=js.get('exclude',[])
    dry=bool(js.get('dry'))
            if not find: return jsonify({'error':'find required'}), 400
    # reuse preview to compute matches + write changes
    prev=preview().json
    if not prev.get('ok'): return jsonify(prev), 400
    # compile pattern
    regex=bool(flags.get('regex')); ic=bool(flags.get('ignore_case')); ww=bool(flags.get('whole_word'))
    pat=find
    if regex:
        fl=re.MULTILINE|re.DOTALL
        if ic: fl|=re.IGNORECASE
        if ww: pat=r'\b(?:' + pat + r')\b'
        rx=re.compile(pat, fl)
    else:
        if ww: pat=f"\b{re.escape(find)}\b"
        else:  pat=re.escape(find)
        fl=re.IGNORECASE if ic else 0
        rx=re.compile(pat, fl)
    undo={'ts': time.time(), 'ops': []}
    applied=0
    for ent in prev.get('files',[]):
        fp=ent['path']
        try:
            p=_safe(fp)
            data=open(p,'r',encoding='utf-8',errors='ignore').read()
            new = rx.sub(repl, data)
            if not dry:
                open(p+'.bak','w',encoding='utf-8').write(data)
                open(p,'w',encoding='utf-8').write(new)
            undo['ops'].append({'path':p, 'backup': p+'.bak'})
            applied+=1
        except Exception:
            pass
    if not dry:
        json.dump(undo, open(UNDO,'w',encoding='utf-8'), indent=2)
            return jsonify({'ok':True,'applied_files':applied,'total_replacements': prev.get('total',0),'undo_log': UNDO if not dry else ''})

@fr_bp.route('/api/findreplace/undo', methods=['POST'])
def undo():
    try:
        u=json.load(open(UNDO,'r',encoding='utf-8'))
    except Exception:
        return jsonify({'error':'no undo log'}), 400
    restored=0
    for op in u.get('ops',[]):
        b=op.get('backup'); p=op.get('path')
        if b and p and os.path.exists(b):
            try:
                os.replace(b, p)
                restored+=1
            except Exception:
                pass
                return jsonify({'ok':True,'restored_files':restored})

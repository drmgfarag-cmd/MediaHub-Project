from flask import Blueprint, jsonify, request
import os, json, re, hashlib
dd_bp = Blueprint('dd', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
DQ =os.path.join(STO,'downloader_queue.json')
RDL=os.path.join(STO,'rd_links.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

TOKS=re.compile(r'(?i)\\b(2160p|UHD|4K|1080p|HDR|DV|Dolby\\.Vision|DoVi|Atmos|TrueHD|EAC3|FLAC)\\b')
def _norm(t):
    t=re.sub(r'[._]+',' ',t)
    t=re.sub(r'\\bS\\d{1,2}E\\d{1,2}\\b','',t, flags=re.I)
    t=re.sub(TOKS,'',t)
    t=re.sub(r'\\s+',' ',t).strip().lower()
        return t

@dd_bp.route('/api/dedupe/downloader', methods=['POST'])
def dd_dl():
    try:
        js=request.get_json(silent=True) or {}
        mode=(js.get('mode') or 'mark').lower() # mark|remove
        q=_load(DQ, {'packages':[]})
        seen=set(); keep=[]; removed=0
        for p in q.get('packages',[]):
        k=_norm(p.get('name') or '')
        if k in seen:
        removed+=1
        if mode=='mark':
        p['status']='Duplicate'
        keep.append(p)
        # else drop
        else:
        seen.add(k); keep.append(p)
        q['packages']=keep; _save(DQ, q)
        return jsonify({'ok':True,'removed': removed, 'kept': len(keep)})

        @dd_bp.route('/api/dedupe/rd', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def dd_rd():
    try:
        js=request.get_json(silent=True) or {}
        mode=(js.get('mode') or 'collapse').lower() # collapse|remove_smaller
        db=_load(RDL, {'links':[]}); out=[]; groups={}
        for ln in db.get('links',[]):
        k=_norm(ln.get('title') or '')
        groups.setdefault(k, []).append(ln)
        removed=0
        for k,arr in groups.items():
        if mode=='collapse':
        # keep all but this is already grouped in UI; just report counts
        out.extend(arr)
        else:
        arr.sort(key=lambda x:x.get('size_mb',0), reverse=True)
        out.append(arr[0]); removed+=max(0, len(arr)-1)
        db['links']=out; _save(RDL, db)
        return jsonify({'ok':True,'removed': removed, 'total': len(out)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

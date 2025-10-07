from flask import Blueprint, jsonify, request
import os, json, re, time, hashlib, shutil, pathlib, base64

hooks_bp = Blueprint('hooks', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'completion_hooks.json')
QF=os.path.join(STO,'downloader_queue.json')
LIB=os.path.join(STO,'library_index.json')
JNL=os.path.join(STO,'wanted_journal.json')
WANT=os.path.join(STO,'wanted.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default

def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

TOKS_QUALITY = re.compile(r'(?i)\\b(2160p|1080p|720p|UHD|4K|HDR10|HDR|DV|DoVi|Dolby\\.Vision|Atmos|TrueHD|DTS(?:-?HD)?|EAC3|DDP)\\b')
SXXEYY = re.compile(r'(?i)\\bS(\\d{1,2})E(\\d{1,2})\\b')
YEAR = re.compile(r'\\b(19\\d{2}|20\\d{2})\\b')

def _infer_kind_and_meta(name):
    n=name or ''
    low=n.lower()
    ext=os.path.splitext(low)[1]
    if ext in ['.mkv','.mp4','.avi','.mov']:
        # try TV first
        m=SXXEYY.search(n)
        if m:
        return 'series', {'Season': m.group(1).zfill(2), 'Episode': m.group(2).zfill(2)}
        return 'movie', {}
    if ext in ['.epub','.pdf','.mobi','.azw3','.cbz','.cbr']:
        # comics/manga treated as book family
        return 'book', {}
    if ext in ['.flac','.alac','.m4a','.mp3','.wav']:
        return 'audio', {}
    # fallback
    return 'movie', {}

def _title_from_name(name):
    # strip common tokens
    base=os.path.splitext(os.path.basename(name))[0]
    t=re.sub(r'(?i)[._]+',' ', base)
    t=re.sub(SXXEYY, '', t)
    t=re.sub(TOKS_QUALITY, '', t)
    t=re.sub(r'\\b(\\d{3,4}p|x264|x265|hevc|h\\.?264|h\\.?265|web-?dl|bluray|webrip|remux|ddp5\\.?1|dd5\\.?1|aac|dts)\\b','',t, flags=re.I)
    t=re.sub(r'\\s+',' ', t).strip()
    return t

def _year_from_name(name):
    m=YEAR.search(name)
    return m.group(1) if m else ''

def _quality_from_name(name):
    m=TOKS_QUALITY.search(name)
    return m.group(1) if m else ''

def _ensure_file(path):
    # create an empty file if missing (offline demo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        open(path, 'wb').close()

def _add_artwork(dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    poster=os.path.join(dest_dir, 'poster.jpg')
    if not os.path.exists(poster):
        # tiny 1x1 JPEG
        data=base64.b64decode('/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxISEhISEhIVFRUVFRUVFRUVFRUVFRUVFhUVFRUYHSggGBolHRUVITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OGxAQGi0lHyUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBIgACEQEDEQH/xAAXAAEBAQEAAAAAAAAAAAAAAAAAAQID/8QAFhABAQEAAAAAAAAAAAAAAAAAABIB/8QAFQEBAQAAAAAAAAAAAAAAAAAAAgP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAAAAAAAAAAAAAAAAAAAAAAB//2Q==')
        open(poster,'wb').write(data)

def _journal(kind, title, meta=None):
    j=_load(JNL, {'events':[]})
    j['events'].append({'ts': int(time.time()), 'kind': kind, 'title': title, 'meta': meta or {}})
    _save(JNL, j)

def _append_library(item):
    lib=_load(LIB, [])
    lib.append(item)
    _save(LIB, lib)

def _match_wanted(title):
    w=_load(WANT, {'items':[]}).get('items',[])
    tl=title.strip().lower()
    return any((i.get('title','').strip().lower()==tl) for i in w)

def _format_rename(kind, meta, cfg):
    rn=cfg.get('rename',{}).get(kind,'{Title}/{Title}.mkv')
    # safe defaults
    m=dict(meta)
    for k in ['Title','Year','Quality','Season','Episode','Artist','Album','Track','Author','Series']:
        m.setdefault(k,'')
    # zero-pad numbers
    if isinstance(m.get('Track'), int):
        m['Track'] = f"{m['Track']:02d}"
    return rn.format(**m)

def _dest_root(kind, cfg):
    d=cfg.get('dest',{}).get(kind) or 'Library/Other'
    return os.path.join(ROOT, d)

def _run_for_package(pkg_id):
    cfg=_load(CFG, {})
    if not cfg.get('enabled', True):
        return {'skipped': True, 'reason': 'disabled'}
    dat=_load(QF, {'packages':[]})
    pk=next((p for p in dat.get('packages',[]) if p.get('id')==pkg_id), None)
    if not pk:
        return {'error':'package not found'}
    # use first file name as source token
    files=pk.get('files') or []
    fname=files[0].get('name') if files else pk.get('name') or 'file.mkv'
    title=_title_from_name(fname)
    year=_year_from_name(fname)
    quality=_quality_from_name(fname)
    kind, inferred = _infer_kind_and_meta(fname)
    meta={'Title': title, 'Year': year, 'Quality': quality}
    meta.update(inferred)
    rel=_format_rename(kind, meta, cfg)
    dest=os.path.join(_dest_root(kind, cfg), rel)
    # create placeholder file and artwork
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    _ensure_file(dest)
    if cfg.get('artwork',{}).get('enabled'):
        _add_artwork(os.path.dirname(dest))
    # rescan: append to library
    item={'title': title, 'path': dest, 'type': kind, 'year': year, 'added_ts': int(time.time())}
    _append_library(item)
    # journal: obtained if was wanted
    if _match_wanted(title):
        _journal('obtained', title, {'pkg_id': pkg_id, 'path': dest})
    return {'ok': True, 'dest': dest, 'kind': kind, 'title': title}

@hooks_bp.route('/api/hooks/config_get')
def cfg_get():
    try:
        return jsonify(_load(CFG, {}))

        @hooks_bp.route('/api/hooks/config_set', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def cfg_set():
    try:
        js=request.get_json(silent=True) or {}
        cur=_load(CFG, {}); cur.update(js); _save(CFG, cur); return jsonify({'ok':True})

        @hooks_bp.route('/api/hooks/run_for_package', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def run_for_pkg():
    try:
        js=request.get_json(silent=True) or {}
        pid=(js.get('id') or '').strip()
        if not pid: return jsonify({'error':'id required'}), 400
        res=_run_for_package(pid)
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

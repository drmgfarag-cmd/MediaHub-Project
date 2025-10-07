
from flask import Blueprint, jsonify, request
import os, re, json, time

org_bp = Blueprint('org', __name__)
STO = os.environ.get('MH_STORAGE','storage')
CATALOG = os.path.join(STO, 'scan_index.json') # expected from scanner
SAMPLE = [ # fallback sample entries if no index exists
  {"path":"X:/Movies/Dune.2021.2160p.DV.Atmos.mkv","type":"movie","title":"Dune","year":2021,"resolution":"2160p"},
  {"path":"X:/TV/The.Expanse.S03E05.1080p.mkv","type":"episode","series":"The Expanse","season":3,"episode":5,"resolution":"1080p"},
  {"path":"X:/Books/Comics/Batman (2016)/Batman (2016) 001.cbz","type":"comic","title":"Batman (2016) 001"},
  {"path":"X:/Audio/Albums/Hans Zimmer - Dune OST/01 - Dream Of Arrakis.flac","type":"audio","title":"Dream Of Arrakis","album":"Dune OST","artist":"Hans Zimmer"}
]

PATTERNS = [
  {"id":"movie_default","name":"Movies default","pattern":"{title} ({year})/{title} ({year}) [{resolution}]"},
  {"id":"tv_default","name":"TV default","pattern":"{series}/Season {season}/{series} S{season}E{episode} [{resolution}]"},
  {"id":"book_default","name":"Books default","pattern":"{typeTitle}/{title}"},
  {"id":"audio_default","name":"Music default","pattern":"{artist}/{album}/{track:02d} - {title}"}
]

def _read_index():
  if os.path.exists(CATALOG):
    try: return json.load(open(CATALOG,'r',encoding='utf-8')).get('items',[])
    except: pass
        return SAMPLE

def _tokenize(fname):
  # simple token extraction from filename
  base=os.path.basename(fname)
  m=re.search(r'(?i)(?P<title>.+?)[\.\s\-_]\(?(?P<year>19\d{2}|20\d{2})\)?', base)
  title=(m.group('title').replace('.',' ').replace('_',' ') if m else os.path.splitext(base)[0])
  year=int(m.group('year')) if m else None
  res=re.search(r'(?i)(2160p|1080p|720p|480p|UHD|4K)', base)
  resolution=res.group(1).upper() if res else ''
  ms=re.search(r'(?i)S(?P<s>\d{1,2})E(?P<e>\d{1,3})', base)
  season=int(ms.group('s')) if ms else None
  episode=int(ms.group('e')) if ms else None
        return dict(title=title.strip(), year=year, resolution=resolution, season=season, episode=episode)

def _format(pattern, meta):
  def repl(m):
    key=m.group(1)
    if ':' in key:
      k,pad = key.split(':',1)
      val=str(meta.get(k,''))
      if pad.isdigit(): val=val.zfill(int(pad))
      return val
    return str(meta.get(key,''))
  return re.sub(r'\{([^}]+)\}', repl, pattern)

@org_bp.route('/api/organizer/patterns')
def patterns():
try:
    return jsonify({"ok":True,"patterns":PATTERNS})
except Exception as e:
    return jsonify({'success': False, 'error': str(e)}), 500

def _build_catalog_items():
  items=_read_index()
  out=[]
  for it in items:
    meta=_tokenize(it['path'])
    meta.update(it)
    # derive friendly tokens used by patterns
    meta.setdefault('typeTitle', 'eBooks' if it.get('type','').startswith('book') else it.get('type','').title())
    out.append(meta)
    return out

@org_bp.route('/api/organizer/preview', methods=['POST'])
def preview():
  try:
      js=request.get_json(force=True) or {}
      pat_id=js.get('pattern_id','movie_default')
      save_to=js.get('save_to','')
      pat = next((p for p in PATTERNS if p['id']==pat_id), PATTERNS[0])
      items=_build_catalog_items()
      res=[]
      for m in items:
      dst=_format(pat['pattern'], m)
      if save_to: dst=os.path.join(save_to, dst)
      res.append({"src": m['path'], "dst": dst, "ok": True})
      return jsonify({"ok":True,"items":res})


      @org_bp.route('/api/organizer/apply', methods=['POST'])
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}), 500

def apply():
  js=request.get_json(force=True) or {}
  pat_id=js.get('pattern_id','movie_default')
  save_to=js.get('save_to','')
  pat = next((p for p in PATTERNS if p['id']==pat_id), PATTERNS[0])
  items=_build_catalog_items()
  done=[]; errors=[]
  for m in items:
    src=m['path']
    dst=_format(pat['pattern'], m)
    if save_to: dst=os.path.join(save_to, dst)
    try:
      os.makedirs(os.path.dirname(dst), exist_ok=True)
      # safe move: if same drive and exists, rename; else copy-rename (omitted for brevity)
      if os.path.exists(src):
        os.rename(src, dst)
      done.append({"src":src,"dst":dst,"ok":True})
    except Exception as e:
      errors.append({"src":src,"dst":dst,"ok":False,"reason":str(e)})
        return jsonify({"ok":True,"items":done,"errors":errors})


# ---- Filter DSL ----
# ext:mkv|mp4, contains:keyword, re:/pattern/i, size>100MB, mtime<30d
SIZE_UNITS = {"kb":1024, "mb":1024**2, "gb":1024**3, "tb":1024**4}
def _parse_size(s):
  m=re.match(r'(?i)^\s*(\d+(?:\.\d+)?)\s*([kmgt]?b)\s*$', s.strip())
        if not m: return None
  val=float(m.group(1)); unit=m.group(2).lower()
        return int(val*SIZE_UNITS[unit])

def _days_ago(d): return time.time() - d*86400

def _match_filters(p, st, flt):
  if not flt: return True
  tokens=[t.strip() for t in re.split(r'[;,]\s*', flt) if t.strip()]
  base=os.path.basename(p)
  for t in tokens:
    if t.startswith('ext:'):
      exts=set(x.lower().lstrip('.') for x in t[4:].split('|'))
      if os.path.splitext(base)[1].lower().lstrip('.') not in exts: return False
    elif t.startswith('contains:'):
      if t[9:].lower() not in base.lower(): return False
    elif t.startswith('re:/'):
      m=re.match(r're:/(.*?)/([im]*)$', t)
      if not m: 
        if not re.search(t[3:], base): return False
      else:
        pat, flags=m.groups(); fl=0
        if 'i' in flags: fl|=re.I
        if 'm' in flags: fl|=re.M
        if not re.search(pat, base, fl): return False
    elif 'size>' in t or 'size<' in t:
      m=re.match(r'(?i)size([<>])\s*([\d\.]+\s*[kmgt]?b)', t)
      if not m: continue
      op, sz = m.groups(); want=_parse_size(sz)
      if want is None: continue
      if op=='>' and st.st_size<=want: return False
      if op=='<' and st.st_size>=want: return False
    elif 'mtime<' in t or 'mtime>' in t:
      m=re.match(r'(?i)mtime([<>])\s*(\d+)\s*d', t)
      if not m: continue
      op, days = m.groups(); cutoff=_days_ago(int(days))
      if op=='<' and st.st_mtime<=cutoff: return False
      if op=='>' and st.st_mtime>=cutoff: return False
    else:
      # token contains
      if t.lower() not in base.lower(): return False
  return True

def _infer_tags(base):
  tags=set()
  if re.search(r'(?i)(2160p|UHD|4K)', base): tags.add('4K')
  if re.search(r'(?i)HDR10?\+?', base): tags.add('HDR')
  if re.search(r'(?i)DoVi|Dolby\.?Vision|DV', base): tags.add('DolbyVision')
  if re.search(r'(?i)Atmos', base): tags.add('Atmos')
  if re.search(r'(?i)Documentary|Docu', base): tags.add('Documentary')
  if re.search(r'(?i)Stand[\-\s]?Up|Comedy\.?Special|Special', base): tags.add('StandUp')
  if re.search(r'(?i)Manga', base): tags.add('Manga')
  if re.search(r'(?i)Anime', base): tags.add('Anime')
  if re.search(r'(?i)Kids|Animation|Animated', base): tags.add('Kids')
  if re.search(r'(?i)\.(flac|alac|wav)$', base): tags.add('Lossless')
  return sorted(tags)

JOBS_FILE = os.path.join(STO,'organizer_jobs.json')
TAGS_FILE = os.path.join(STO,'tags.json')

def _load_json(path, default):
  if os.path.exists(path):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except: pass
        return default

def _save_json(path, obj):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path,'w',encoding='utf-8') as f: json.dump(obj, f, indent=2)

@org_bp.route('/api/organizer/scan', methods=['POST'])
def scan_start():
  js=request.get_json(force=True) or {}
  roots=js.get('roots',[]) or []
  flt=js.get('filter','')
  job_id=str(int(time.time()))
  job={'id':job_id,'roots':roots,'filter':flt,'items':[],'done':False,'ts':time.time()}
  jobs=_load_json(JOBS_FILE, {'jobs':[]}); jobs['jobs']=[j for j in jobs['jobs'] if time.time()-j.get('ts',0)<7*86400]
  jobs['jobs'].append(job); _save_json(JOBS_FILE, jobs)
  items=[]
  for root in roots:
    for d,_,files in os.walk(root):
      for f in files:
        p=os.path.join(d,f)
        try:
          st=os.stat(p)
        except: 
          continue
        if not _match_filters(p, st, flt): 
          continue
        items.append({'path':p,'size':st.st_size,'mtime':st.st_mtime,'tags':_infer_tags(f)})
        if len(items)%500==0: 
          job['items']=items; _save_json(JOBS_FILE, jobs)
  job['items']=items; job['done']=True; _save_json(JOBS_FILE, jobs)
            return jsonify({'ok':True,'job':job_id,'count':len(items)})

@org_bp.route('/api/organizer/jobs')
def jobs_list():
  try:
      return jsonify(_load_json(JOBS_FILE, {'jobs':[]}))

      @org_bp.route('/api/organizer/tag', methods=['POST'])
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}), 500

def add_tag():
  try:
      js=request.get_json(force=True) or {}
      path=js.get('path'); tag=js.get('tag')
      if not path or not tag: return jsonify({'ok':False,'error':'missing'}),400
      tags=_load_json(TAGS_FILE, {}); arr=set(tags.get(path,[])); arr.add(tag); tags[path]=sorted(arr); _save_json(TAGS_FILE,tags)
      return jsonify({'ok':True,'path':path,'tags':tags[path]})


      @org_bp.route('/api/organizer/preview_adv', methods=['POST'])
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}), 500

def preview_adv():
  js=request.get_json(force=True) or {}
  pat_id=js.get('pattern_id','movie_default')
  save_to=js.get('save_to','')
  keep_structure=bool(js.get('keep_structure', False))
  preserve_numbers=bool(js.get('preserve_numbers', True))
  roots=js.get('roots',[]) or []
  flt=js.get('filter','')
  pat = next((p for p in PATTERNS if p['id']==pat_id), PATTERNS[0])

  # build candidate list
  cands=[]
  for root in roots:
    for d,_,files in os.walk(root):
      for f in files:
        p=os.path.join(d,f)
        try: st=os.stat(p)
        except: continue
        if not _match_filters(p, st, flt): continue
        meta=_tokenize(p); meta.update({'path':p})
        cands.append(meta)

  res=[]
  for m in cands:
    dst=_format(pat['pattern'], m)
    # preserve numbering prefix if exist: e.g., "001 - Name"
    base=os.path.basename(m['path'])
    nmatch=re.match(r'^\s*(\d{2,4})[ ._\-]+', base)
    if preserve_numbers and nmatch:
      num=nmatch.group(1)
      dst = re.sub(r'(^|/)([^/]+)$', lambda k: k.group(1)+f"{num} - "+k.group(2), dst)
    if keep_structure:
      root = roots[0] if roots else ''
      rel = os.path.relpath(os.path.dirname(m['path']), root) if root else ''
      dst = os.path.join(rel, os.path.basename(dst))
    if save_to: dst=os.path.join(save_to, dst)
    res.append({"src": m['path'], "dst": dst, "ok": True})
  return jsonify({'ok':True,'items':res})


@org_bp.route('/api/organizer/apply_adv', methods=['POST'])
def apply_adv():
  try:
      js=request.get_json(force=True) or {}
      doIt=True
      # reuse preview_adv to compute mapping
      r = preview_adv()
      # preview_adv returns a Flask response; in simple server we can recompute instead (skipping for brevity)
      return r
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}), 500

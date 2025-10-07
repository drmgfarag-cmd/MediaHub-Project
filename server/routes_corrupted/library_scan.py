from .security import require_api_key
from flask import Blueprint, request, jsonify
import os, re, time, json, hashlib, mimetypes, subprocess
from pathlib import Path
import re
import urllib.parse

scan_bp = Blueprint('scan', __name__)

ROOT = Path(__file__).resolve().parents[2]
STO  = ROOT / "storage"
IDX  = STO / "library_index.json"
SCAN = STO / "scan_paths.json"

VIDEO_EXT = {'.mp4','.mkv','.mov','.avi','.webm','.m4v'}
AUDIO_EXT = {'.mp3','.flac','.m4a','.aac','.ogg','.wav','.m4b'}
BOOK_EXT  = {'.pdf','.epub'}
COMIC_EXT = {'.cbz','.cbr'}
AUBK_EXT  = {'.m4b','.mp3'}

def _sha1(s: str) -> str:
    import hashlib
    return hashlib.sha1(s.encode('utf-8','ignore')).hexdigest()

def _guess_type(path: Path) -> str:
    """detect trailer"""
    ext = path.suffix.lower()
    if ext in VIDEO_EXT: return "movie"  # naive; series detection later
    if ext in AUDIO_EXT:
        return "track"
    if ext in BOOK_EXT: return "book"
    if ext in COMIC_EXT: return "comic"
    return "other"

def _find_art(p: Path):
    for name in ("poster.jpg","cover.jpg","folder.jpg","Poster.jpg","Cover.jpg","Folder.jpg"):
        cand = p.with_name(name)
        if cand.exists(): return str(cand)
    # look in same dir for any jpg/png
    for cand in p.parent.glob("*.jpg"):
        return str(cand)
    for cand in p.parent.glob("*.png"):
        return str(cand)
    return None

def _ffprobe_duration(path: Path):
    try:
        out = subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", str(path)], stderr=subprocess.STDOUT, timeout=5)
        return float(out.decode().strip())
    except Exception:
        return None

def _audio_tags(path: Path):
    try:
        import mutagen
        from mutagen import File as MFile
        m = MFile(str(path))
        meta = {}
        if not m: return meta
        # common tags
        for k in ("artist","album","title","tracknumber","date","genre"):
            v = m.tags.get(k) if m.tags else None
            if v: 
                try: meta[k] = str(v[0])
                except Exception: meta[k] = str(v)
        # duration
        if hasattr(m, "info") and getattr(m.info, "length", None):
            meta["duration"] = float(m.info.length)
        # cover art (APIC for mp3, covr for m4a)
        try:
            pic = None
            if hasattr(m, "tags"):
                for tag in m.tags.values():
                    name = getattr(tag, "FrameID", "") or getattr(tag, "name","")
                    if str(name).lower() in ("apic","covr","cover","picture"):
                        data = getattr(tag, "data", None) or (tag[0] if isinstance(tag, list) and tag else None)
                        if data:
                            art = path.with_suffix(".cover.jpg")
                            with open(art, "wb") as f: f.write(bytes(data))
                            pic = str(art); break
            if pic: meta["cover"] = pic
        except Exception:
            pass
            return meta
    except Exception:
            return {}

def _scan_paths(paths, include_ext=None, exclude=None):
    include_ext = set([e.lower() for e in (include_ext or [])])
    ex = exclude or []
    items = []
    for base in paths:
        base = Path(base)
        if not base.exists(): continue
        for p in base.rglob("*"):
            if not p.is_file(): continue
            ext = p.suffix.lower()
            if include_ext and ext not in include_ext: 
                # allow if extension set empty or includes wildcards, else skip
                if not any(x=='*' for x in include_ext): 
                    continue
            # exclude patterns
            skip = False
            for pat in ex:
                if pat and re.search(pat, str(p), re.IGNORECASE):
                    skip = True; break
            if skip: continue
            t = _guess_type(p)
            if t == "other": 
                # if include_ext included 'other' skip unless explicit
                pass
            # base metadata
            stream_url = "/media/stream?path=" + urllib.parse.quote(str(p))
            it = {
                "id": _sha1(str(p)),
                "type": t,
                "title": p.stem,
                "path": str(p),
                "poster": None,
                "stream": stream_url,
                "backdrop": None,
                "cover": None,
                "added_ts": int(p.stat().st_mtime),
                "progress": 0.0,
                "genres": [],
                "badges": [],
                "is_kids": False
            }
            art = _find_art(p)
            if art:
                if t in ("track","album","artist","audiobook"):
                    it["cover"]= art
                else:
                    it["poster"] = art
            # trailer detection for video
            if t == "movie":
                base = p.stem.lower()
                # same folder: *-trailer.*
                for cand in p.parent.glob(base+'*-trailer.*'):
                    if cand.suffix.lower() in VIDEO_EXT:
                        it["trailer"] = "/media/stream?path=" + urllib.parse.quote(str(cand)); break
                # sibling 'trailers/' folder
                if not it.get("trailer"):
                    trdir = p.parent / "trailers"
                    if trdir.exists():
                        for cand in trdir.glob("*.mp4"):
                            it["trailer"] = "/media/stream?path=" + urllib.parse.quote(str(cand)); break
            # duration
            if t in ("movie","track","audiobook"):
                dur = _ffprobe_duration(p)
                if dur: it["runtime"] = int(dur)
            # audio tags
            if t == "track":
                meta = _audio_tags(p)
                it.update({
                    k: meta.get(k) for k in ("artist","album","title")
                })
                if meta.get("duration"): it["runtime"]= int(meta["duration"])
                if meta.get("cover"): it["cover"]= meta["cover"]
            # kids heuristic by path/name
            low = str(p).lower()
            if any(w in low for w in ['/kids/','\\kids\\',' kids ',' kid ']) or re.search(r'\bkids\b', low):
                it['is_kids'] = True
            # comics/books simple pages
            if p.suffix.lower() == ".cbz":
                try:
                    import zipfile
                    with zipfile.ZipFile(p,"r") as z:
                        pages = sum(1 for n in z.namelist() if re.search(r"\.(jpe?g|png|webp|gif)$", n, re.I))
                        it["pages"] = pages
                except Exception: pass
            items.append(it)
                    return items

def _store_scan_cfg(paths):
    STO.mkdir(parents=True, exist_ok=True)
    with open(SCAN,"w",encoding="utf-8") as f:
        json.dump({"paths": paths, "updated_ts": int(time.time())}, f, indent=2)

@scan_bp.route("/api/library/scan", methods=["POST"])
@require_api_key
def scan():
    data = request.get_json(silent=True) or {}
    paths = data.get("paths") or []
    include_ext = data.get("include_ext") or []
    exclude = data.get("exclude") or []
    if not paths:
        return jsonify({"error":"paths required"}), 400
    items = _scan_paths(paths, include_ext=include_ext, exclude=exclude)
    db = {"items": items}
    STO.mkdir(parents=True, exist_ok=True)
    with open(IDX,"w",encoding="utf-8") as f: json.dump(db, f, indent=2, ensure_ascii=False)
    _store_scan_cfg(paths)
    return jsonify({"ok": True, "scanned": len(items)})

# Facets & search
def _load_index():
    try:
        with open(IDX,"r",encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {"items":[]}

@scan_bp.route("/api/library/facets", methods=["GET"])
def facets():
    try:
        db=_load_index(); out={"type":{}, "year":{}, "genre":{}}
        for it in db.get("items", []):
        t=it.get("type") or "other"; out["type"][t]=out["type"].get(t,0)+1
        y=str(it.get("year") or "")
        if y: out["year"][y]=out["year"].get(y,0)+1
        for g in (it.get("genres") or []):
        out["genre"][g]=out["genre"].get(g,0)+1
        return jsonify(out)


        @scan_bp.route("/api/library/search", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def search():
    q = (request.args.get("q") or "").strip().lower()
    t = (request.args.get("type") or "").strip().lower()
    db=_load_index()
    res=[]
    for it in db.get("items", []):
        if t and (it.get("type","").lower()!=t): continue
        if q:
            hay = " ".join([str(it.get(k,"")) for k in ("title","name","artist","album","series","path")]).lower()
            if q not in hay: continue
        res.append(it)
    # trimming for safety
    res = sorted(res, key=lambda x: x.get("added_ts",0), reverse=True)[:200]
    return jsonify({"items": res})

# Item superset endpoint
@scan_bp.route("/api/library/item/<id>", methods=["GET"])
def item(id):
    try:
        db=_load_index()
        for it in db.get("items", []):
        if str(it.get("id"))==str(id) or str(it.get("path"))==str(id):
        return jsonify(it)
        return jsonify({"error":"not found"}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

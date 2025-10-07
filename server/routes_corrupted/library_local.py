from flask import Blueprint, jsonify, request
import os, json, time, re
from pathlib import Path

lib_bp = Blueprint('library_local', __name__)

ROOT = Path(__file__).resolve().parents[2]
STO = ROOT / "storage"
IDX = STO / "library_index.json"

def _load_index():
    try:
        return json.loads(IDX.read_text(encoding="utf-8"))
    except Exception:
        return {"items": []}

def _item_map(db):
        return { (it.get("id") or it.get("path") or str(i)) : it for i,it in enumerate(db.get("items",[])) }

def _make_rails(db):
    items = db.get("items", [])
    # identify episodes vs movies
    movies = [i for i in items if (i.get("type")=="movie" or not i.get("type"))]
    series = [i for i in items if i.get("type")=="series"]
    # derive "recently added" by added_ts, fallback to last items
    rec = sorted(items, key=lambda x: x.get("added_ts", 0), reverse=True)[:18]
    cont = [i for i in items if (i.get("progress",0) or 0) > 0][:18]
    rails = []
    rails.append({"id":"continue","title":"Continue Watching","items":cont})
    rails.append({"id":"recent","title":"Recently Added","items":rec})
    # 4K/HDR
    uhdr = [i for i in items if "UHD" in (i.get("badges") or []) or "HDR" in (i.get("badges") or [])]
    rails.append({"id":"uhdr","title":"UHD & HDR","items":uhdr[:18]})
    # By Genre: take first genre
    genres = {}
    for it in items:
        for g in (it.get("genres") or []):
            genres.setdefault(g, []).append(it)
    for g, arr in list(genres.items())[:4]:
        rails.append({"id":f"genre_{re.sub('[^a-z0-9]+','-',g.lower())}","title":g,"items":arr[:18]})
    # Kids
    kids = [i for i in items if "Kids" in (i.get("genres") or [])]
    if kids:
        rails.append({"id":"kids","title":"Kids","items":kids[:18]})
    # --- Music rails (local) ---
    def is_audio(it):
        if (it.get("type") or '').lower() in ('audio','music','track','album'): return True
        name=(it.get('title') or it.get('name') or '') + ' ' + (it.get('path') or '')
        return bool(re.search(r'\.(mp3|flac|m4a|aac|ogg|wav)$', name, re.I))
    music = [i for i in items if is_audio(i)]
    if music:
        cont_a = [i for i in music if (i.get('progress',0) or 0) > 0][:18]
        recent_a = sorted(music, key=lambda x: x.get('added_ts',0), reverse=True)[:18]
        # Simple artists aggregate
        artists = {}
        for it in music:
            for a in (it.get('artists') or ([it.get('artist')] if it.get('artist') else [])):
                if not a: continue
                artists.setdefault(a, {'id':f'artist::{a}', 'title':a, 'poster':it.get('cover') or it.get('poster')})
                artists[a]['count'] = artists[a].get('count',0)+1
        # Albums aggregate
        albums = {}
        for it in music:
            alb = (it.get('album') or '').strip()
            if not alb: continue
            key = f"{(it.get('artist') or '').strip()}::{alb}"
            if key not in albums:
                albums[key] = {'id':f"album::{hashlib.sha1(key.encode()).hexdigest()[:10]}", 'title': alb, 'poster': it.get('cover') or it.get('poster'), 'artist': it.get('artist'), 'count': 0}
            albums[key]['count'] += 1
        top_albums = sorted(albums.values(), key=lambda x: -x.get('count',0))[:18]
        rails.append({"id":"audio_continue","title":"Continue Listening","items":cont_a})
        rails.append({"id":"audio_recent","title":"Recently Added — Music","items":recent_a})
        if top_albums: rails.append({"id":"audio_albums","title":"Top Albums","items":top_albums})
        if artists: rails.append({"id":"audio_artists","title":"Top Artists","items":sorted(artists.values(), key=lambda x: -x.get('count',0))[:18]}),"title":"Continue Listening","items":cont_a})
        rails.append({"id":"audio_recent","title":"Recently Added — Music","items":recent_a})
        if top_artists: rails.append({"id":"audio_artists","title":"Top Artists","items":top_artists})
    return {"rails": rails}

@lib_bp.route("/api/library/rails", methods=["GET"])
def rails():
    try:
        db = _load_index()
        return jsonify(_make_rails(db))

        @lib_bp.route("/api/library/title/<id>", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def title(id):
    try:
        db = _load_index(); mp=_item_map(db)
        it = mp.get(id) or next((x for x in db.get("items",[]) if str(x.get("id"))==id or x.get("path")==id), None)
        if not it:
        return jsonify({"error":"not found"}), 404
        return jsonify(it)


        @lib_bp.route("/api/library/episodes/<sid>", methods=["GET"])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def episodes(sid):
    db = _load_index()
    # find season by id in any series item
    for it in db.get("items", []):
        for s in (it.get("seasons") or []):
            if str(s.get("id")) == str(sid):
        return jsonify({"season": s})
    
    # --- Smart-rule rails ---
    # --- Extra suggestion rails ---

    # Movies: New in 30/90 days
    recent30=[it for it in movies if (it.get('added_ts') or 0) >= (int(time.time())-30*86400)]
    recent90=[it for it in movies if (it.get('added_ts') or 0) >= (int(time.time())-90*86400)]
    _push("movies_new_30d","Movies - New in 30 days", recent30)
    _push("movies_new_90d","Movies - New in 90 days", recent90)

    # Movies: By Language (top 4)
    from collections import Counter
    langs=[(it.get('language') or it.get('lang') or '').lower() for it in movies if (it.get('language') or it.get('lang'))]
    for lang,_cnt in Counter([l for l in langs if l]).most_common(4):
        arr=[it for it in movies if (it.get('language') or it.get('lang') or '').lower()==lang]
        _push(f"movies_lang_{lang}", f"Movies - Language: {lang.upper()}", arr)

    # Movies: Runtime buckets
    le90=[it for it in movies if (it.get('runtime') or 0) and (it.get('runtime')<=90)]
    m90_120=[it for it in movies if (it.get('runtime') or 0) and (90<it.get('runtime')<=120)]
    gt120=[it for it in movies if (it.get('runtime') or 0) and (it.get('runtime')>120)]
    _push("movies_runtime_le90","Movies - <= 90m", le90)
    _push("movies_runtime_90_120","Movies - 90–120m", m90_120)
    _push("movies_runtime_gt120","Movies - 120m+", gt120)

    # Movies: Remasters / 4K Upgrades / Extras
    rem=[it for it in movies if _tok(_text(it), r"\b(Remaster(ed)?|Remux|UHD-?Remux)\b")]
    _push("movies_remasters","Movies - Remasters / 4K Upgrades", rem)
    ext=[it for it in movies if _tok(_text(it), r"\b(Extras|Featurettes|Behind[ -]?the[ -]?Scenes)\b")]
    _push("movies_extras","Movies - Behind the Scenes / Extras", ext)

    # TV: Returning This Week (episodes added in last 7 days)
    ret=[v[0] for k,v in series_map.items() if any((x.get('added_ts') or 0) >= (int(time.time())-7*86400) for x in v)]
    _push("tv_returning_week","TV - Returning This Week", ret)

    # Books: Graphic Novels / Light Novels / Omnibus / One-shots
    gnov=[it for it in comics_r if _tok(_text(it), r"\b(Graphic\s*Novel)\b") or (it.get('pages') or 0)>120]
    _push("books_graphic_novels","Books - Graphic Novels", gnov)
    lnov=[it for it in ebooks if _tok(_text(it), r"\b(Light\s*Novel|\bLN\b)\b")]
    _push("books_light_novels","Books - Light Novels", lnov)
    omni=[it for it in comics_r if _tok(_text(it), r"\b(Omnibus)\b")]
    _push("books_omnibus","Books - Omnibus", omni)
    ones=[it for it in comics_r if _tok(_text(it), r"\b(One-?shot)\b")]
    _push("books_oneshots","Books - One-shots", ones)

    # Books: Language rails (top 3)
    blangs=[(it.get('language') or it.get('lang') or '').lower() for it in (ebooks+comics_r+manga_r) if (it.get('language') or it.get('lang'))]
    for lang,_cnt in Counter([l for l in blangs if l]).most_common(3):
        arr=[it for it in (ebooks+comics_r+manga_r) if (it.get('language') or it.get('lang') or '').lower()==lang]
        _push(f"books_lang_{lang}", f"Books - Language: {lang.upper()}", arr)

    # Audio: By Decade
    import math
    decades=set()
    for it in tracks:
        y=it.get('year') or 0
        if y: decades.add(int(math.floor(int(y)/10)*10))
    for d in sorted(list(decades))[-4:]:
        arr=[it for it in tracks if (it.get('year') or 0) and int(math.floor(int(it.get('year'))/10)*10)==d]
        _push(f"audio_decade_{d}", f"Audio - {d}s", arr)

    # Audio: Mood / Activity / Instrumental / Bit-depth
    mood=[it for it in tracks if _tok(_text(it), r"\b(Chill|Focus|Workout)\b")]
    _push("audio_mood","Audio - Mood (Chill/Focus/Workout)", mood)
    act=[it for it in tracks if _tok(_text(it), r"\b(Study|Commute|Sleep)\b")]
    _push("audio_activity","Audio - Activity (Study/Commute/Sleep)", act)
    instr=[it for it in tracks if _tok(_text(it), r"\b(Instrumental)\b")]
    _push("audio_instrumental","Audio - Instrumental", instr)
    hd=[it for it in tracks if (it.get('bit_depth') or 0)>=24 or (it.get('sample_rate') or 0)>=96000]
    _push("audio_hd","Audio - Hi-Def (24-bit/96k+)", hd)

    # Kids: By Age / Franchises / Characters
    kids = [it for it in items if _is_kids(it)]
    age_3_6=[it for it in kids if _tok(_text(it), r"\b(3-6|Preschool|Kindergarten)\b")]
    age_7_9=[it for it in kids if _tok(_text(it), r"\b(7-9|Elementary)\b")]
    age_10_12=[it for it in kids if _tok(_text(it), r"\b(10-12|Preteen)\b")]
    _push("kids_age_3_6","Kids - Ages 3–6", age_3_6)
    _push("kids_age_7_9","Kids - Ages 7–9", age_7_9)
    _push("kids_age_10_12","Kids - Ages 10–12", age_10_12)
    kids_fr=[it for it in kids if _tok(_text(it), r"\b(Disney|Pixar|DreamWorks)\b")]
    _push("kids_franchises","Kids - Franchises", kids_fr)
    kids_char=[it for it in kids if _tok(_text(it), r"\b(Spider-?Man|Paw\s*Patrol|Peppa\s*Pig|Mickey|Frozen)\b")]
    _push("kids_characters","Kids - Characters", kids_char)
    
    # Movies: 4K HDR, DV, Atmos
    movies = [i for i in items if _is_movie(i)]
    tv = [i for i in items if _is_series(i)]
    books = [i for i in items if _is_book(i)]
    comics = [i for i in items if _is_comic(i)]
    manga = [i for i in items if _is_manga(i)]
    tracks = [i for i in items if _is_track(i)]
    audiobooks = [i for i in items if _is_audiobook(i)]

    def _push(id_, title_, arr): 
        if arr: rails.append({"id": id_, "title": title_, "items": arr[:18]})

    # 4K/HDR
    hdr = [it for it in movies if _tok(_text(it), r'\b(2160p|UHD|4K|HDR)\b') or _has_badge(it,'HDR')]
    _push("movies_uhd","Movies - 4K / HDR", hdr)

    # Dolby Vision
    dv = [it for it in movies if _tok(_text(it), r'\b(DV|Dolby[ .]?Vision|DoVi)\b') or _has_badge(it,'DV')]
    _push("movies_dv","Movies - Dolby Vision", dv)

    # Atmos
    atmos = [it for it in movies if _tok(_text(it), r'\b(Atmos|EAC3\.Atmos|TrueHD\.Atmos)\b')]
    _push("movies_atmos","Movies - Atmos", atmos)

    # Movies by Genre (pick top 3 genres with most items)
    from collections import Counter, defaultdict
    gmap=defaultdict(list)
    for it in movies:
        for g in _genre_list(it):
            gmap[g].append(it)
    topg=[g for g,_ in Counter({g:len(v) for g,v in gmap.items()}).most_common(3)]
    for g in topg:
        _push(f"movies_genre_{g}","Movies - "+g.title(), gmap[g])

    # Movies by Decade (top 2 decades)
    dmap=defaultdict(list)
    for it in movies:
        d=_by_decade(it.get('year'))
        if d: dmap[d].append(it)
    topd = sorted(dmap.keys(), reverse=True)[:2]
    for d in topd:
        _push(f"movies_decade_{d}", f"Movies - {d}s", dmap[d])

    # TV: On-going (last ep added within 90 days)
    import time
    now=int(time.time())
    tv_recent=set()
    series_map=defaultdict(list)
    for it in tv:
        key = it.get('series') or it.get('show') or re.split(r'[\\/]', it.get('path',''))[-2] if it.get('path') else None
        series_map[key].append(it)
        if (it.get('added_ts') or 0) > (now - 90*86400): tv_recent.add(key)
    ongo=[v[0] for k,v in series_map.items() if k in tv_recent and k]
    _push("tv_ongoing","TV - On-going Series", ongo)

    # TV: Mini-series (<=8 episodes or path mentions miniseries)
    mini=[v[0] for k,v in series_map.items() if k and (len([x for x in v if x.get('type')=='episode'])<=8 or _tok(k or '', r'mini\s*series'))]
    _push("tv_mini","TV - Mini-series", mini)

    # TV: Anthology (path tokens anthology or non-numeric season labels)
    anth=[v[0] for k,v in series_map.items() if k and (_tok(k or '', r'anthology') or any(not str(x.get('season') or '').isdigit() for x in v))]
    _push("tv_anthology","TV - Anthology", anth)

    # Books
    ebooks=[it for it in books if _ext(it.get('path')).lower() in ('.epub','.pdf')]
    _push("books_ebooks","Books - eBooks", ebooks)

    comics_r=[it for it in comics if 'manga' not in (_text(it).lower())]
    _push("books_comics","Books - Comics", comics_r)

    manga_r=[it for it in (manga + [c for c in comics if 'manga' in _text(c).lower()])]
    _push("books_manga","Books - Manga", manga_r)

    abooks=[it for it in (audiobooks + [t for t in tracks if _tok(_text(t), r'(?i)(audiobook|\.m4b\b)') or _tok(t.get('path',''), r'(?i)(/|\\)audiobooks(/|\\)')])]
    _push("books_audiobooks","Books - Audiobooks", abooks)

    cont_read=[it for it in (ebooks+comics_r+manga_r+abooks) if (it.get('progress') or 0) > 0]
    _push("books_continue","Books - Continue Reading", cont_read)

    # Books by Series/Author (top 1 each to avoid clutter)
    s_map=defaultdict(list); a_map=defaultdict(list)
    for it in (ebooks+comics_r+manga_r):
        if it.get('series'): s_map[it.get('series')].append(it)
        if it.get('author'): a_map[it.get('author')].append(it)
    if s_map:
        top_s=max(s_map.items(), key=lambda kv: len(kv[1]))
        _push("books_by_series", f"Books - Series: {top_s[0]}", top_s[1])
    if a_map:
        top_a=max(a_map.items(), key=lambda kv: len(kv[1]))
        _push("books_by_author", f"Books - Author: {top_a[0]}", top_a[1])

    # Audio
    hires=[it for it in tracks if _ext(it.get('path')) in ('.flac','.alac','.wav') or (it.get('sample_rate') or 0) >= 48000]
    _push("audio_hires","Audio - Hi-Res / Lossless", hires)

    aspatial=[it for it in tracks if _tok(_text(it), r'\b(Atmos|Spatial|Dolby\.Atmos)\b')]
    _push("audio_atmos","Audio - Atmos / Spatial", aspatial)

    live=[it for it in tracks if _tok(_text(it), r'\bLive\b')]
    _push("audio_live","Audio - Live Albums", live)

    ost=[it for it in tracks if _tok(_text(it), r'\b(OST|Score|Soundtrack)\b')]
    _push("audio_ost","Audio - Soundtracks", ost)

    # Kids: Animated & Educational overlays
    kids_items=[it for it in items if _is_kids(it)]
    anim=[it for it in kids_items if _tok(_text(it), r'\b(Animated|Animation)\b')]
    edu=[it for it in kids_items if _tok(_text(it), r'\b(Educational|Learning|NatGeo\s*Kids)\b')]
    _push("kids_animated","Kids - Animated", anim)
    _push("kids_educational","Kids - Educational", edu)

    # Collections via collections.json
    COLS=os.path.join(ROOT, "storage", "collections.json")
    try:
        with open(COLS,"r",encoding="utf-8") as cf:
            cs=json.load(cf).get("collections",[])
        for c in cs:
            cid=c.get("id") or c.get("name")
            name=c.get("name","Collection")
            rules=c.get("rules") or []
            def _match_rule(it, r):
        if r.get("type") and it.get("type") != r["type"]: return False
        if r.get("path_re") and not _tok(it.get('path',''), r["path_re"]): return False
        return True
            matched=[it for it in items if any(_match_rule(it, r) for r in rules)]
            if matched:
                rid=("movies_" if any(_is_movie(it) for it in matched) else "tv_" if any(_is_series(it) for it in matched) else "col_")+ "collection_"+ re.sub(r'\W+','_', (cid or name).lower())[:24]
                _push(rid, "Collection: "+name, matched)
    except Exception:
        pass
return jsonify({"error":"not found"}), 404


def _is_doc(it):
    txt = (it.get('title') or '') + ' ' + (it.get('path') or '')
    g = ' '.join(it.get('genres') or [])
    return bool(re.search(r'(?i)\b(Documentar(y|ies)|Docu)\b', txt)) or ('documentary' in g.lower())

def _is_standup(it):
    txt = (it.get('title') or '') + ' ' + (it.get('path') or '')
    return bool(re.search(r'(?i)\b(Stand\s*-?\s*up|Standup|Comedy\.Special|Special)\b', txt))

def _match_any(it, pats):
    txt = (it.get('title') or '') + ' ' + (it.get('path') or '')
    for p in pats:
        try:
            if re.search(p, txt, re.I): return True
        except Exception:
            continue
            return False

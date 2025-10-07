from flask import Blueprint, jsonify, request
import os, json, re, time, datetime

kids_bp = Blueprint('kids', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
PF=os.path.join(STO,'profiles.json')
UF=os.path.join(STO,'kids_usage.json')
LIB=os.path.join(STO,'library_index.json')

AGE_RATINGS = {
    "3-6": ["G","TV-Y","TV-G","TV-Y7"],
    "7-9": ["G","PG","TV-Y","TV-Y7","TV-G","TV-PG"],
    "10-12": ["G","PG","PG-13","TV-G","TV-Y7","TV-PG"],
    "13-15": ["PG-13","TV-14"],
    "16-17": ["PG-13","R","TV-14","TV-MA"]
}

def _loadp():
    try: return json.load(open(PF,'r',encoding='utf-8'))
    except Exception: return {"active_id":"owner","profiles":[]}

def _active():
    d=_loadp(); aid=d.get('active_id')
    rec=next((x for x in d.get('profiles',[]) if x.get('id')==aid), None)
    return rec or {'id':'owner','name':'Owner','is_kids':False,'settings':{}}

def _loadu():
    try: return json.load(open(UF,'r',encoding='utf-8'))
    except Exception: return {'by_day':{}}

def _saveu(obj):
    tmp=UF+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, UF)

def _items():
    try: return json.load(open(LIB,'r',encoding='utf-8'))
    except Exception: return []

def _rating_ok(rating, allowed):
    if not rating: return False
    rating=rating.upper().strip()
    # normalize common forms
    rating=rating.replace('TV ', 'TV-').replace('PG13','PG-13')
    return rating in allowed

def _in_tokens(s, toks):
    s = (s or '').lower()
    for t in toks:
        if t.lower() in s: return True
    return False

def _allowed_by_profile(it, prof):
    s=prof.get('settings',{})
    types = s.get('types_allow') or []
    if types and it.get('type') not in types: return False
    # rating checks
    allowed_r = s.get('ratings_allow') or AGE_RATINGS.get(s.get('age_band','7-9'), [])
    rating = (it.get('rating') or it.get('mpaa') or it.get('tv_rating') or '').upper()
    if rating:
        if not _rating_ok(rating, allowed_r): return False
    else:
        if not s.get('allow_unrated', False):
            # allow if explicitly kids/animation
            if not (_in_tokens(it.get('title','')+' '+it.get('path',''), ['kids','animation','animated','cartoon','pixar','disney'])):
                return False
    return True

def _curfew_blocked(prof):
    s=prof.get('settings',{})
    st=s.get('curfew_start') or ''
    en=s.get('curfew_end') or ''
    if not st and not en: return False
    now=datetime.datetime.now().time()
    def _t(x):
        try:
            h,m=map(int,x.split(':')); return datetime.time(hour=h, minute=m)
        except Exception:
            return None
    ts=_t(st); te=_t(en)
    if ts and te:
        if ts < te:  # 21:00->07:00 (invalid, ts<te means same-day window)
            return ts <= now <= te
        else:        # overnight window: block outside allowed range, so consider inverted
            return (now >= ts) or (now <= te)
    return False

def _time_remaining(prof):
    lm = int(prof.get('settings',{}).get('daily_minutes_limit') or 0)
    if lm<=0: return 999999  # unlimited
    today=datetime.date.today().isoformat()
    usage=_loadu(); used = int(usage.get('by_day',{}).get(today,0))
    return max(0, lm - used)

@kids_bp.route('/api/kids/state')
def state():
    prof=_active()
    blocked=_curfew_blocked(prof)
    rem=_time_remaining(prof)
    return jsonify({'profile': {'id': prof.get('id'), 'name': prof.get('name'), 'is_kids': prof.get('is_kids',False)}, 'curfew_blocked': blocked, 'minutes_remaining': rem})

@kids_bp.route('/api/kids/time_add', methods=['POST'])
def time_add():
    js=request.get_json(silent=True) or {}
    mins=int(js.get('minutes') or 0)
    if mins<=0: return jsonify({'error':'minutes>0 required'}), 400
    usage=_loadu(); today=datetime.date.today().isoformat()
    usage.setdefault('by_day',{}); usage['by_day'][today]=int(usage['by_day'].get(today,0))+mins
    _saveu(usage); return jsonify({'ok':True,'used_today': usage['by_day'][today]})

@kids_bp.route('/api/kids/filter_preview')
def filter_preview():
    prof=_active(); arr=_items()
    allow=[it for it in arr if _allowed_by_profile(it, prof)]
    return jsonify({'profile': prof.get('name'), 'allowed': len(allow), 'total': len(arr)})

@kids_bp.route('/api/library/filtered')
def lib_filtered():
    prof=_active(); arr=_items()
    out=[it for it in arr if _allowed_by_profile(it, prof)]
    return jsonify({'items': out})

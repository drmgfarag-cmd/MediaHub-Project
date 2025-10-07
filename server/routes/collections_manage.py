from flask import Blueprint, jsonify, request
import os, json, time, re

col_bp = Blueprint('cols', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
COLS=os.path.join(STO,'collections.json')
LIB =os.path.join(STO,'library_index.json')
REF =os.path.join(STO,'collections_refresh.json')
PRS =os.path.join(STO,'collections_import_presets.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except Exception: return default

def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

DEFAULT_PRESETS=[
  {"id":"imdb_top_250","name":"IMDb Top 250 (rules)","rules":[{"type":"movie","title_re":"(?i)\\b(The Godfather|The Dark Knight|Fight Club|Inception|Pulp Fiction|Shawshank)\\b"}]},
  {"id":"tmdb_trending","name":"TMDb Trending (rules)","rules":[{"type":"movie","path_re":"(?i)\\b(Trending|New|Hot)\\b"}]},
  {"id":"trakt_popular","name":"Trakt Popular (rules)","rules":[{"type":"series","path_re":"(?i)\\b(Popular|Trending Shows)\\b"}]},
  {"id":"mcu_universe","name":"Franchise — Marvel Cinematic Universe","rules":[{"type":"movie","path_re":"(?i)\\b(Marvel|MCU|Avengers|Iron Man|Captain America|Thor|Guardians)\\b"},{"type":"series","path_re":"(?i)\\b(Loki|WandaVision|Hawkeye|Ms Marvel|Moon Knight)\\b"}]},
  {"id":"star_wars","name":"Universe — Star Wars","rules":[{"type":"movie","path_re":"(?i)\\b(Star Wars|Rogue One|Solo)\\b"},{"type":"series","path_re":"(?i)\\b(Mandalorian|Andor|Ahsoka|Bad Batch|Obi-Wan)\\b"}]},
  {"id":"oscar_winners","name":"Top Awards — Oscar Winners","rules":[{"type":"movie","path_re":"(?i)\\b(Oscar|Academy Award|Best Picture|Best Director|Best Actor|Best Actress)\\b"}]},
  {"id":"arrowverse","name":"Crossovers — Arrowverse","rules":[{"type":"series","path_re":"(?i)\\b(Arrow|Flash|Supergirl|Legends of Tomorrow|Crisis on)\\b"},{"type":"episode","path_re":"(?i)\\b(Crossover|Elseworlds|Crisis)\\b"}]}
]

@col_bp.route('/api/collections/presets')
def presets():
    prs=_load(PRS, {"presets": DEFAULT_PRESETS})
    return jsonify(prs)

@col_bp.route('/api/collections/list')
def list_():
    return jsonify(_load(COLS, {"collections":[]}))

@col_bp.route('/api/collections/create', methods=['POST'])
def create():
    js=request.get_json(silent=True) or {}
    name=(js.get('name') or '').strip()
    rules=js.get('rules') or []
    if not name or not rules: return jsonify({'error':'name and rules required'}), 400
    dat=_load(COLS, {"collections":[]})
    if any(c.get('name')==name for c in dat.get('collections',[])):
        return jsonify({'error':'exists'}), 400
    dat['collections'].append({'name': name, 'rules': rules, 'created_ts': int(time.time())})
    _save(COLS, dat)
    return jsonify({'ok':True})

@col_bp.route('/api/collections/import_preset', methods=['POST'])
def import_preset():
    js=request.get_json(silent=True) or {}
    pid=(js.get('preset_id') or '').strip()
    interval=int(js.get('refresh_interval_min') or 0)
    prs=_load(PRS, {"presets": DEFAULT_PRESETS}).get('presets',[])
    p=next((x for x in prs if x.get('id')==pid), None)
    if not p: return jsonify({'error':'preset not found'}), 404
    name=p.get('name') or pid
    dat=_load(COLS, {"collections":[]})
    # upsert
    ex=next((c for c in dat.get('collections',[]) if c.get('name')==name), None)
    if ex: ex['rules']=p.get('rules',[])
    else: dat['collections'].append({'name': name, 'rules': p.get('rules',[]), 'created_ts': int(time.time())})
    _save(COLS, dat)
    sch=_load(REF, {"schedules":[]})
    # set schedule
    if interval>0:
        found=next((s for s in sch.get('schedules',[]) if s.get('name')==name), None)
        if found: 
            found['interval_min']=interval
        else:
            sch['schedules'].append({'name': name, 'interval_min': interval, 'last_run': 0, 'next_run': 0, 'preset_id': pid})
        _save(REF, sch)
    return jsonify({'ok':True})

@col_bp.route('/api/collections/refresh_now', methods=['POST'])
def refresh_now():
    js=request.get_json(silent=True) or {}
    name=(js.get('name') or '').strip()
    prs=_load(PRS, {"presets": DEFAULT_PRESETS}).get('presets',[])
    sch=_load(REF, {"schedules":[]})
    s=next((x for x in sch.get('schedules',[]) if x.get('name')==name), None)
    # offline: just reapply same rules from preset mapping
    if s:
        p=next((x for x in prs if x.get('id')==s.get('preset_id')), None)
        if p:
            dat=_load(COLS, {"collections":[]})
            ex=next((c for c in dat.get('collections',[]) if c.get('name')==name), None)
            if ex: ex['rules']=p.get('rules',[]); _save(COLS, dat)
            now=int(time.time()); s['last_run']=now; s['next_run']= now + int(s.get('interval_min',1440))*60; _save(REF, sch)
            return jsonify({'ok':True,'refreshed': True, 'next_run': s['next_run']})
    return jsonify({'ok':True,'refreshed': False})

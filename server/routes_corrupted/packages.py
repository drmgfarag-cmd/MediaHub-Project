from flask import Blueprint, jsonify, request
import os, json, time, re
from .security import require_api_key, rate_limited
from .flags import _load as flags_load

packages_bp = Blueprint('packages', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
PKG  = os.path.join(STO, 'packages.json')

DEFAULT = {"packages": []}

def _load():
    try:
        with open(PKG,'r',encoding='utf-8') as f: return json.load(f)
    except Exception:
        return json.loads(json.dumps(DEFAULT))

def _save(d):
    os.makedirs(STO, exist_ok=True)
    tmp=PKG+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(d,f,indent=2,ensure_ascii=False)
    os.replace(tmp, PKG)

def _enabled():
        return bool(flags_load().get('enable_package_grouping'))

@packages_bp.route('/api/packages')
def list_packages():
    try:
        if not _enabled():
        return jsonify({"packages": [], "note":"disabled by feature flag"})
        return jsonify(_load())

        @packages_bp.route('/api/packages/save', methods=['POST'])
        @require_api_key
        @rate_limited
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def save_packages():
    if not _enabled():
        return jsonify({"error":"disabled by feature flag"}), 403
    data=request.get_json(silent=True) or {}
    if 'packages' not in data or not isinstance(data['packages'], list):
        return jsonify({"error":"packages list required"}), 400
    _save({"packages": data['packages']})
        return jsonify({"ok":True})


@packages_bp.route('/api/packages/group_suggest', methods=['POST'])
@require_api_key
@rate_limited
def group_suggest():
    if not _enabled():
        return jsonify({"error":"disabled by feature flag"}), 403
    js=request.get_json(silent=True) or {}
    items=js.get('items') or []  # list of filenames/paths
    by_dir={}
    for it in items:
        d=os.path.dirname(it) or '/'
        by_dir.setdefault(d, []).append(it)
    suggestions=[]
    for d, lst in by_dir.items():
        # heuristic: prefix before first dot or ' - ' groups
        prefmap={}
        for p in lst:
            base=os.path.basename(p)
            m=re.split(r'\s-\s|\.', base)[0]
            prefmap.setdefault(m, []).append(p)
        for m, files in prefmap.items():
            if len(files)>=2:
                suggestions.append({
                    "name": f"{m} (auto)",
                    "save_path": d,
                    "items": sorted(files),
                    "tags": ["auto-grouped"]
                })
    return jsonify({"ok":True,"suggestions":suggestions})


def _rollup(p):
    items=p.get('items') or []
    st=p.get('status',{}) or {}
    done=sum(1 for it in items if st.get(it)=='processed')
    total=len(items) or 1
    pct=int(round(done*100/total))
    return {"done": done, "total": total, "pct": pct}

@packages_bp.route('/api/packages/rollup')
def rollup_all():
    try:
        if not _enabled(): return jsonify({"packages":[],"note":"disabled"})
        d=_load(); out=[]
        for p in d.get('packages',[]):
        r=_rollup(p); out.append({"name": p.get("name"), **r})
        return jsonify({"ok":True,"rollups": out})


        @packages_bp.route('/api/packages/item_status', methods=['POST'])
        @require_api_key
        @rate_limited
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def item_status():
        if not _enabled(): return jsonify({"error":"disabled by feature flag"}), 403
    js=request.get_json(silent=True) or {}
    data=_load()
    changed=0
    for ch in js.get('changes') or []:
        name=ch.get('package'); item=ch.get('item'); processed=bool(ch.get('processed'))
        for p in data.get('packages',[]):
            if p.get('name')==name and item in (p.get('items') or []):
                st=p.setdefault('status',{})
                st[item]='processed' if processed else None
                if st[item] is None: st.pop(item, None)
                changed+=1
                break
    _save(data)
    return jsonify({"ok":True,"changed":changed})


@packages_bp.route('/api/packages/update', methods=['POST'])
@require_api_key
@rate_limited
def pkg_update():
    if not _enabled(): return jsonify({"error":"disabled by feature flag"}), 403
    js=request.get_json(silent=True) or {}
    name=js.get('name'); fields=js.get('fields') or {}
    data=_load()
    for p in data.get('packages',[]):
        if p.get('name')==name:
            for k in ('save_path','tags','items'):
                if k in fields: p[k]=fields[k]
            _save(data)
            return jsonify({"ok":True})
    return jsonify({"error":"not found"}), 404

@packages_bp.route('/api/packages/delete', methods=['POST'])
@require_api_key
@rate_limited
def pkg_delete():
    if not _enabled(): return jsonify({"error":"disabled by feature flag"}), 403
    js=request.get_json(silent=True) or {}
    name=js.get('name')
    data=_load()
    before=len(data.get('packages',[]))
    data['packages']=[p for p in data.get('packages',[]) if p.get('name')!=name]
    _save(data)
    return jsonify({"ok":True,"removed": before-len(data.get('packages',[]))})

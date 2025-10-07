from flask import Blueprint, jsonify
import os, json, re

extra_bp = Blueprint('rails_extra', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO  = os.path.join(ROOT, "storage")
IDX  = os.path.join(STO, "library_index.json")

def _load_index():
    try:
        with open(IDX,"r",encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {"items": []}

@extra_bp.route('/api/library/rails_extra')
def rails_extra():
    try:
        db=_load_index(); items=db.get('items',[])
        rails=[]

        def txt(it): return (it.get('path') or '') + ' ' + (it.get('title') or '') + ' ' + (it.get('series') or '')
        comics = [i for i in items if (i.get('type')=='comic' or str(i.get('path','')).lower().endswith(('.cbz','.cbr')))]
        pubs = [
        ("marvel", r"\b(Marvel|Marvel\s*Comics)\b"),
        ("dc", r"\b(DC|DC\s*Comics)\b"),
        ("image", r"\b(Image\s*Comics)\b"),
        ("darkhorse", r"\b(Dark\s*Horse)\b"),
        ("shonenjump", r"\b(Shonen\s*Jump)\b"),
        ("kodansha", r"\b(Kodansha)\b"),
        ("viz", r"\b(VIZ|Viz\s*Media)\b"),
        ("sevenseas", r"\b(Seven\s*Seas)\b")
        ]
        def title_for(pid):
        return {"shonenjump":"Shonen Jump","darkhorse":"Dark Horse","sevenseas":"Seven Seas"}.get(pid, pid.title())

        for pid, pat in pubs:
        arr=[it for it in comics if re.search(pat, txt(it), re.I)]
        if arr:
        rails.append({"id": f"comics_pub_{pid}", "title": f"Comics - Publisher: {title_for(pid)}", "items": arr[:18]})
        return jsonify({"rails": rails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

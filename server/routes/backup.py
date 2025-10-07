from flask import Blueprint, jsonify, request, send_file
import os, json, io, time, zipfile

backup_bp = Blueprint('backup', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); STO=os.path.join(ROOT,'storage')
FILES=['config.json','feature_gates.json','rate_presets.json','top_lists_directory.json','rss_feeds.json','rss_auto.json','collections.json','library_index.json']

@backup_bp.route('/api/backup/export')
def export_zip():
    bio=io.BytesIO()
    with zipfile.ZipFile(bio, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            p=os.path.join(STO,f)
            if os.path.exists(p):
                z.write(p, f)
    bio.seek(0)
    return send_file(bio, mimetype='application/zip', as_attachment=True, download_name=f'mediahub_backup_{int(time.time())}.zip')

@backup_bp.route('/api/backup/import', methods=['POST'])
def import_zip():
    # Expect JSON mapping filename -> content
    js=request.get_json(silent=True) or {}
    for k,v in js.items():
        p=os.path.join(STO, k)
        with open(p+'.tmp','w',encoding='utf-8') as fh: fh.write(json.dumps(v, indent=2) if isinstance(v, (dict,list)) else str(v))
        os.replace(p+'.tmp', p)
    return jsonify({'ok': True, 'imported': list(js.keys())})

from flask import Blueprint, jsonify, request, send_file
import os, json, time, shutil, glob
sys_bp = Blueprint('sys', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
LOG=os.path.join(STO,'logs','app.log')
DEPS=os.path.join(STO,'deps.json')
SNAP=os.path.join(STO,'_snapshots')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default
def _save(path, obj):
    tmp=path+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, path)

def _exist_any(paths):
    for p in paths:
        if os.path.exists(p): return p
        return ""

@sys_bp.route('/api/sys/logs_tail')
def logs_tail():
    lines=int(request.args.get('lines') or 200)
    try:
        with open(LOG,'r',encoding='utf-8', errors='ignore') as f:
            data=f.read().splitlines()[-lines:]
    except Exception:
        data=['(no log)']
        return jsonify({'lines': data})


@sys_bp.route('/api/sys/logs_append', methods=['POST'])
def logs_append():
    try:
        js=request.get_json(silent=True) or {}
        msg=js.get('msg','')
        if msg:
        with open(LOG,'a',encoding='utf-8') as f:
        f.write(f"[{int(time.time())}] {msg}\n")
        return jsonify({'ok':True})


        @sys_bp.route('/api/sys/logs_overlay', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def logs_overlay():
    try:
        js=request.get_json(silent=True) or {}
        cfg=_load(CFG,{}); ss=cfg.get('sys_settings',{}); ss['always_log_overlay']=bool(js.get('enabled',False)); cfg['sys_settings']=ss; _save(CFG,cfg)
        return jsonify({'ok':True,'enabled': ss['always_log_overlay']})


        @sys_bp.route('/api/sys/deps_get')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def deps_get():
    try:
        cur=_load(DEPS, {"ffmpeg":{"installed":False,"path":""},"7zip":{"installed":False,"path":""}})
        # probe common paths
        ff=_exist_any([cur['ffmpeg'].get('path',''), '/usr/bin/ffmpeg','/usr/local/bin/ffmpeg','tools/ffmpeg/ffmpeg','tools/ffmpeg/ffmpeg.exe'])
        sz=_exist_any([cur['7zip'].get('path',''), '/usr/bin/7z','/usr/local/bin/7z','tools/7zip/7z','tools/7zip/7z.exe'])
        cur['ffmpeg']['installed']=bool(ff); cur['ffmpeg']['path']=ff or cur['ffmpeg'].get('path','')
        cur['7zip']['installed']=bool(sz); cur['7zip']['path']=sz or cur['7zip'].get('path','')
        _save(DEPS, cur)
        return jsonify(cur)


        @sys_bp.route('/api/sys/deps_locate', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def deps_locate():
    try:
        js=request.get_json(silent=True) or {}
        typ=js.get('type'); path=js.get('path') or ''
        cur=_load(DEPS, {"ffmpeg":{"installed":False,"path":""},"7zip":{"installed":False,"path":""}})
        if typ not in ('ffmpeg','7zip'): return jsonify({'error':'type'}), 400
        cur[typ]['path']=path; cur[typ]['installed']=bool(path)
        _save(DEPS, cur)
        return jsonify({'ok':True, typ: cur[typ]})


        @sys_bp.route('/api/sys/deps_install', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def deps_install():
    try:
        js=request.get_json(silent=True) or {}
        typ=js.get('type'); 
        if typ not in ('ffmpeg','7zip'): return jsonify({'error':'type'}), 400
        # offline placeholder: create tools folder with README
        tdir=os.path.join(ROOT,'tools', 'ffmpeg' if typ=='ffmpeg' else '7zip')
        os.makedirs(tdir, exist_ok=True)
        with open(os.path.join(tdir,'README.txt'),'w',encoding='utf-8') as f:
        f.write('Place the '+('ffmpeg binary' if typ=='ffmpeg' else '7z binary')+' here and update via Settings.')
        cur=_load(DEPS, {"ffmpeg":{"installed":False,"path":""},"7zip":{"installed":False,"path":""}})
        cur[typ]['installed']=False; cur[typ]['path']=tdir
        _save(DEPS, cur)
        return jsonify({'ok':True, 'path': tdir})


        @sys_bp.route('/api/sys/snapshot', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def snapshot():
    try:
        js=request.get_json(silent=True) or {}
        name=js.get('name') or ('snap_'+str(int(time.time())))
        dest=os.path.join(SNAP, name)
        os.makedirs(dest, exist_ok=True)
        keep=['config.json','ui_rails.json','collections.json','collections_refresh.json','collections_import_presets.json','downloader_queue.json','downloader_presets.json','session_stats.json','rd_links.json','reader_prefs.json','play_state.json','wanted.json','completion_hooks.json']
        for k in keep:
        src=os.path.join(STO,k)
        if os.path.exists(src): shutil.copy2(src, os.path.join(dest,k))
        return jsonify({'ok':True,'snapshot': name})


        @sys_bp.route('/api/sys/restore', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def restore():
    try:
        js=request.get_json(silent=True) or {}
        name=js.get('name') or ''
        src=os.path.join(SNAP, name)
        if not (name and os.path.isdir(src)): return jsonify({'error':'not found'}), 404
        for f in os.listdir(src):
        shutil.copy2(os.path.join(src,f), os.path.join(STO,f))
        return jsonify({'ok':True})


        @sys_bp.route('/api/settings/export')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def settings_export():
    os.makedirs(os.path.join(STO,'exports'), exist_ok=True)
    files={}
    for fn in os.listdir(STO):
        if fn.endswith('.json') and not fn.startswith('_'):
            try:
                files[fn]=json.load(open(os.path.join(STO,fn),'r',encoding='utf-8'))
            except Exception: pass
    payload={'exported_at': int(time.time()), 'files': files}
    out=os.path.join(STO,'exports', f"settings_{int(time.time())}.json")
    json.dump(payload, open(out,'w',encoding='utf-8'), indent=2)
                return jsonify({'ok':True,'file': out})


@sys_bp.route('/api/settings/import', methods=['POST'])
def settings_import():
    js=request.get_json(silent=True) or {}
    files=js.get('files') or {}
    for k,v in files.items():
        try:
            json.dump(v, open(os.path.join(STO,k),'w',encoding='utf-8'), indent=2)
        except Exception: pass
            return jsonify({'ok':True})

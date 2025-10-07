import os, shutil, platform, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..'))
STO  = os.path.join(ROOT, 'storage')
CFG  = os.path.join(STO, 'config.json')

def _load_cfg():
    try:
        import json
        return json.load(open(CFG,'r',encoding='utf-8'))
    except Exception:
        return {}

def which(name):
    return shutil.which(name)

def guess_ffmpeg():
    cfg=_load_cfg(); explicit = (cfg.get('bin') or {}).get('ffmpeg','')
    if explicit and os.path.exists(explicit): return explicit
    cand = [
        os.path.join(ROOT,'bin','ffmpeg.exe'),
        os.path.join(ROOT,'bin','ffmpeg'),
    ]
    for c in cand:
        if os.path.exists(c): return c
    return which('ffmpeg')

def guess_7z():
    cfg=_load_cfg(); explicit = (cfg.get('bin') or {}).get('_7zip','')
    if explicit and os.path.exists(explicit): return explicit
    cand = [
        os.path.join(ROOT,'bin','7z.exe'),
        os.path.join(ROOT,'bin','7za.exe'),
        os.path.join(ROOT,'bin','7zz.exe'),
        os.path.join(ROOT,'bin','7z'),
        os.path.join(ROOT,'bin','7za'),
        os.path.join(ROOT,'bin','7zz'),
    ]
    for c in cand:
        if os.path.exists(c): return c
    for n in ['7z','7za','7zz']:
        p = which(n)
        if p: return p
    return None

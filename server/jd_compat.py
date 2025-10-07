
# Auto-generated JD compatibility shim
# Uses jd_hosts.json to classify URLs and apply simple packagizer-like rules.

import re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "config"
HOSTS = set((json.loads((CONF/"jd_hosts.json").read_text(encoding="utf-8"))).get("hosts", []))

DEFAULT_RULES_PATH = CONF / "packagizer_rules.json"

def load_rules():
    # rules: [{enabled:true, order:0, host:'', contains:'', regex:'', dest:'', pack:'', tags:[], priority:0, limit_kbps:0}]

    if DEFAULT_RULES_PATH.exists():
        return json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    return {"rules":[]}

def save_rules(obj):
    DEFAULT_RULES_PATH.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def classify(url:str):
    host = ""
    m = re.match(r"^[a-z]+://([^/]+)", url, re.I)
    if m: host = m.group(1).lower()
    # reduce subdomains
    parts = host.split(".")
    while len(parts) > 2:
        parts = parts[1:]
    host = ".".join(parts) if host else ""
    cat = "unknown"
    if host in HOSTS:
        cat = "host"
    elif url.startswith("magnet:"):
        cat = "magnet"
    elif url.endswith(".dlc"):
        cat = "container"
    return {"host": host, "category": cat}

def apply_rules(item:dict):
    # apply in order where enabled
    # item: {url, name?, host?}
    rules = sorted([r for r in load_rules().get("rules", []) if r.get('enabled', True)], key=lambda x: int(x.get('order',0)))
    out = item.copy()
    for r in rules:
        # basic rule: if host matches or name contains pattern, set dest/pack/tags
        ok = True
        if r.get("host") and r["host"] != out.get("host"):
            ok = False
        if r.get("contains") and r["contains"].lower() not in (out.get("name") or out.get("url","")).lower():
            ok = False
        if not ok: 
            continue
        for k in ("dest","pack","tags","priority","limit_kbps"):
            if k in r:
                out[k]=r[k]
    # regex support
    for r in rules:
        rgx=r.get('regex');
        if rgx:
            try:
                if not re.search(rgx, out.get('name') or out.get('url','')): continue
            except Exception:
                continue
        for k in ('dest','pack','tags','priority','limit_kbps'):
            if k in r: out[k]=r[k]
    return out

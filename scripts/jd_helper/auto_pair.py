import json, time, sys, os
from pathlib import Path

root = Path(__file__).resolve().parents[2]
cfgp = root / "config" / "myjd.json"
logp = Path(__file__).resolve().parent / "auto_pair.log"

def log(*a):
    with open(logp, "a", encoding="utf-8") as f:
        print(*a, file=f)
    print(*a)

if not cfgp.exists():
    log("myjd.json not found. Set it via /api/jd/config."); sys.exit(1)

cfg = json.loads(cfgp.read_text(encoding="utf-8"))
email = cfg.get("email"); passwd = cfg.get("password"); device = cfg.get("device")
if not (email and passwd):
    log("Missing email/password in myjd.json"); sys.exit(1)

try:
    import myjdapi
except Exception as e:
    log("myjdapi not installed:", e); sys.exit(1)

try:
    jd = myjdapi.Myjdapi()
    jd.connect(email, passwd)
    devs = jd.list_devices() or []
    log("Devices:", [d.get("name") for d in devs])
    if device:
        names = [d.get("name") for d in devs]
        if device in names:
            log("Device present:", device, " - pairing OK")
            sys.exit(0)
        else:
            log("Device", device, "not found. Available:", names)
    else:
        log("No device name specified. Choose one of:", [d.get("name") for d in devs])
except Exception as e:
    log("Auto-pair failed:", e); sys.exit(1)
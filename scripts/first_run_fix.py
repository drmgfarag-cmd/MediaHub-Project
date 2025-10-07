import sys, json
from pathlib import Path
import argparse

root = Path(__file__).resolve().parents[1]
CONFIG = root/"config"
DATA = root/"data"
SERVER = root/"server"

def load_json(p, d=None):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return d if d is not None else {}

def save_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def check_keys():
    kp = CONFIG/"keys.local.json"
    if not kp.exists():
        print("WARN: config\\keys.local.json not found. Run scripts\\set_keys.cmd to add provider keys.")
        return 1
    obj = load_json(kp, {})
    missing = [k for k in ("TMDB_KEY","OMDB_KEY","TVDB_KEY","ANILIST_CLIENT_ID","ANILIST_CLIENT_SECRET","DISCOGS_TOKEN","ACOUSTID_KEY","GOOGLE_BOOKS_KEY","REAL_DEBRID_TOKEN") if not obj.get(k)]
    if missing:
        print("WARN: missing keys ->", ", ".join(missing))
        return 2
    print("OK: keys present")
    return 0

def apply_profiles():
    profp = CONFIG/"profiles"/"UserDefined.json"
    if not profp.exists():
        # write a sane default
        save_json(profp, {
            "name":"UserDefined",
            "rd_filters":{"include_words":["2160p","1080p"],"exclude_words":["sample"],"allow_ext":["mkv","mp4"],"deny_ext":["exe"]},
            "dedupe":{"priority_groups":["CtrlHD","Cytsunee","OFT"],"never_remove":["CtrlHD"],"conditional":[{"remove":"Cytsunee","only_if_present":"CtrlHD"}]}
        })
    # set active config pointers
    cfg = load_json(CONFIG/"config.json", {})
    cfg.setdefault("profiles", {})
    cfg["profiles"]["active_rd_filters"] = "UserDefined"
    cfg["profiles"]["active_dedupe"] = "UserDefined"
    save_json(CONFIG/"config.json", cfg)
    print("OK: applied UserDefined profile to RD filters & Dedupe")

def apply_flags():
    flags = {
      "rd_filters_ui": True,"dedupe_policy_ui": True,"downloader_jd_layout": True,"link_grabber_queue": True,
      "per_host_limits": True,"per_host_throughput": True,"dlc_import": True,"jd_helper": True,"keys_backup_restore": True,
      "smart_collections": True,"hls_profiles": True,"webos_cast": True,"dlna_cast": True,"text_editor_multi_tab": True
    }
    save_json(CONFIG/"feature_flags.json", flags)
    print("OK: feature flags seeded")

def self_tests():
    sys.path.insert(0, str(SERVER))
    import importlib.util
    spec = importlib.util.spec_from_file_location("mh_app", SERVER/"app.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = getattr(mod, "app")
    with app.test_client() as c:
        r = c.post("/self_tests/run")
        print("self_tests:", r.status_code)
        r = c.get("/rules_audit/full")
        print("rules_audit/full:", r.status_code)
    print("OK: self tests + audit kicked")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-keys", action="store_true")
    ap.add_argument("--apply-profiles", action="store_true")
    ap.add_argument("--apply-flags", action="store_true")
    ap.add_argument("--self-tests", action="store_true")
    a = ap.parse_args()
    if a.check_keys: check_keys()
    if a.apply_profiles: apply_profiles()
    if a.apply_flags: apply_flags()
    if a.self_tests: self_tests()
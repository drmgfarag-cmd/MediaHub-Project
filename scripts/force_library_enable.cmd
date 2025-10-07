@echo off
title MediaHub Force Library Surfaces
echo Seeding feature flags and manifest...
python - <<PY
import json, os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
conf = root/'config'
flags = {
  "library_pinned_tiles": True, "library_hierarchy_dock": True, "library_card_context": True,
  "library_rebuild_index": True, "library_integrity_scan": True,
  "rd_filters_ui": True, "dedupe_policy_ui": True, "downloader_jd_layout": True, "link_grabber_queue": True,
  "per_host_limits": True, "per_host_throughput": True, "dlc_import": True, "jd_helper": True, "keys_backup_restore": True,
  "smart_collections": True, "hls_profiles": True, "webos_cast": True, "dlna_cast": True, "text_editor_multi_tab": True
}
(conf/'feature_flags.json').write_text(json.dumps(flags, indent=2), encoding='utf-8')
manifest = {
  "required_surfaces":[
    "library:pinned_subcategories","library:hierarchy_dock","library:card_context_menu",
    "library:toolbar:rebuild_index","library:toolbar:integrity_scan"
  ],
  "pillars":["Movies","TV","Books","Audio"]
}
(conf/'feature_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('OK: flags + manifest written')
PY
echo Restart the server to reflect changes if needed.
pause >nul
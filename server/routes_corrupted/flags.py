from flask import Blueprint, jsonify, request
import os, json
from .security import require_api_key, rate_limited

flags_bp = Blueprint('flags', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
FLAGS = os.path.join(STO, 'feature_flags.json')

DEFAULT = {
  "enable_logs_tail": true,
  "enable_package_grouping": true,
  "enable_per_row_progress": True,
  "enable_bandwidth_limiter": true,
  "enable_linkgrabber_wizard": true,
  "enable_metrics_local": true,
  "enable_status_footer": True,
  "enable_downloader": true,
  "enable_rss": true,
  "enable_download_drawer": true   # Gate: /api/logs/tail is inactive unless set True
,
  "enable_polish_pack": true
,
  "enable_bundles_polish": true
,
  "enable_rails_polish": true
,
  "enable_real_debrid": true
,
  "enable_native_downloader": true
,
  "enable_rss_to_rd": true
,
  "enable_immersion_hero": true
,
  "enable_collections_import": true
,
  "enable_collections_timelines": true
,
  "enable_pinned_subcats": true
,
  "enable_top50_lists": true
,
  "enable_inline_bundles_table": true
,
  "enable_table_extra_columns": true
,
  "enable_row_progress_in_table": true
,
  "enable_rss_scheduler": true
,
  "enable_rd_adv_prefs": true
,
  "enable_rd_cloud_pull": true
,
  "enable_clipboard_catcher": true
,
  "enable_footer_graph": true
,
  "enable_aria2": true
,
  "enable_qbittorrent": true
,
  "enable_kids_age_rails": true
,
  "enable_sort_editor": true
,
  "enable_dedupe_editor": true
,
  "enable_tree_view": true
}

def _load():
    try:
        with open(FLAGS,'r',encoding='utf-8') as f: 
        d=json.load(f); return {**DEFAULT, **d,
  "enable_polish_pack": true
,
  "enable_bundles_polish": true
,
  "enable_rails_polish": true
,
  "enable_real_debrid": true
,
  "enable_native_downloader": true
,
  "enable_rss_to_rd": true
,
  "enable_immersion_hero": true
,
  "enable_collections_import": true
,
  "enable_collections_timelines": true
,
  "enable_pinned_subcats": true
,
  "enable_top50_lists": true
,
  "enable_inline_bundles_table": true
,
  "enable_table_extra_columns": true
,
  "enable_row_progress_in_table": true
,
  "enable_rss_scheduler": true
,
  "enable_rd_adv_prefs": true
,
  "enable_rd_cloud_pull": true
,
  "enable_clipboard_catcher": true
,
  "enable_footer_graph": true
,
  "enable_aria2": true
,
  "enable_qbittorrent": true
,
  "enable_kids_age_rails": true
,
  "enable_sort_editor": true
,
  "enable_dedupe_editor": true
,
  "enable_tree_view": true
}
    except Exception:
        return DEFAULT

def _save(d):
    os.makedirs(STO, exist_ok=True)
    tmp=FLAGS+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(d,f,indent=2)
    os.replace(tmp, FLAGS)

@flags_bp.route('/api/flags', methods=['GET'])
def get_flags():
    return jsonify(_load())

# DUPLICATE REMOVED: @flags_bp.route('/api/flags', methods=['POST'])
def create_flags():
    """Create Flags"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_flags():
    """Create Flags"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: @require_api_key
# DUPLICATE REMOVED: @rate_limited
# DUPLICATE REMOVED: def set_flags():
    d=request.get_json(silent=True) or {,
  "enable_polish_pack": true
,
  "enable_bundles_polish": true
,
  "enable_rails_polish": true
,
  "enable_real_debrid": true
,
  "enable_native_downloader": true
,
  "enable_rss_to_rd": true
,
  "enable_immersion_hero": true
,
  "enable_collections_import": true
,
  "enable_collections_timelines": true
,
  "enable_pinned_subcats": true
,
  "enable_top50_lists": true
,
  "enable_inline_bundles_table": true
,
  "enable_table_extra_columns": true
,
  "enable_row_progress_in_table": true
,
  "enable_rss_scheduler": true
,
  "enable_rd_adv_prefs": true
,
  "enable_rd_cloud_pull": true
,
  "enable_clipboard_catcher": true
,
  "enable_footer_graph": true
,
  "enable_aria2": true
,
  "enable_qbittorrent": true
,
  "enable_kids_age_rails": true
,
  "enable_sort_editor": true
,
  "enable_dedupe_editor": true
,
  "enable_tree_view": true
}
    cur=_load(); cur.update({k:v for k,v in d.items() if k in DEFAULT,
  "enable_polish_pack": true
,
  "enable_bundles_polish": true
,
  "enable_rails_polish": true
,
  "enable_real_debrid": true
,
  "enable_native_downloader": true
,
  "enable_rss_to_rd": true
,
  "enable_immersion_hero": true
,
  "enable_collections_import": true
,
  "enable_collections_timelines": true
,
  "enable_pinned_subcats": true
,
  "enable_top50_lists": true
,
  "enable_inline_bundles_table": true
,
  "enable_table_extra_columns": true
,
  "enable_row_progress_in_table": true
,
  "enable_rss_scheduler": true
,
  "enable_rd_adv_prefs": true
,
  "enable_rd_cloud_pull": true
,
  "enable_clipboard_catcher": true
,
  "enable_footer_graph": true
,
  "enable_aria2": true
,
  "enable_qbittorrent": true
,
  "enable_kids_age_rails": true
,
  "enable_sort_editor": true
,
  "enable_dedupe_editor": true
,
  "enable_tree_view": true
})
    _save(cur); return jsonify({"ok":True,"flags":cur,
  "enable_polish_pack": true
,
  "enable_bundles_polish": true
,
  "enable_rails_polish": true
,
  "enable_real_debrid": true
,
  "enable_native_downloader": true
,
  "enable_rss_to_rd": true
,
  "enable_immersion_hero": true
,
  "enable_collections_import": true
,
  "enable_collections_timelines": true
,
  "enable_pinned_subcats": true
,
  "enable_top50_lists": true
,
  "enable_inline_bundles_table": true
,
  "enable_table_extra_columns": true
,
  "enable_row_progress_in_table": true
,
  "enable_rss_scheduler": true
,
  "enable_rd_adv_prefs": true
,
  "enable_rd_cloud_pull": true
,
  "enable_clipboard_catcher": true
,
  "enable_footer_graph": true
,
  "enable_aria2": true
,
  "enable_qbittorrent": true
,
  "enable_kids_age_rails": true
,
  "enable_sort_editor": true
,
  "enable_dedupe_editor": true
,
  "enable_tree_view": true
})
# Route Registration Checklist

**Total Routes:** 170  
**Currently Registered:** 35  
**To Register:** 146  

---

## CRITICAL Routes (11 to register)

- [ ] **audio_enhanced.py**
  - Import: `from routes.audio_enhanced import audio_enhanced_bp`
  - Register: `app.register_blueprint(audio_enhanced_bp, url_prefix='/audio-enhanced')`

- [ ] **audio_player.py**
  - Import: `from routes.audio_player import ap_bp`
  - Register: `app.register_blueprint(ap_bp, url_prefix='/audio')`

- [ ] **audio_playlists.py**
  - Import: `from routes.audio_playlists import mix_bp`
  - Register: `app.register_blueprint(mix_bp, url_prefix='/mix')`

- [ ] **audio_replaygain.py**
  - Import: `from routes.audio_replaygain import rg_bp`
  - Register: `app.register_blueprint(rg_bp, url_prefix='/rg')`

- [ ] **audio_settings.py**
  - Import: `from routes.audio_settings import aset_bp`
  - Register: `app.register_blueprint(aset_bp, url_prefix='/aset')`

- [ ] **comics_enhanced.py**
  - Import: `from routes.comics_enhanced import comics_enhanced_bp`
  - Register: `app.register_blueprint(comics_enhanced_bp, url_prefix='/comics-enhanced')`

- [ ] **discovery.py**
  - Import: `from routes.discovery import disc_bp`
  - Register: `app.register_blueprint(disc_bp, url_prefix='/disc')`

- [ ] **discovery_advanced.py**
  - Import: `from routes.discovery_advanced import discovery_advanced_bp`
  - Register: `app.register_blueprint(discovery_advanced_bp, url_prefix='/discovery-advanced')`

- [ ] **mobile_smart_rails_api.py**
  - Import: `from routes.mobile_smart_rails_api import mobile_rails_bp`
  - Register: `app.register_blueprint(mobile_rails_bp, url_prefix='/mobile-smart-rails')`

- [ ] **toplists.py**
  - Import: `from routes.toplists import tl_bp`
  - Register: `app.register_blueprint(tl_bp, url_prefix='/toplists')`

- [ ] **toplists_directory.py**
  - Import: `from routes.toplists_directory import td_bp`
  - Register: `app.register_blueprint(td_bp, url_prefix='/toplists-directory')`

## MEDIA Routes (15 to register)

- [ ] **collections.py**
  - Import: `from routes.collections import col_bp`
  - Register: `app.register_blueprint(col_bp, url_prefix='/collections')`

- [ ] **collections_api.py**
  - Import: `from routes.collections_api import coll_bp`
  - Register: `app.register_blueprint(coll_bp, url_prefix='/coll')`

- [ ] **collections_import.py**
  - Import: `from routes.collections_import import coll_bp`
  - Register: `app.register_blueprint(coll_bp, url_prefix='/collections-import')`

- [ ] **collections_manage.py**
  - Import: `from routes.collections_manage import col_bp`
  - Register: `app.register_blueprint(col_bp, url_prefix='/cols')`

- [ ] **collections_timeline.py**
  - Import: `from routes.collections_timeline import timeline_bp`
  - Register: `app.register_blueprint(timeline_bp, url_prefix='/collections-timeline')`

- [ ] **library.py**
  - Import: `from routes.library import lib_bp`
  - Register: `app.register_blueprint(lib_bp, url_prefix='/library')`

- [ ] **library_local.py**
  - Import: `from routes.library_local import lib_bp`
  - Register: `app.register_blueprint(lib_bp, url_prefix='/library-local')`

- [ ] **library_scan.py**
  - Import: `from routes.library_scan import scan_bp`
  - Register: `app.register_blueprint(scan_bp, url_prefix='/scan')`

- [ ] **media_collections.py**
  - Import: `from routes.media_collections import col_bp`
  - Register: `app.register_blueprint(col_bp, url_prefix='/collections')`

- [ ] **playlists.py**
  - Import: `from routes.playlists import pl_bp`
  - Register: `app.register_blueprint(pl_bp, url_prefix='/pl')`

- [ ] **reader.py**
  - Import: `from routes.reader import reader_bp`
  - Register: `app.register_blueprint(reader_bp, url_prefix='/reader')`

- [ ] **reader_cbz.py**
  - Import: `from routes.reader_cbz import cbz_bp`
  - Register: `app.register_blueprint(cbz_bp, url_prefix='/cbz-reader')`

- [ ] **reader_extract.py**
  - Import: `from routes.reader_extract import readerx_bp`
  - Register: `app.register_blueprint(readerx_bp, url_prefix='/readerx')`

- [ ] **smartplaylists.py**
  - Import: `from routes.smartplaylists import sp_bp`
  - Register: `app.register_blueprint(sp_bp, url_prefix='/smartpl')`

- [ ] **stream.py**
  - Import: `from routes.stream import stream_bp`
  - Register: `app.register_blueprint(stream_bp, url_prefix='/stream')`

## AUTOMATION Routes (13 to register)

- [ ] **advanced_downloader_api.py**
  - Import: `from routes.advanced_downloader_api import advanced_dl_bp`
  - Register: `app.register_blueprint(advanced_dl_bp, url_prefix='/advanced-downloader')`

- [ ] **downloader.py**
  - Import: `from routes.downloader import dl_bp`
  - Register: `app.register_blueprint(dl_bp, url_prefix='/dl')`

- [ ] **downloader_api.py**
  - Import: `from routes.downloader_api import dlx_bp`
  - Register: `app.register_blueprint(dlx_bp, url_prefix='/dlx')`

- [ ] **downloader_enhanced.py**
  - Import: `from routes.downloader_enhanced import downloader_enhanced_bp`
  - Register: `app.register_blueprint(downloader_enhanced_bp, url_prefix='/downloader-enhanced')`

- [ ] **downloader_packages.py**
  - Import: `from routes.downloader_packages import pkg_bp`
  - Register: `app.register_blueprint(pkg_bp, url_prefix='/packages')`

- [ ] **downloader_view.py**
  - Import: `from routes.downloader_view import view_bp`
  - Register: `app.register_blueprint(view_bp, url_prefix='/dlview')`

- [ ] **qbittorrent.py**
  - Import: `from routes.qbittorrent import qb_bp`
  - Register: `app.register_blueprint(qb_bp, url_prefix='/qb')`

- [ ] **rss.py**
  - Import: `from routes.rss import rss_bp`
  - Register: `app.register_blueprint(rss_bp, url_prefix='/rss')`

- [ ] **rss_enhanced.py**
  - Import: `from routes.rss_enhanced import rss_enhanced_bp`
  - Register: `app.register_blueprint(rss_enhanced_bp, url_prefix='/rss-enhanced')`

- [ ] **rss_feeder.py**
  - Import: `from routes.rss_feeder import rss_feeder_bp`
  - Register: `app.register_blueprint(rss_feeder_bp, url_prefix='/rss')`

- [ ] **rss_scheduler.py**
  - Import: `from routes.rss_scheduler import sched_bp`
  - Register: `app.register_blueprint(sched_bp, url_prefix='/rss-sched')`

- [ ] **scheduler.py**
  - Import: `from routes.scheduler import sched_bp`
  - Register: `app.register_blueprint(sched_bp, url_prefix='/sched')`

- [ ] **torrent_inspector.py**
  - Import: `from routes.torrent_inspector import torrent_inspector_bp`
  - Register: `app.register_blueprint(torrent_inspector_bp, url_prefix='/torrent-inspector')`

## UI Routes (8 to register)

- [ ] **advanced_text_editor.py**
  - Import: `from routes.advanced_text_editor import advanced_editor_bp`
  - Register: `app.register_blueprint(advanced_editor_bp, url_prefix='/advanced-text-editor')`

- [ ] **dedupe_editor.py**
  - Import: `from routes.dedupe_editor import dedupe_bp`
  - Register: `app.register_blueprint(dedupe_bp, url_prefix='/dedupe')`

- [ ] **editor.py**
  - Import: `from routes.editor import editor_bp`
  - Register: `app.register_blueprint(editor_bp, url_prefix='/ed')`

- [ ] **editor_pro.py**
  - Import: `from routes.editor_pro import ed_bp`
  - Register: `app.register_blueprint(ed_bp, url_prefix='/ed')`

- [ ] **editor_tabs.py**
  - Import: `from routes.editor_tabs import tb_bp`
  - Register: `app.register_blueprint(tb_bp, url_prefix='/tabs')`

- [ ] **sort_editor.py**
  - Import: `from routes.sort_editor import sort_bp`
  - Register: `app.register_blueprint(sort_bp, url_prefix='/sort')`

- [ ] **text_editor_enhanced.py**
  - Import: `from routes.text_editor_enhanced import text_editor_enhanced_bp`
  - Register: `app.register_blueprint(text_editor_enhanced_bp, url_prefix='/text-editor-enhanced')`

- [ ] **ui.py**
  - Import: `from routes.ui import ui_bp`
  - Register: `app.register_blueprint(ui_bp, url_prefix='/ui')`

## TOOLS Routes (5 to register)

- [ ] **batchrename.py**
  - Import: `from routes.batchrename import br_bp`
  - Register: `app.register_blueprint(br_bp, url_prefix='/br')`

- [ ] **db_tools.py**
  - Import: `from routes.db_tools import db_bp`
  - Register: `app.register_blueprint(db_bp, url_prefix='/db')`

- [ ] **organizer.py**
  - Import: `from routes.organizer import org_bp`
  - Register: `app.register_blueprint(org_bp, url_prefix='/org')`

- [ ] **renamer_advanced.py**
  - Import: `from routes.renamer_advanced import renamer_advanced_bp`
  - Register: `app.register_blueprint(renamer_advanced_bp, url_prefix='/renamer-advanced')`

- [ ] **tools.py**
  - Import: `from routes.tools import tools_bp`
  - Register: `app.register_blueprint(tools_bp, url_prefix='/tools')`

## TESTING Routes (2 to register)

- [ ] **diagnostics.py**
  - Import: `from routes.diagnostics import diag_bp`
  - Register: `app.register_blueprint(diag_bp, url_prefix='/diag')`

- [ ] **selftest.py**
  - Import: `from routes.selftest import selftest_bp`
  - Register: `app.register_blueprint(selftest_bp, url_prefix='/selftest')`

## OTHER Routes (92 to register)

- [ ] **accounts.py**
  - Import: `from routes.accounts import acct_bp`
  - Register: `app.register_blueprint(acct_bp, url_prefix='/accounts')`

- [ ] **adv_search.py**
  - Import: `from routes.adv_search import adv_bp`
  - Register: `app.register_blueprint(adv_bp, url_prefix='/adv')`

- [ ] **auto_explain.py**
  - Import: `from routes.auto_explain import autoex_bp`
  - Register: `app.register_blueprint(autoex_bp, url_prefix='/autoex')`

- [ ] **auto_select.py**
  - Import: `from routes.auto_select import auto_bp`
  - Register: `app.register_blueprint(auto_bp, url_prefix='/auto')`

- [ ] **backup.py**
  - Import: `from routes.backup import backup_bp`
  - Register: `app.register_blueprint(backup_bp, url_prefix='/backup')`

- [ ] **books_enhanced.py**
  - Import: `from routes.books_enhanced import books_enhanced_bp`
  - Register: `app.register_blueprint(books_enhanced_bp, url_prefix='/books-enhanced')`

- [ ] **captcha_prefs.py**
  - Import: `from routes.captcha_prefs import cap_bp`
  - Register: `app.register_blueprint(cap_bp, url_prefix='/captcha')`

- [ ] **catalogs.py**
  - Import: `from routes.catalogs import catalogs_bp`
  - Register: `app.register_blueprint(catalogs_bp, url_prefix='/catalogs')`

- [ ] **config.py**
  - Import: `from routes.config import cfg_bp`
  - Register: `app.register_blueprint(cfg_bp, url_prefix='/config')`

- [ ] **connectors.py**
  - Import: `from routes.connectors import conn_bp`
  - Register: `app.register_blueprint(conn_bp, url_prefix='/connectors')`

- [ ] **curations.py**
  - Import: `from routes.curations import curations_bp`
  - Register: `app.register_blueprint(curations_bp, url_prefix='/curations')`

- [ ] **dashboard_custom.py**
  - Import: `from routes.dashboard_custom import dashboard_custom_bp`
  - Register: `app.register_blueprint(dashboard_custom_bp, url_prefix='/dashboard-custom')`

- [ ] **debrid.py**
  - Import: `from routes.debrid import debrid_bp`
  - Register: `app.register_blueprint(debrid_bp, url_prefix='/debrid')`

- [ ] **dedupe.py**
  - Import: `from routes.dedupe import dd_bp`
  - Register: `app.register_blueprint(dd_bp, url_prefix='/dd')`

- [ ] **dl_columns.py**
  - Import: `from routes.dl_columns import col_bp`
  - Register: `app.register_blueprint(col_bp, url_prefix='/col')`

- [ ] **enhanced_media_management.py**
  - Import: `from routes.enhanced_media_management import enhanced_media_bp`
  - Register: `app.register_blueprint(enhanced_media_bp, url_prefix='/enhanced-media')`

- [ ] **export_import.py**
  - Import: `from routes.export_import import ei_bp`
  - Register: `app.register_blueprint(ei_bp, url_prefix='/export-import')`

- [ ] **faceted_database.py**
  - Import: `from routes.faceted_database import faceted_db_bp`
  - Register: `app.register_blueprint(faceted_db_bp, url_prefix='/faceted-db')`

- [ ] **features.py**
  - Import: `from routes.features import feat_bp`
  - Register: `app.register_blueprint(feat_bp, url_prefix='/feat')`

- [ ] **feeds.py**
  - Import: `from routes.feeds import feeds_bp`
  - Register: `app.register_blueprint(feeds_bp, url_prefix='/feeds')`

- [ ] **findreplace.py**
  - Import: `from routes.findreplace import fr_bp`
  - Register: `app.register_blueprint(fr_bp, url_prefix='/findrep')`

- [ ] **flags.py**
  - Import: `from routes.flags import flags_bp`
  - Register: `app.register_blueprint(flags_bp, url_prefix='/flags')`

- [ ] **foundation.py**
  - Import: `from routes.foundation import foundation_bp`
  - Register: `app.register_blueprint(foundation_bp, url_prefix='/foundation')`

- [ ] **guard_enforcer.py**
  - Import: `from routes.guard_enforcer import guard_bp`
  - Register: `app.register_blueprint(guard_bp, url_prefix='/guard')`

- [ ] **hash.py**
  - Import: `from routes.hash import hash_bp`
  - Register: `app.register_blueprint(hash_bp, url_prefix='/hash')`

- [ ] **health.py**
  - Import: `from routes.health import health_bp`
  - Register: `app.register_blueprint(health_bp, url_prefix='/health')`

- [ ] **hls_mgr.py**
  - Import: `from routes.hls_mgr import hls_bp`
  - Register: `app.register_blueprint(hls_bp, url_prefix='/hls')`

- [ ] **home_pins.py**
  - Import: `from routes.home_pins import pins_bp`
  - Register: `app.register_blueprint(pins_bp, url_prefix='/home-pins')`

- [ ] **hooks.py**
  - Import: `from routes.hooks import hooks_bp`
  - Register: `app.register_blueprint(hooks_bp, url_prefix='/hooks')`

- [ ] **i18n.py**
  - Import: `from routes.i18n import i18n_bp`
  - Register: `app.register_blueprint(i18n_bp, url_prefix='/i18n')`

- [ ] **indexing.py**
  - Import: `from routes.indexing import idx_bp`
  - Register: `app.register_blueprint(idx_bp, url_prefix='/idx')`

- [ ] **integrations.py**
  - Import: `from routes.integrations import integ_bp`
  - Register: `app.register_blueprint(integ_bp, url_prefix='/integrations')`

- [ ] **jobs.py**
  - Import: `from routes.jobs import jobs_bp`
  - Register: `app.register_blueprint(jobs_bp, url_prefix='/jobs')`

- [ ] **kids.py**
  - Import: `from routes.kids import kids_bp`
  - Register: `app.register_blueprint(kids_bp, url_prefix='/kids')`

- [ ] **kids_parental_controls.py**
  - Import: `from routes.kids_parental_controls import kids_parental_controls_bp`
  - Register: `app.register_blueprint(kids_parental_controls_bp, url_prefix='/kids-parental-controls')`

- [ ] **libsearch.py**
  - Import: `from routes.libsearch import libsearch_bp`
  - Register: `app.register_blueprint(libsearch_bp, url_prefix='/libsearch')`

- [ ] **limits.py**
  - Import: `from routes.limits import lim_bp`
  - Register: `app.register_blueprint(lim_bp, url_prefix='/limits')`

- [ ] **link_grabber.py**
  - Import: `from routes.link_grabber import link_grabber_bp`
  - Register: `app.register_blueprint(link_grabber_bp, url_prefix='/link-grabber')`

- [ ] **linkgrabber_templates.py**
  - Import: `from routes.linkgrabber_templates import tmpl_bp`
  - Register: `app.register_blueprint(tmpl_bp, url_prefix='/link-templates')`

- [ ] **lists.py**
  - Import: `from routes.lists import lists_bp`
  - Register: `app.register_blueprint(lists_bp, url_prefix='/lists')`

- [ ] **lists_catalog.py**
  - Import: `from routes.lists_catalog import cat_bp`
  - Register: `app.register_blueprint(cat_bp, url_prefix='/cat')`

- [ ] **logs.py**
  - Import: `from routes.logs import logs_bp`
  - Register: `app.register_blueprint(logs_bp, url_prefix='/logs')`

- [ ] **lyrics.py**
  - Import: `from routes.lyrics import lyr_bp`
  - Register: `app.register_blueprint(lyr_bp, url_prefix='/lyrics')`

- [ ] **metadata.py**
  - Import: `from routes.metadata import md_bp`
  - Register: `app.register_blueprint(md_bp, url_prefix='/md')`

- [ ] **metrics_speed.py**
  - Import: `from routes.metrics_speed import sp_bp`
  - Register: `app.register_blueprint(sp_bp, url_prefix='/metrics-speed')`

- [ ] **missing.py**
  - Import: `from routes.missing import miss_bp`
  - Register: `app.register_blueprint(miss_bp, url_prefix='/miss')`

- [ ] **monaco_mgr.py**
  - Import: `from routes.monaco_mgr import monaco_bp`
  - Register: `app.register_blueprint(monaco_bp, url_prefix='/monaco')`

- [ ] **movies_enhanced.py**
  - Import: `from routes.movies_enhanced import movies_enhanced_bp`
  - Register: `app.register_blueprint(movies_enhanced_bp, url_prefix='/movies-enhanced')`

- [ ] **music_queue.py**
  - Import: `from routes.music_queue import mq_bp`
  - Register: `app.register_blueprint(mq_bp, url_prefix='/music-queue')`

- [ ] **opds.py**
  - Import: `from routes.opds import opds_bp`
  - Register: `app.register_blueprint(opds_bp, url_prefix='/opds')`

- [ ] **opds_books.py**
  - Import: `from routes.opds_books import opds_books_bp`
  - Register: `app.register_blueprint(opds_books_bp, url_prefix='/opds-books')`

- [ ] **packages.py**
  - Import: `from routes.packages import packages_bp`
  - Register: `app.register_blueprint(packages_bp, url_prefix='/packages')`

- [ ] **pinboard.py**
  - Import: `from routes.pinboard import pin_bp`
  - Register: `app.register_blueprint(pin_bp, url_prefix='/pin')`

- [ ] **pinned.py**
  - Import: `from routes.pinned import pin_bp`
  - Register: `app.register_blueprint(pin_bp, url_prefix='/pin')`

- [ ] **pins.py**
  - Import: `from routes.pins import pins_bp`
  - Register: `app.register_blueprint(pins_bp, url_prefix='/pins')`

- [ ] **presets.py**
  - Import: `from routes.presets import presets_bp`
  - Register: `app.register_blueprint(presets_bp, url_prefix='/presets')`

- [ ] **profile_management.py**
  - Import: `from routes.profile_management import profile_management_bp`
  - Register: `app.register_blueprint(profile_management_bp, url_prefix='/profile-management')`

- [ ] **profiles.py**
  - Import: `from routes.profiles import prof_bp`
  - Register: `app.register_blueprint(prof_bp, url_prefix='/prof')`

- [ ] **queue.py**
  - Import: `from routes.queue import q_bp`
  - Register: `app.register_blueprint(q_bp, url_prefix='/queue')`

- [ ] **queue_combined.py**
  - Import: `from routes.queue_combined import combo_bp`
  - Register: `app.register_blueprint(combo_bp, url_prefix='/queue-combo')`

- [ ] **queue_meta.py**
  - Import: `from routes.queue_meta import qm_bp`
  - Register: `app.register_blueprint(qm_bp, url_prefix='/queue-meta')`

- [ ] **rails.py**
  - Import: `from routes.rails import rails_bp`
  - Register: `app.register_blueprint(rails_bp, url_prefix='/rails')`

- [ ] **rails_extra.py**
  - Import: `from routes.rails_extra import extra_bp`
  - Register: `app.register_blueprint(extra_bp, url_prefix='/rails-extra')`

- [ ] **rails_polish.py**
  - Import: `from routes.rails_polish import rails_bp`
  - Register: `app.register_blueprint(rails_bp, url_prefix='/rails-polish')`

- [ ] **rd.py**
  - Import: `from routes.rd import rd_bp`
  - Register: `app.register_blueprint(rd_bp, url_prefix='/rd')`

- [ ] **rd_analyze.py**
  - Import: `from routes.rd_analyze import ra_bp`
  - Register: `app.register_blueprint(ra_bp, url_prefix='/ra')`

- [ ] **rd_cloudpull.py**
  - Import: `from routes.rd_cloudpull import cloud_bp`
  - Register: `app.register_blueprint(cloud_bp, url_prefix='/rd-cloudpull')`

- [ ] **rd_dedup.py**
  - Import: `from routes.rd_dedup import dedup_bp`
  - Register: `app.register_blueprint(dedup_bp, url_prefix='/rd-dedup')`

- [ ] **rd_inbox.py**
  - Import: `from routes.rd_inbox import in_bp`
  - Register: `app.register_blueprint(in_bp, url_prefix='/inbox')`

- [ ] **rd_manager.py**
  - Import: `from routes.rd_manager import rd_bp`
  - Register: `app.register_blueprint(rd_bp, url_prefix='/rd')`

- [ ] **rd_manager_enhanced.py**
  - Import: `from routes.rd_manager_enhanced import rd_manager_enhanced_bp`
  - Register: `app.register_blueprint(rd_manager_enhanced_bp, url_prefix='/rd-manager-enhanced')`

- [ ] **realdebrid.py**
  - Import: `from routes.realdebrid import rd_bp`
  - Register: `app.register_blueprint(rd_bp, url_prefix='/rd')`

- [ ] **recipes.py**
  - Import: `from routes.recipes import recipes_bp`
  - Register: `app.register_blueprint(recipes_bp, url_prefix='/recipes')`

- [ ] **rules_audit.py**
  - Import: `from routes.rules_audit import rules_audit_bp`
  - Register: `app.register_blueprint(rules_audit_bp, url_prefix='/rules-audit')`

- [ ] **scoring_engine.py**
  - Import: `from routes.scoring_engine import scoring_bp`
  - Register: `app.register_blueprint(scoring_bp, url_prefix='/scoring')`

- [ ] **secrets.py**
  - Import: `from routes.secrets import secrets_bp`
  - Register: `app.register_blueprint(secrets_bp, url_prefix='/secrets')`

- [ ] **security.py**
  - Import: `from routes.security import security_bp`
  - Register: `app.register_blueprint(security_bp, url_prefix='/security')`

- [ ] **smart_rails.py**
  - Import: `from routes.smart_rails import sr_bp`
  - Register: `app.register_blueprint(sr_bp, url_prefix='/smart')`

- [ ] **smart_rails_api.py**
  - Import: `from routes.smart_rails_api import smart_rails_bp`
  - Register: `app.register_blueprint(smart_rails_bp, url_prefix='/smart-rails-api')`

- [ ] **stubs_extra.py**
  - Import: `from routes.stubs_extra import stubs_bp`
  - Register: `app.register_blueprint(stubs_bp, url_prefix='/stubs-extra')`

- [ ] **subtitles_advanced.py**
  - Import: `from routes.subtitles_advanced import subtitles_advanced_bp`
  - Register: `app.register_blueprint(subtitles_advanced_bp, url_prefix='/subtitles-advanced')`

- [ ] **support_pack.py**
  - Import: `from routes.support_pack import support_bp`
  - Register: `app.register_blueprint(support_bp, url_prefix='/support')`

- [ ] **system.py**
  - Import: `from routes.system import sys_bp`
  - Register: `app.register_blueprint(sys_bp, url_prefix='/sys')`

- [ ] **taxonomy.py**
  - Import: `from routes.taxonomy import tax_bp`
  - Register: `app.register_blueprint(tax_bp, url_prefix='/taxonomy')`

- [ ] **thumbs.py**
  - Import: `from routes.thumbs import thumbs_bp`
  - Register: `app.register_blueprint(thumbs_bp, url_prefix='/thumbs')`

- [ ] **timeline.py**
  - Import: `from routes.timeline import tl_bp`
  - Register: `app.register_blueprint(tl_bp, url_prefix='/tl')`

- [ ] **timelines.py**
  - Import: `from routes.timelines import tl_bp`
  - Register: `app.register_blueprint(tl_bp, url_prefix='/tl')`

- [ ] **trailer.py**
  - Import: `from routes.trailer import tr_bp`
  - Register: `app.register_blueprint(tr_bp, url_prefix='/trailer')`

- [ ] **tree_view.py**
  - Import: `from routes.tree_view import tree_bp`
  - Register: `app.register_blueprint(tree_bp, url_prefix='/tree')`

- [ ] **tv_shows_enhanced.py**
  - Import: `from routes.tv_shows_enhanced import tv_shows_enhanced_bp`
  - Register: `app.register_blueprint(tv_shows_enhanced_bp, url_prefix='/tv-shows-enhanced')`

- [ ] **views_counts.py**
  - Import: `from routes.views_counts import vc_bp`
  - Register: `app.register_blueprint(vc_bp, url_prefix='/views-counts')`

- [ ] **wanted.py**
  - Import: `from routes.wanted import want_bp`
  - Register: `app.register_blueprint(want_bp, url_prefix='/want')`

---

## Already Registered

- [x] advanced_dedupe_api.py
- [x] advanced_ui.py
- [x] aria2.py
- [x] casting_integration.py
- [x] core_infrastructure_api.py
- [x] cross_references.py
- [x] downloader_rd_api.py
- [x] editor_plugins.py
- [x] frontend_apis.py
- [x] media_management_api.py
- [x] media_management_golden_api.py
- [x] mediahub_home_api.py
- [x] metadata_export.py
- [x] mobile_streaming.py
- [x] rd_parser.py
- [x] rss_automation.py
- [x] stream_audio_norm.py
- [x] synopsis_overlay.py
- [x] tags_system.py
- [x] text_editor_api.py
- [x] ui_features_api.py
- [x] ui_features_v57_api.py
- [x] uiux_golden_api.py
- [x] visual_search.py

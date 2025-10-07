# Code to add to app.py
# Add these imports at the top of the file

# IMPORTS
from routes.accounts import acct_bp
from routes.adv_search import adv_bp
from routes.advanced_downloader_api import advanced_dl_bp
from routes.advanced_text_editor import advanced_editor_bp
from routes.audio_enhanced import audio_enhanced_bp
from routes.audio_player import ap_bp
from routes.audio_playlists import mix_bp
from routes.audio_replaygain import rg_bp
from routes.audio_settings import aset_bp
from routes.auto_explain import autoex_bp
from routes.auto_select import auto_bp
from routes.backup import backup_bp
from routes.batchrename import br_bp
from routes.books_enhanced import books_enhanced_bp
from routes.captcha_prefs import cap_bp
from routes.catalogs import catalogs_bp
from routes.collections import col_bp
from routes.collections_api import coll_bp
from routes.collections_import import coll_bp
from routes.collections_manage import col_bp
from routes.collections_timeline import timeline_bp
from routes.comics_enhanced import comics_enhanced_bp
from routes.config import cfg_bp
from routes.connectors import conn_bp
from routes.curations import curations_bp
from routes.dashboard_custom import dashboard_custom_bp
from routes.db_tools import db_bp
from routes.debrid import debrid_bp
from routes.dedupe import dd_bp
from routes.dedupe_editor import dedupe_bp
from routes.diagnostics import diag_bp
from routes.discovery import disc_bp
from routes.discovery_advanced import discovery_advanced_bp
from routes.dl_columns import col_bp
from routes.downloader import dl_bp
from routes.downloader_api import dlx_bp
from routes.downloader_enhanced import downloader_enhanced_bp
from routes.downloader_packages import pkg_bp
from routes.downloader_view import view_bp
from routes.editor import editor_bp
from routes.editor_pro import ed_bp
from routes.editor_tabs import tb_bp
from routes.enhanced_media_management import enhanced_media_bp
from routes.export_import import ei_bp
from routes.faceted_database import faceted_db_bp
from routes.features import feat_bp
from routes.feeds import feeds_bp
from routes.findreplace import fr_bp
from routes.flags import flags_bp
from routes.foundation import foundation_bp
from routes.guard_enforcer import guard_bp
from routes.hash import hash_bp
from routes.health import health_bp
from routes.hls_mgr import hls_bp
from routes.home_pins import pins_bp
from routes.hooks import hooks_bp
from routes.i18n import i18n_bp
from routes.indexing import idx_bp
from routes.integrations import integ_bp
from routes.jobs import jobs_bp
from routes.kids import kids_bp
from routes.kids_parental_controls import kids_parental_controls_bp
from routes.library import lib_bp
from routes.library_local import lib_bp
from routes.library_scan import scan_bp
from routes.libsearch import libsearch_bp
from routes.limits import lim_bp
from routes.link_grabber import link_grabber_bp
from routes.linkgrabber_templates import tmpl_bp
from routes.lists import lists_bp
from routes.lists_catalog import cat_bp
from routes.logs import logs_bp
from routes.lyrics import lyr_bp
from routes.media_collections import col_bp
from routes.metadata import md_bp
from routes.metrics_speed import sp_bp
from routes.missing import miss_bp
from routes.mobile_smart_rails_api import mobile_rails_bp
from routes.monaco_mgr import monaco_bp
from routes.movies_enhanced import movies_enhanced_bp
from routes.music_queue import mq_bp
from routes.opds import opds_bp
from routes.opds_books import opds_books_bp
from routes.organizer import org_bp
from routes.packages import packages_bp
from routes.pinboard import pin_bp
from routes.pinned import pin_bp
from routes.pins import pins_bp
from routes.playlists import pl_bp
from routes.presets import presets_bp
from routes.profile_management import profile_management_bp
from routes.profiles import prof_bp
from routes.qbittorrent import qb_bp
from routes.queue import q_bp
from routes.queue_combined import combo_bp
from routes.queue_meta import qm_bp
from routes.rails import rails_bp
from routes.rails_extra import extra_bp
from routes.rails_polish import rails_bp
from routes.rd import rd_bp
from routes.rd_analyze import ra_bp
from routes.rd_cloudpull import cloud_bp
from routes.rd_dedup import dedup_bp
from routes.rd_inbox import in_bp
from routes.rd_manager import rd_bp
from routes.rd_manager_enhanced import rd_manager_enhanced_bp
from routes.reader import reader_bp
from routes.reader_cbz import cbz_bp
from routes.reader_extract import readerx_bp
from routes.realdebrid import rd_bp
from routes.recipes import recipes_bp
from routes.renamer_advanced import renamer_advanced_bp
from routes.rss import rss_bp
from routes.rss_enhanced import rss_enhanced_bp
from routes.rss_feeder import rss_feeder_bp
from routes.rss_scheduler import sched_bp
from routes.rules_audit import rules_audit_bp
from routes.scheduler import sched_bp
from routes.scoring_engine import scoring_bp
from routes.secrets import secrets_bp
from routes.security import security_bp
from routes.selftest import selftest_bp
from routes.smart_rails import sr_bp
from routes.smart_rails_api import smart_rails_bp
from routes.smartplaylists import sp_bp
from routes.sort_editor import sort_bp
from routes.stream import stream_bp
from routes.stubs_extra import stubs_bp
from routes.subtitles_advanced import subtitles_advanced_bp
from routes.support_pack import support_bp
from routes.system import sys_bp
from routes.taxonomy import tax_bp
from routes.text_editor_enhanced import text_editor_enhanced_bp
from routes.thumbs import thumbs_bp
from routes.timeline import tl_bp
from routes.timelines import tl_bp
from routes.tools import tools_bp
from routes.toplists import tl_bp
from routes.toplists_directory import td_bp
from routes.torrent_inspector import torrent_inspector_bp
from routes.trailer import tr_bp
from routes.tree_view import tree_bp
from routes.tv_shows_enhanced import tv_shows_enhanced_bp
from routes.ui import ui_bp
from routes.views_counts import vc_bp
from routes.wanted import want_bp


# REGISTRATIONS
# Add these inside the register_routes() method or __init__


# CRITICAL Routes
app.register_blueprint(audio_enhanced_bp, url_prefix='/audio-enhanced')
app.register_blueprint(ap_bp, url_prefix='/audio')
app.register_blueprint(mix_bp, url_prefix='/mix')
app.register_blueprint(rg_bp, url_prefix='/rg')
app.register_blueprint(aset_bp, url_prefix='/aset')
app.register_blueprint(comics_enhanced_bp, url_prefix='/comics-enhanced')
app.register_blueprint(disc_bp, url_prefix='/disc')
app.register_blueprint(discovery_advanced_bp, url_prefix='/discovery-advanced')
app.register_blueprint(mobile_rails_bp, url_prefix='/mobile-smart-rails')
app.register_blueprint(tl_bp, url_prefix='/toplists')
app.register_blueprint(td_bp, url_prefix='/toplists-directory')

# MEDIA Routes
app.register_blueprint(col_bp, url_prefix='/collections')
app.register_blueprint(coll_bp, url_prefix='/coll')
app.register_blueprint(coll_bp, url_prefix='/collections-import')
app.register_blueprint(col_bp, url_prefix='/cols')
app.register_blueprint(timeline_bp, url_prefix='/collections-timeline')
app.register_blueprint(lib_bp, url_prefix='/library')
app.register_blueprint(lib_bp, url_prefix='/library-local')
app.register_blueprint(scan_bp, url_prefix='/scan')
app.register_blueprint(col_bp, url_prefix='/collections')
app.register_blueprint(pl_bp, url_prefix='/pl')
app.register_blueprint(reader_bp, url_prefix='/reader')
app.register_blueprint(cbz_bp, url_prefix='/cbz-reader')
app.register_blueprint(readerx_bp, url_prefix='/readerx')
app.register_blueprint(sp_bp, url_prefix='/smartpl')
app.register_blueprint(stream_bp, url_prefix='/stream')

# AUTOMATION Routes
app.register_blueprint(advanced_dl_bp, url_prefix='/advanced-downloader')
app.register_blueprint(dl_bp, url_prefix='/dl')
app.register_blueprint(dlx_bp, url_prefix='/dlx')
app.register_blueprint(downloader_enhanced_bp, url_prefix='/downloader-enhanced')
app.register_blueprint(pkg_bp, url_prefix='/packages')
app.register_blueprint(view_bp, url_prefix='/dlview')
app.register_blueprint(qb_bp, url_prefix='/qb')
app.register_blueprint(rss_bp, url_prefix='/rss')
app.register_blueprint(rss_enhanced_bp, url_prefix='/rss-enhanced')
app.register_blueprint(rss_feeder_bp, url_prefix='/rss')
app.register_blueprint(sched_bp, url_prefix='/rss-sched')
app.register_blueprint(sched_bp, url_prefix='/sched')
app.register_blueprint(torrent_inspector_bp, url_prefix='/torrent-inspector')

# UI Routes
app.register_blueprint(advanced_editor_bp, url_prefix='/advanced-text-editor')
app.register_blueprint(dedupe_bp, url_prefix='/dedupe')
app.register_blueprint(editor_bp, url_prefix='/ed')
app.register_blueprint(ed_bp, url_prefix='/ed')
app.register_blueprint(tb_bp, url_prefix='/tabs')
app.register_blueprint(sort_bp, url_prefix='/sort')
app.register_blueprint(text_editor_enhanced_bp, url_prefix='/text-editor-enhanced')
app.register_blueprint(ui_bp, url_prefix='/ui')

# TOOLS Routes
app.register_blueprint(br_bp, url_prefix='/br')
app.register_blueprint(db_bp, url_prefix='/db')
app.register_blueprint(org_bp, url_prefix='/org')
app.register_blueprint(renamer_advanced_bp, url_prefix='/renamer-advanced')
app.register_blueprint(tools_bp, url_prefix='/tools')

# TESTING Routes
app.register_blueprint(diag_bp, url_prefix='/diag')
app.register_blueprint(selftest_bp, url_prefix='/selftest')

# OTHER Routes
app.register_blueprint(acct_bp, url_prefix='/accounts')
app.register_blueprint(adv_bp, url_prefix='/adv')
app.register_blueprint(autoex_bp, url_prefix='/autoex')
app.register_blueprint(auto_bp, url_prefix='/auto')
app.register_blueprint(backup_bp, url_prefix='/backup')
app.register_blueprint(books_enhanced_bp, url_prefix='/books-enhanced')
app.register_blueprint(cap_bp, url_prefix='/captcha')
app.register_blueprint(catalogs_bp, url_prefix='/catalogs')
app.register_blueprint(cfg_bp, url_prefix='/config')
app.register_blueprint(conn_bp, url_prefix='/connectors')
app.register_blueprint(curations_bp, url_prefix='/curations')
app.register_blueprint(dashboard_custom_bp, url_prefix='/dashboard-custom')
app.register_blueprint(debrid_bp, url_prefix='/debrid')
app.register_blueprint(dd_bp, url_prefix='/dd')
app.register_blueprint(col_bp, url_prefix='/col')
app.register_blueprint(enhanced_media_bp, url_prefix='/enhanced-media')
app.register_blueprint(ei_bp, url_prefix='/export-import')
app.register_blueprint(faceted_db_bp, url_prefix='/faceted-db')
app.register_blueprint(feat_bp, url_prefix='/feat')
app.register_blueprint(feeds_bp, url_prefix='/feeds')
app.register_blueprint(fr_bp, url_prefix='/findrep')
app.register_blueprint(flags_bp, url_prefix='/flags')
app.register_blueprint(foundation_bp, url_prefix='/foundation')
app.register_blueprint(guard_bp, url_prefix='/guard')
app.register_blueprint(hash_bp, url_prefix='/hash')
app.register_blueprint(health_bp, url_prefix='/health')
app.register_blueprint(hls_bp, url_prefix='/hls')
app.register_blueprint(pins_bp, url_prefix='/home-pins')
app.register_blueprint(hooks_bp, url_prefix='/hooks')
app.register_blueprint(i18n_bp, url_prefix='/i18n')
app.register_blueprint(idx_bp, url_prefix='/idx')
app.register_blueprint(integ_bp, url_prefix='/integrations')
app.register_blueprint(jobs_bp, url_prefix='/jobs')
app.register_blueprint(kids_bp, url_prefix='/kids')
app.register_blueprint(kids_parental_controls_bp, url_prefix='/kids-parental-controls')
app.register_blueprint(libsearch_bp, url_prefix='/libsearch')
app.register_blueprint(lim_bp, url_prefix='/limits')
app.register_blueprint(link_grabber_bp, url_prefix='/link-grabber')
app.register_blueprint(tmpl_bp, url_prefix='/link-templates')
app.register_blueprint(lists_bp, url_prefix='/lists')
app.register_blueprint(cat_bp, url_prefix='/cat')
app.register_blueprint(logs_bp, url_prefix='/logs')
app.register_blueprint(lyr_bp, url_prefix='/lyrics')
app.register_blueprint(md_bp, url_prefix='/md')
app.register_blueprint(sp_bp, url_prefix='/metrics-speed')
app.register_blueprint(miss_bp, url_prefix='/miss')
app.register_blueprint(monaco_bp, url_prefix='/monaco')
app.register_blueprint(movies_enhanced_bp, url_prefix='/movies-enhanced')
app.register_blueprint(mq_bp, url_prefix='/music-queue')
app.register_blueprint(opds_bp, url_prefix='/opds')
app.register_blueprint(opds_books_bp, url_prefix='/opds-books')
app.register_blueprint(packages_bp, url_prefix='/packages')
app.register_blueprint(pin_bp, url_prefix='/pin')
app.register_blueprint(pin_bp, url_prefix='/pin')
app.register_blueprint(pins_bp, url_prefix='/pins')
app.register_blueprint(presets_bp, url_prefix='/presets')
app.register_blueprint(profile_management_bp, url_prefix='/profile-management')
app.register_blueprint(prof_bp, url_prefix='/prof')
app.register_blueprint(q_bp, url_prefix='/queue')
app.register_blueprint(combo_bp, url_prefix='/queue-combo')
app.register_blueprint(qm_bp, url_prefix='/queue-meta')
app.register_blueprint(rails_bp, url_prefix='/rails')
app.register_blueprint(extra_bp, url_prefix='/rails-extra')
app.register_blueprint(rails_bp, url_prefix='/rails-polish')
app.register_blueprint(rd_bp, url_prefix='/rd')
app.register_blueprint(ra_bp, url_prefix='/ra')
app.register_blueprint(cloud_bp, url_prefix='/rd-cloudpull')
app.register_blueprint(dedup_bp, url_prefix='/rd-dedup')
app.register_blueprint(in_bp, url_prefix='/inbox')
app.register_blueprint(rd_bp, url_prefix='/rd')
app.register_blueprint(rd_manager_enhanced_bp, url_prefix='/rd-manager-enhanced')
app.register_blueprint(rd_bp, url_prefix='/rd')
app.register_blueprint(recipes_bp, url_prefix='/recipes')
app.register_blueprint(rules_audit_bp, url_prefix='/rules-audit')
app.register_blueprint(scoring_bp, url_prefix='/scoring')
app.register_blueprint(secrets_bp, url_prefix='/secrets')
app.register_blueprint(security_bp, url_prefix='/security')
app.register_blueprint(sr_bp, url_prefix='/smart')
app.register_blueprint(smart_rails_bp, url_prefix='/smart-rails-api')
app.register_blueprint(stubs_bp, url_prefix='/stubs-extra')
app.register_blueprint(subtitles_advanced_bp, url_prefix='/subtitles-advanced')
app.register_blueprint(support_bp, url_prefix='/support')
app.register_blueprint(sys_bp, url_prefix='/sys')
app.register_blueprint(tax_bp, url_prefix='/taxonomy')
app.register_blueprint(thumbs_bp, url_prefix='/thumbs')
app.register_blueprint(tl_bp, url_prefix='/tl')
app.register_blueprint(tl_bp, url_prefix='/tl')
app.register_blueprint(tr_bp, url_prefix='/trailer')
app.register_blueprint(tree_bp, url_prefix='/tree')
app.register_blueprint(tv_shows_enhanced_bp, url_prefix='/tv-shows-enhanced')
app.register_blueprint(vc_bp, url_prefix='/views-counts')
app.register_blueprint(want_bp, url_prefix='/want')

from flask import Flask, send_from_directory
import os
from routes.config import cfg_bp
from routes.limits import lim_bp
from routes.toplists_directory import td_bp
from routes.opds import opds_bp
from routes.rd import rd_bp
from routes.queue import q_bp
from routes.library import lib_bp
from routes.trailer import tr_bp
from routes.reader import reader_bp
from routes.collections import col_bp
from routes.tools import tools_bp
from routes.stream import stream_bp
from routes.thumbs import thumbs_bp
from routes.logs import logs_bp
from routes.selftest import selftest_bp
from routes.hash import hash_bp
from routes.scheduler import sched_bp
from routes.db_tools import db_bp
from routes.debrid import debrid_bp
from routes.recipes import recipes_bp
from routes.libsearch import libsearch_bp
from routes.playlists import pl_bp
from routes.lyrics import lyr_bp
from routes.lists_catalog import cat_bp
from routes.profiles import prof_bp
from routes.editor import editor_bp
from routes.monaco_mgr import monaco_bp
from routes.hls_mgr import hls_bp
from routes.smartplaylists import sp_bp
from routes.stream_audio_norm import anorm_bp
from routes.discovery import disc_bp
from routes.i18n import i18n_bp
from routes.security import security_bp
from routes.batchrename import br_bp
from routes.rd_manager import rd_bp
from routes.reader import rd_bp
from routes.audio_player import ap_bp
from routes.system import sys_bp
from routes.editor_pro import ed_bp
from routes.features import feat_bp
from routes.rss_feeder import rss_bp
from routes.dedupe import dd_bp
from routes.rd_inbox import in_bp
from routes.editor_tabs import tb_bp
from routes.auto_select import auto_bp
from routes.wanted import want_bp
from routes.downloader_api import dlx_bp
from routes.downloader_view import view_bp
from routes.ui import ui_bp
from routes.collections_manage import col_bp
from routes.timelines import tl_bp
from routes.auto_explain import autoex_bp
from routes.hooks import hooks_bp
from routes.lists import lists_bp
from routes.smart_rails import sr_bp
from routes.audio_playlists import mix_bp
from routes.kids import kids_bp
from routes.indexing import idx_bp
from routes.pinboard import pin_bp
from routes.timeline import tl_bp
from routes.editor import ed_bp
from routes.dl_columns import col_bp
from routes.audio_replaygain import rg_bp
from routes.audio_settings import aset_bp
from routes.collections_api import coll_bp
from routes.dedupe import dedupe_bp
from routes.downloader import dl_bp
from routes.missing import miss_bp
from routes.feeds import feeds_bp
from routes.findreplace import fr_bp
from routes.adv_search import adv_bp
from routes.secrets import secrets_bp
from routes.jobs import jobs_bp
from routes.health import health_bp
from routes.reader_extract import readerx_bp
from routes.backup import backup_bp
from flask import send_from_directory
from routes.rss import rss_bp
from routes.rails import rails_bp
from scheduler.jobs import jobs_start

app = Flask(__name__, static_folder=None)
for bp in (cfg_bp, lim_bp, td_bp, opds_bp, rd_bp, q_bp, lib_bp, reader_bp, readerx_bp, tr_bp, col_bp, rss_bp, rails_bp, backup_bp, tools_bp, stream_bp, thumbs_bp, logs_bp, selftest_bp, hash_bp, sched_bp, db_bp, debrid_bp, recipes_bp, libsearch_bp, pl_bp, lyr_bp, cat_bp, prof_bp, editor_bp):
    app.register_blueprint(bp)

WEB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web'))
@app.route('/<path:path>')
def static_proxy(path): return send_from_directory(WEB, path)
@app.route('/')
def index(): return send_from_directory(WEB, 'home.html')

LEG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web_legacy'))
@app.route('/legacy/<path:path>')
def legacy(path):
    return send_from_directory(LEG, path)

jobs_start()  # background tasks

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)


# --- Gate J security hooks (CSRF/CORS) ---
def _apply_security_hooks(app):
    import json, os
    from flask import request, abort
    ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
    STO=os.path.join(ROOT,'storage')
    CFG=os.path.join(STO,'config.json')
    TOK=os.path.join(STO,'csrf_token.txt')
    def _cfg():
        try: return json.load(open(CFG,'r',encoding='utf-8'))
        except Exception: return {}
    def _token():
        if not os.path.exists(TOK):
            import secrets; open(TOK,'w',encoding='utf-8').write(secrets.token_urlsafe(32))
        return open(TOK,'r',encoding='utf-8').read().strip()

    @app.before_request
    def _csrf_guard():
        c=_cfg().get('security',{})
        if not c.get('csrf_enforce'): return
        if request.method in ('POST','PUT','DELETE','PATCH'):
            hdr=request.headers.get('X-CSRF-Token','')
            if hdr != _token():
                abort(403)

    @app.after_request
    def _cors_hdrs(resp):
        c=_cfg().get('security',{})
        allow=c.get('cors_allow_origin') or ''
        if allow:
            resp.headers['Access-Control-Allow-Origin']=allow
            resp.headers['Vary']='Origin'
            resp.headers['Access-Control-Allow-Headers']='*, X-CSRF-Token, Content-Type'
            resp.headers['Access-Control-Allow-Methods']='GET, POST, PUT, DELETE, PATCH, OPTIONS'
        return resp

_apply_security_hooks(app)

from routes.organizer import org_bp
app.register_blueprint(org_bp)

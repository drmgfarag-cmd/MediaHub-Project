from flask import Blueprint, jsonify
import threading, time, os, json, requests, re
from .flags import _load as flags_load

sched_bp = Blueprint('rss_sched', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
FEEDS= os.path.join(STO, 'rss_feeds.json')
RUN  = {'t': None, 'stop': False}

def _flags(): 
    try: return flags_load()
        except: return {}

def _load_feeds():
        try: return json.load(open(FEEDS,'r',encoding='utf-8'))
        except: return {"feeds":[]}

def _poll_feed(url, include, exclude):
    try:
        r=requests.get(url, timeout=20)
        if r.status_code!=200: return []
        import xml.etree.ElementTree as ET
        root=ET.fromstring(r.text)
        items=[]
        for it in root.findall('.//item'):
            title=(it.findtext('title') or '').strip()
            link =(it.findtext('link') or '').strip()
            ok=all(re.search(x,title,re.I) for x in (include or []) if x and x!='*')
            ok= ok and all(not re.search(x,title,re.I) for x in (exclude or []))
            if ok: items.append({"title":title,"link":link})
        return items
    except Exception:
        return []

def _loop():
    while not RUN['stop']:
        if not _flags().get('enable_rss_scheduler'):
            time.sleep(5); continue
        data=_load_feeds()
        changed=False
        for f in data.get('feeds',[]):
            interval=int(f.get('interval', 60))
            last=int(f.get('last', 0))
            now=int(time.time())
            if now - last >= interval*60:
                f['last']=now; changed=True
                items=_poll_feed(f.get('url',''), f.get('include'), f.get('exclude'))
                # auto-pipe: RD or Downloader
                if f.get('to')=='rd':
                    for it in items[:10]:
                        try:
                            requests.post('http://127.0.0.1:5000/api/rd/unrestrict', json={"link": it['link']}, timeout=10)
                        except Exception: pass
                elif f.get('to')=='downloader':
                    for it in items[:10]:
                        try:
                            requests.post('http://127.0.0.1:5000/api/downloader/add', json={"url": it['link']}, timeout=10)
                        except Exception: pass
        if changed:
            tmp=FEEDS+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(data,indent=2)); os.replace(tmp, FEEDS)
        time.sleep(10)

@sched_bp.route('/api/rss/scheduler/start')
def start():
    try:
        if RUN['t']: return jsonify({"ok":True,"note":"running"})
        RUN['stop']=False
        t=threading.Thread(target=_loop, daemon=True); RUN['t']=t; t.start()
        return jsonify({"ok":True})


        @sched_bp.route('/api/rss/scheduler/stop')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def stop():
    try:
        RUN['stop']=True; RUN['t']=None
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

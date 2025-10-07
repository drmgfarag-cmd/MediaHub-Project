import threading, time, os, json
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
RSS=os.path.join(STO,'rss_feeds.json'); SUGG=os.path.join(STO,'rss_suggestions.json')
TD=os.path.join(STO,'top_lists_directory.json')
AUTO=os.path.join(STO,'rss_auto.json')
CFG=os.path.join(STO,'config.json')
SCH=os.path.join(STO,'scheduler.json')

def _load(p,d):
    try: return json.load(open(p,'r',encoding='utf-8'))
    except: return d
def _save(p,o): open(p+'.tmp','w',encoding='utf-8').write(json.dumps(o,indent=2)); os.replace(p+'.tmp',p)

from connectors.aria2 import Aria2
from connectors.qb import QBit
from routes.recipes import process_events

def rss_job():
    while True:
        try:
            feeds=_load(RSS, {"feeds":[]}).get('feeds',[]) ; auto=_load(AUTO,{"enabled":False}) ; cfg=_load(CFG,{})
            sugg=_load(SUGG, {"items":[]})
            # Placeholder: in real app, fetch feeds -> update suggestions
            if feeds and not sugg.get('items'):
                sugg['items']=[{'title':'Missing Episode placeholder','source':feeds[0].get('name','feed'), 'url': feeds[0].get('url','')}]
            # auto-enqueue
            if auto.get('enabled'):
                urls=[it.get('url') for it in sugg.get('items',[]) if it.get('url')]
                if urls:
                    try:
                        if cfg.get('qb',{}).get('base_url'):
                            QBit(cfg['qb']['base_url'], cfg['qb'].get('username',''), cfg['qb'].get('password','')).add_urls(urls)
                    except Exception: pass
                    try:
                        if cfg.get('aria2',{}).get('rpc_url'):
                            Aria2(cfg['aria2']['rpc_url'], cfg['aria2'].get('secret')).add_uri(urls)
                    except Exception: pass
                _save(SUGG, sugg)
        except Exception: pass
        time.sleep(300)

_started=False
def jobs_start():
    global _started
    if _started: return
    threading.Thread(target=rss_job, daemon=True).start()
    _started=True

def _now_local():
    import datetime
    return datetime.datetime.now()

def _in_window(rule, now):
    # rule: {"days":[0-6], "start":"HH:MM", "end":"HH:MM", "download_kbps": 0 (unlimited) }
    if rule.get('days') and now.weekday() not in rule['days']: return False
    try:
        sh,sm=map(int,(rule.get('start','00:00')).split(':'))
        eh,em=map(int,(rule.get('end','23:59')).split(':'))
    except Exception:
        return False
    st=now.replace(hour=sh, minute=sm, second=0, microsecond=0)
    et=now.replace(hour=eh, minute=em, second=0, microsecond=0)
    if et<st:  # crosses midnight
        return now>=st or now<=et
    return st<=now<=et

def rate_job():
    cfg=_load(CFG,{}); sch=_load(SCH,{'rules':[]})
    # compute current desired limit
    now=_now_local()
    kbps=None
    for r in sch.get('rules',[]):
        if _in_window(r, now): kbps = r.get('download_kbps', kbps)
    # apply to qB/aria2 if configured
    try:
        if cfg.get('qb',{}).get('base_url'):
            q=QBit(cfg['qb']['base_url'], cfg['qb'].get('username',''), cfg['qb'].get('password',''))
            if kbps is None or kbps==0: q.set_download_limit(0)
            else: q.set_download_limit(int(kbps*1024))
    except Exception: pass
    try:
        if cfg.get('aria2',{}).get('rpc_url'):
            a=Aria2(cfg['aria2']['rpc_url'], cfg['aria2'].get('secret'))
            if kbps is None or kbps==0: a.set_global_limit(0)
            else: a.set_global_limit(int(kbps*1024))
    except Exception: pass

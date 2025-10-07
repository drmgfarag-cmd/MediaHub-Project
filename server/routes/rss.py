from flask import Blueprint, jsonify, request
import os, json, time, re
import requests

rss_bp = Blueprint('rss', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
F=os.path.join(STO,'rss_feeds.json')

def _load():
  try: return json.load(open(F,'r',encoding='utf-8'))
  except Exception: return {'feeds':[]}

def _save(obj):
  tmp=F+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp,F)

@rss_bp.route('/api/rss/list')
def list_():
  return jsonify(_load())

@rss_bp.route('/api/rss/set', methods=['POST'])
def set_():
  js=request.get_json(silent=True) or {'feeds':[]}
  _save(js); return jsonify({'ok':True})

@rss_bp.route('/api/rss/scan')
def scan():
  js=_load(); out=[]
  for f in js.get('feeds',[]):
    if not f.get('enabled'): continue
    url=f.get('url'); 
    try:
      r=requests.get(url, timeout=10)
      if r.status_code==200:
        # naive parse for titles/links
        text=r.text
        items=re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?</item>', text, re.S|re.I)
        out.extend([{'feed':f.get('name'), 'title': t[0], 'link': t[1]} for t in items[:50]])
    except Exception:
      pass
  return jsonify({'items': out})

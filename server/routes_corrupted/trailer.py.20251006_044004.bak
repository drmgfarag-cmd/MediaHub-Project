from flask import Blueprint, jsonify, request
tr_bp = Blueprint('trailer', __name__)
@tr_bp.route('/api/trailer/hero')
def hero():
    cat = request.args.get('category','movies')
    autogen = request.args.get('autogen','0')=='1'
    data = {
        'movies': [{'poster':'/assets/demo_poster.jpg', 'title':'Demo Movie'}],
        'tv':     [{'poster':'/assets/demo_poster.jpg', 'title':'Demo Show'}],
        'books':  [{'poster':'/assets/demo_poster.jpg', 'title':'Demo Book'}],
        'audio':  [{'poster':'/assets/demo_poster.jpg', 'title':'Demo Album'}],
        'kids':   [{'poster':'/assets/demo_poster.jpg', 'title':'Kids Picks'}],
    }
    if autogen:
        import os, json
        ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
        LIB=os.path.join(ROOT,'storage','library_index.json')
        try:
            lib=json.load(open(LIB,'r',encoding='utf-8'))
        except Exception:
            lib=[]
        # pick first item by category
        def pick(kind):
            for it in lib:
                if kind=='movies' and it.get('type')=='movie': return it
                if kind=='tv' and it.get('type')=='series': return it
                if kind=='books' and it.get('type') in ('ebook','comic','manga','audiobook'): return it
                if kind=='audio' and it.get('type')=='audio': return it
                if kind=='kids' and it.get('is_kids'): return it
            return None
        cand = pick(cat)
        if cand and cand.get('path'):
            from .thumbs import _sid
            sid=_sid(cand['path'])
            d={'poster': f'/thumbs/{sid}/poster.jpg'}
            # if poster missing, call ensure inline
            poster_path=os.path.join(ROOT,'storage','tmp','thumbs',sid,'poster.jpg')
            if not os.path.exists(poster_path):
                try:
                    from flask import current_app
                    with current_app.test_request_context(): pass
                    # simple import-local ensure to generate
                    from .thumbs import ensure as _ensure
                except Exception: pass
            data[cat] = [ {'poster': d['poster'], 'title': cand.get('title','')} ]
    return jsonify({'ok': True, 'category': cat, 'items': data.get(cat, [])})

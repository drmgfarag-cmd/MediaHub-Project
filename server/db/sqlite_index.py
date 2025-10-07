import os, sqlite3, json, time
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
DB=os.path.join(STO,'db.sqlite')
JSON_IDX=os.path.join(STO,'library_index.json')

def _conn():
    os.makedirs(STO, exist_ok=True)
    return sqlite3.connect(DB)

def ensure():
    with _conn() as c:
        c.execute('create table if not exists items (id integer primary key, type text, title text, path text unique, year int, is_kids int default 0, meta text)')
        c.execute('create index if not exists ix_items_type on items(type)')
        c.execute('create index if not exists ix_items_title on items(title)')

def migrate_from_json():
    ensure()
    try:
        data=json.load(open(JSON_IDX,'r',encoding='utf-8'))
    except Exception:
        data=[]
    with _conn() as c:
        for it in data:
            year=None
            # try parse year off title or meta
            import re
            m=re.search(r'(19\d{2}|20\d{2})', (it.get('title') or '')+' '+(it.get('path') or ''))
            if m: year=int(m.group(1))
            c.execute('insert or ignore into items(type,title,path,year,is_kids,meta) values(?,?,?,?,?,?)',
                      (it.get('type'), it.get('title'), it.get('path'), year, 1 if it.get('is_kids') else 0, json.dumps(it, ensure_ascii=False)))
        c.commit()

def query(q:str='', type_:str=None, limit:int=200):
    ensure()
    sql='select title, path, type, year, is_kids from items where 1=1'
    args=[]
    if type_:
        sql+=' and type=?'; args.append(type_)
    if q:
        like='%' + q.replace('%','') + '%'
        sql+=' and (title like ? or path like ?)'; args.extend([like, like])
    sql+=' order by title limit ?'; args.append(limit)
    with _conn() as c:
        return [dict(title=r[0], path=r[1], type=r[2], year=r[3], is_kids=r[4]) for r in c.execute(sql, args)]

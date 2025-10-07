import time, json, requests

def fetch_tmdb(api_key:str, list_type:str='movie_top_rated', page:int=1):
    base='https://api.themoviedb.org/3'
    if list_type=='movie_top_rated':
        url=f'{base}/movie/top_rated?language=en-US&page={page}&api_key={api_key}'
    elif list_type=='tv_popular':
        url=f'{base}/tv/popular?language=en-US&page={page}&api_key={api_key}'
    else:
        return []
    r=requests.get(url, timeout=10); r.raise_for_status(); js=r.json()
    out=[]
    for it in js.get('results', []):
        out.append({'title': it.get('title') or it.get('name'), 'id': it.get('id'), 'year': (it.get('release_date') or it.get('first_air_date') or '')[:4]})
    return out

def fetch_trakt(client_id:str, path:str='/movies/trending'):
    url='https://api.trakt.tv'+path
    h={'trakt-api-key': client_id, 'trakt-api-version':'2'}
    r=requests.get(url, headers=h, timeout=10); r.raise_for_status(); js=r.json()
    out=[]
    for it in js:
        m = it.get('movie') or it.get('show') or {}
        out.append({'title': m.get('title'), 'year': m.get('year'), 'id': (m.get('ids') or {}).get('slug')})
    return out

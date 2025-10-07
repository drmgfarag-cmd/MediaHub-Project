import requests
from .debrid_base import DebridBase

class Premiumize(DebridBase):
    def __init__(self, apikey): self.apikey=apikey; self.base='https://www.premiumize.me/api'
    def _get(self, path, **kw): return requests.get(self.base+path, params={'apikey': self.apikey, **kw}).json()
    def _post(self, path, data=None): return requests.post(self.base+path, data={**(data or {}), 'apikey': self.apikey}).json()
    def torrents(self): 
        try: return self._get('/transfer/list').get('transfers',[])
        except Exception: return []
    def add_magnet(self, magnet): return self._post('/transfer/create', data={'src': magnet})
    def del_torrent(self, tid): return self._post('/transfer/delete', data={'id': tid})
    def unrestrict(self, link): return self._post('/transfer/directdl', data={'src': link})
    def user(self): return self._get('/account/info')
    def traffic(self): return {}
    def hosts(self): return {}
    def torrent_info(self, tid): return {}
    def select_files(self, tid, files): return {}

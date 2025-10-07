import requests
from .debrid_base import DebridBase

class AllDebrid(DebridBase):
    def __init__(self, apikey): self.apikey=apikey; self.base='https://api.alldebrid.com/v4'
    def _get(self, path, **kw): return requests.get(self.base+path, params={'apikey': self.apikey, **kw}).json()
    def _post(self, path, data=None): return requests.post(self.base+path, data={**(data or {}), 'apikey': self.apikey}).json()
    def torrents(self): 
        try: return self._get('/magnet/status').get('data',{}).get('magnets',[])
        except Exception: return []
    def add_magnet(self, magnet): return self._post('/magnet/upload', data={'magnets[]': magnet})
    def del_torrent(self, tid): return self._post('/magnet/delete', data={'id': tid})
    def unrestrict(self, link): return self._post('/link/unlock', data={'link': link})
    def user(self): return self._get('/user')
    def traffic(self): return self._get('/user/traffic')
    def hosts(self): return self._get('/hosts')
    def torrent_info(self, tid): return self._get('/magnet/status', id=tid)
    def select_files(self, tid, files): return self._post('/magnet/selectFiles', data={'id': tid, 'files[]': files})

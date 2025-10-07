import requests, hashlib

class RealDebrid:
    def __init__(self, token:str, timeout:int=10):
        self.base='https://api.real-debrid.com/rest/1.0'
        self.h={'Authorization':'Bearer '+token}
        self.t=timeout
    def user(self): return requests.get(self.base+'/user', headers=self.h, timeout=self.t).json()
    def torrents(self): return requests.get(self.base+'/torrents', headers=self.h, timeout=self.t).json()
    def unrestrict(self, link:str): return requests.post(self.base+'/unrestrict/link', headers=self.h, data={'link':link}, timeout=self.t).json()
    def add_magnet(self, magnet:str): return requests.post(self.base+'/torrents/addMagnet', headers=self.h, data={'magnet':magnet}, timeout=self.t).json()
    def del_torrent(self, tid:str): return requests.delete(self.base+'/torrents/delete/'+tid, headers=self.h, timeout=self.t).json()
    @staticmethod
    def group_duplicates(files):
        # files: [{'id','filename','filesize'}]
        buckets={}
        for f in files:
            name=f.get('filename','')
            key=''.join([c.lower() for c in name if c.isalnum()])
            size=f.get('filesize',0)
            h=hashlib.md5((key+str(size)).encode()).hexdigest()[:8]
            buckets.setdefault(h, {'hash':h,'name':name.split('.')[0],'files':[]})['files'].append({'id':f.get('id'), 'name':name, 'size_mb': int(size/1_000_000)})
        return list(buckets.values())

import requests

class QBit:
    def __init__(self, base_url:str, username:str, password:str, timeout:int=8):
        self.base = base_url.rstrip('/')
        self.username=username; self.password=password; self.timeout=timeout
        self.s=requests.Session()
    def login(self):
        r=self.s.post(self.base+'/api/v2/auth/login', data={'username':self.username,'password':self.password}, timeout=self.timeout)
        if r.text!='Ok.': raise RuntimeError('qB login failed')
    def set_limit(self, kbps:int):
        self.login()
        self.s.post(self.base+'/api/v2/transfer/setDownloadLimit', data={'limit': str(kbps*1024)}, timeout=self.timeout)
    def info(self):
        self.login(); r=self.s.get(self.base+'/api/v2/torrents/info', timeout=self.timeout); return r.json()
    def add_urls(self, urls:list[str]):
        self.login(); self.s.post(self.base+'/api/v2/torrents/add', data={'urls': '\n'.join(urls)}, timeout=self.timeout)


    def set_download_limit(self, bytes_per_sec:int):
        # 0 => unlimited
        try:
            limit = max(0, int(bytes_per_sec))
            # /transfer/setDownloadLimit expects bytes/second
            self._post('/api/v2/transfer/setDownloadLimit', data={'limit': str(limit)})
        except Exception:
            pass

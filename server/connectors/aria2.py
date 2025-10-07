import json, requests

class Aria2:
    def __init__(self, rpc_url:str, secret:str|None=None, timeout:int=8):
        self.url = rpc_url.rstrip('/')
        self.secret = secret
        self.timeout = timeout
    def _call(self, method, params=None):
        params = params or []
        if self.secret: params = ["token:"+self.secret] + params
        payload = {"jsonrpc":"2.0","id":"mh","method":"aria2."+method,"params":params}
        r = requests.post(self.url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        js = r.json()
        if 'error' in js: raise RuntimeError(js['error'])
        return js.get('result')
    def get_stat(self): return self._call("getGlobalStat")
    def change_limit(self, kbps:int):
        return self._call("changeGlobalOption", [ {"max-overall-download-limit": f"{kbps}K"} ])
    def add_uri(self, uris:list[str], options:dict|None=None): return self._call("addUri", [uris, options or {}])
    def tell_active(self): return self._call("tellActive") or []
    def tell_waiting(self, offset=0, num=100): return self._call("tellWaiting", [offset, num, []]) or []
    def pause(self, gid): return self._call("pause", [gid])
    def unpause(self, gid): return self._call("unpause", [gid])
    def remove(self, gid): return self._call("remove", [gid])


    def set_global_limit(self, bytes_per_sec:int):
        # 0 => unlimited
        opt = {'max-overall-download-limit': '0' if bytes_per_sec<=0 else str(bytes_per_sec)}
        try:
            self._call('aria2.changeGlobalOption', [opt])
        except Exception:
            pass

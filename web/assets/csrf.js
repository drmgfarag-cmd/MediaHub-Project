(async function(){
  try{
    const j=await (await fetch('/api/csrf/token')).json();
    const t=j.token;
    // Patch fetch to auto-attach header on same-origin requests
    const _f=window.fetch;
    window.fetch = function(input, init){
      try{
        const u = (typeof input==='string') ? new URL(input, location.origin) : new URL(input.url, location.origin);
        if (u.origin === location.origin){
          init = init || {};
          init.headers = init.headers || {};
          if (init.headers instanceof Headers){ init.headers.set('X-CSRF-Token', t); }
          else{ init.headers['X-CSRF-Token']=t; }
        }
      }catch(e){}
      return _f(input, init);
    };
    window.__CSRF_TOKEN__=t;
  }catch(e){}
})();
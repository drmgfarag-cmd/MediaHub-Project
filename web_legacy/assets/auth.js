(async function(){
  try{
    const r=await fetch('/api/integrations'); const j=await r.json();
    const key = (j && j.api_key)||'';
    if(!key) return;
    const _fetch = window.fetch;
    window.fetch = function(input, init){ 
      init = init || {};
      init.headers = init.headers || {};
      if(typeof init.headers.append === 'function'){ init.headers.append('X-API-Key', key); }
      else { init.headers['X-API-Key']=key; }
      return _fetch(input, init);
    };
  }catch(e){}
})();
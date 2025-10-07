(function(){
  async function refreshFooterExtra(){
    try{
      const q=await (await fetch('/api/downloader/queue')).json();
      const items=(q.items||[]);
      const active=items.filter(it=>it.status==='downloading').length;
      const queued=items.filter(it=>!it.status || it.status==='queued').length;
      const eta='--'; // placeholder until connectors provide remaining size/speed
      const span=document.getElementById('sf-extra'); if(span){
        span.textContent = `• Active: ${active} • Queued: ${queued} • ETA: ${eta}`;
        span.style.marginLeft='8px';
        span.style.opacity='0.9';
      }
    }catch(e){}
  }
  setInterval(refreshFooterExtra, 5000);
  document.addEventListener('DOMContentLoaded', refreshFooterExtra);
})();
(function(){
  const points=[]; const MAX=120;
  function draw(){
    const c=document.getElementById('sf-graph'); if(!c) return;
    const ctx=c.getContext('2d'); const w=c.width, h=c.height;
    ctx.clearRect(0,0,w,h);
    ctx.beginPath(); ctx.moveTo(0,h);
    points.forEach((v,i)=>{ const x=i*(w/MAX); const y=h - Math.min(h, v); ctx.lineTo(x,y); });
    ctx.lineTo(w,h); ctx.closePath(); ctx.globalAlpha=0.3; ctx.fill(); ctx.globalAlpha=1; ctx.stroke();
  }
  async function tick(){
    try{
      const q=await (await fetch('/api/downloader/queue')).json();
      const sum=(q.items||[]).filter(it=>it.status==='downloading').reduce((a,b)=>a+(b.bytes_rate||0),0);
      points.push(sum/10000); if(points.length>MAX) points.shift();
      draw();
    }catch(e){}
  }
  function init(){
    const footer=document.getElementById('status-footer'); if(!footer) return;
    if(!document.getElementById('sf-graph')){
      const c=document.createElement('canvas'); c.id='sf-graph'; c.width=120; c.height=24; c.style='margin-left:8px;vertical-align:middle;';
      footer.appendChild(c);
    }
    setInterval(tick, 2000);
  }
  document.addEventListener('DOMContentLoaded', init);
})();
(function(){
  const MAX_VISIBLE = 6; // rest go to "More"
  function saveOrder(ids){ localStorage.setItem('rails:order', JSON.stringify(ids)); }
  function loadOrder(){ try{ return JSON.parse(localStorage.getItem('rails:order')||'[]'); }catch(e){ return []; } }
  function applyOrder(area){
    const ids=loadOrder(); if(!ids.length) return;
    const nodes=[...area.querySelectorAll('[data-rail-id]')];
    const map={}; nodes.forEach(n=>map[n.getAttribute('data-rail-id')]=n);
    ids.forEach(id=>{ if(map[id]) area.appendChild(map[id]); });
  }
  function overflow(area){
    const nodes=[...area.querySelectorAll('[data-rail-id]')];
    if(nodes.length<=MAX_VISIBLE) return;
    const vis=nodes.slice(0,MAX_VISIBLE);
    const more=nodes.slice(MAX_VISIBLE);
    more.forEach(n=>n.style.display='none');
    let btn=document.getElementById('rails-more-btn');
    if(!btn){
      btn=document.createElement('button'); btn.id='rails-more-btn'; btn.textContent='More…';
      btn.style='background:#0f172a;border:1px solid #334155;color:#cbd5e1;border-radius:10px;padding:6px 10px;margin:8px 0';
      area.parentElement.insertBefore(btn, area.nextSibling);
      btn.addEventListener('click', ()=>{ more.forEach(n=>n.style.display=''); btn.remove(); });
    }
  }
  function draggable(area){
    let drag=null;
    area.querySelectorAll('[data-rail-id]').forEach(n=>{
      n.draggable=true;
      n.addEventListener('dragstart', ()=>{ drag=n; n.style.opacity='.6'; });
      n.addEventListener('dragend', ()=>{ drag=null; n.style.opacity=''; const ids=[...area.querySelectorAll('[data-rail-id]')].map(x=>x.getAttribute('data-rail-id')); saveOrder(ids); });
      n.addEventListener('dragover', (e)=>{ e.preventDefault(); });
      n.addEventListener('drop', (e)=>{ e.preventDefault(); if(!drag || drag===n) return; area.insertBefore(drag, n); });
    });
  }
  function init(){
    const area=document.querySelector('#rails, .rails, [data-rails]'); if(!area) return;
    applyOrder(area); overflow(area); draggable(area);
  }
  document.addEventListener('DOMContentLoaded', init);
})();
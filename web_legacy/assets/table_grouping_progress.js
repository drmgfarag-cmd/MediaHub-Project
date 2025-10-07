(function(){
  function init(){
    document.querySelectorAll('table[data-groupable]').forEach(tbl=>{
      const hdr = tbl.querySelector('thead tr');
      if(!hdr) return;
      // Add a Group toggle
      let btn = document.createElement('button');
      btn.textContent='Group: Bundles';
      btn.style='margin:6px 0;background:#0f172a;border:1px solid #334155;color:#cbd5e1;border-radius:10px;padding:6px 10px';
      tbl.parentElement.insertBefore(btn, tbl);
      const rows=[...tbl.querySelectorAll('tbody tr')];
      btn.addEventListener('click', ()=>{
        const groups={};
        rows.forEach(r=>{
          const b=(r.getAttribute('data-bundle')||'').trim();
          const k=b||'__no__';
          (groups[k]=groups[k]||[]).push(r);
        });
        const tb=tbl.querySelector('tbody');
        tb.innerHTML='';
        Object.entries(groups).forEach(([k,arr])=>{
          if(k!=='__no__'){
            const tr=document.createElement('tr'); tr.className='group-row';
            const td=document.createElement('td'); td.colSpan=hdr.children.length; td.textContent = 'Bundle: '+k+' ('+arr.length+')';
            td.style='background:#0b1220;color:#cbd5e1;border:1px solid #334155;font-weight:600;cursor:pointer';
            tr.appendChild(td); tb.appendChild(tr);
            tr.addEventListener('click', ()=>{
              const vis=arr[0].style.display!== 'none';
              arr.forEach(x=>x.style.display= vis ? 'none' : '' );
            });
          }
          arr.forEach(r=>tb.appendChild(r));
        });
      });
      // Per-row progress bars (if data-progress present 0..100)
      rows.forEach(r=>{
        const p = parseFloat(r.getAttribute('data-progress')||'NaN');
        if(!isNaN(p)){
          const last=r.lastElementChild || r.appendChild(document.createElement('td'));
          const bar=document.createElement('div'); bar.style='height:6px;border-radius:4px;background:#1f2937;position:relative;overflow:hidden';
          const fill=document.createElement('div'); fill.style='position:absolute;left:0;top:0;bottom:0;width:'+Math.max(0,Math.min(100,p))+'%;background:#22c55e';
          bar.appendChild(fill); last.appendChild(bar);
        }
      });
    });
  }
  document.addEventListener('DOMContentLoaded', init);
})();
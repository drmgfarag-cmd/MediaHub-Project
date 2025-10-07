(function(){
  function init(){
    document.querySelectorAll('table[data-enhance="table"]').forEach((tbl,i)=>{
      const id=tbl.id||('tbl'+i);
      // Sticky header
      tbl.classList.add('stick-head');
      // Build column chooser if header exists
      const ths=[...tbl.querySelectorAll('thead th')];
      if(!ths.length) return;
      const box=document.createElement('div');
      box.className='tbl-controls';
      box.style='display:flex;gap:8px;align-items:center;margin:6px 0;flex-wrap:wrap';
      const den=document.createElement('select');
      den.innerHTML='<option value="compact">Compact</option><option value="comfortable">Comfortable</option>';
      den.addEventListener('change', ()=>{
        tbl.dataset.density=den.value; localStorage.setItem(id+':density', den.value);
      });
      box.appendChild(den);
      const chooser=document.createElement('div'); chooser.textContent='Columns:'; chooser.style='display:flex;gap:8px;flex-wrap:wrap;margin-left:8px';
      ths.forEach((th,ci)=>{
        const lab=document.createElement('label'); lab.style='font-size:12px;opacity:.9';
        const cb=document.createElement('input'); cb.type='checkbox'; cb.checked=true;
        cb.addEventListener('change', ()=>{
          const show=cb.checked;
          tbl.querySelectorAll('tr').forEach(tr=>{
            const tds=tr.children; if(tds[ci]) tds[ci].style.display = show ? '' : 'none';
          });
          const vis=(JSON.parse(localStorage.getItem(id+':cols')||'{}')); vis[ci]=show; localStorage.setItem(id+':cols', JSON.stringify(vis));
        });
        lab.appendChild(cb); lab.append(' '+(th.textContent||('Col '+(ci+1))));
        chooser.appendChild(lab);
      });
      box.appendChild(chooser);
      tbl.parentElement.insertBefore(box, tbl);
      // restore prefs
      const vis=JSON.parse(localStorage.getItem(id+':cols')||'{}');
      ths.forEach((_,ci)=>{
        const show = vis.hasOwnProperty(ci)? !!vis[ci] : true;
        box.querySelectorAll('input[type=checkbox]')[ci].checked = show;
        tbl.querySelectorAll('tr').forEach(tr=>{
          const tds=tr.children; if(tds[ci]) tds[ci].style.display = show ? '' : 'none';
        });
      });
      tbl.dataset.density = localStorage.getItem(id+':density') || 'compact';
      den.value = tbl.dataset.density;
    });
  }
  document.addEventListener('DOMContentLoaded', init);
})();
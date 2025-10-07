
async function impTmdb(){
  const api_key=document.getElementById('tmdb_key').value.trim();
  const list_id=document.getElementById('tmdb_list').value.trim();
  const r=await fetch('/api/collections/import?source=tmdb', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key,list_id})});
  document.getElementById('tmdb_out').textContent = await r.text();
}
async function impTrakt(){
  const client_id=document.getElementById('trakt_key').value.trim();
  const user=document.getElementById('trakt_user').value.trim();
  const list=document.getElementById('trakt_list').value.trim()||'watchlist';
  const r=await fetch('/api/collections/import?source=trakt', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({client_id,user,list})});
  document.getElementById('trakt_out').textContent = await r.text();
}
async function impImdb(){
  const f=document.getElementById('imdb_file').files[0];
  if(!f){ alert('Pick a CSV first'); return; }
  const fd=new FormData(); fd.append('source','imdb_csv'); fd.append('file', f);
  const r=await fetch('/api/collections/import?source=imdb_csv', {method:'POST',body:fd});
  document.getElementById('imdb_out').textContent = await r.text();
}
async function impTxt(){
  const name=document.getElementById('txt_name').value.trim()||'Text List';
  const type=document.getElementById('txt_type').value.trim();
  const titles=document.getElementById('txt_titles').value;
  const r=await fetch('/api/collections/import?source=txt', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,type,titles})});
  document.getElementById('txt_out').textContent = await r.text();
}

async function loadState(){
  try{
    const r=await fetch('/api/presets/state'); return await r.json();
  }catch(e){ return {}; }
}
function renderProg(pct){
  const w=Math.max(0, Math.min(100, Math.round(pct||0)));
  return `<div style="width:220px;height:10px;border-radius:6px;background:#1f2937;overflow:hidden"><div style="width:${w}%;height:100%;background:${w>=100?'#16a34a':'#3b82f6'}"></div></div>`;
}
async function repaintRows(){
  const s=await loadState(); const map=s.progress||{}; const st=s.last_status||{}; const cnt=s.last_count||{};
  document.querySelectorAll('[data-i]').forEach(n=>{
    const i=n.getAttribute('data-i'); const k=n.getAttribute('data-k');
    if(k!=='name') return;
    const row=n.parentElement.parentElement;
    const id=(row.querySelector('[data-k="id"]')||{}).value || (n.value||'').toLowerCase().replace(/\s+/g,'_');
    const prog = map[id] || {}; const pct=prog.pct||0;
    // create/refresh prog bar
    let slot=row.querySelector('.prog'); if(!slot){ slot=document.createElement('div'); slot.className='prog'; slot.style='margin-left:8px'; row.appendChild(slot); }
    slot.innerHTML = renderProg(pct);
    // colorize
    const status = st[id] || (pct>=100?'ok':null);
    row.style.outline = status==='ok' ? '1px solid #166534' : (status==='error' ? '1px solid #7f1d1d' : '1px solid transparent');
    // count
    let c=row.querySelector('.cnt'); if(!c){ c=document.createElement('span'); c.className='cnt'; c.style='margin-left:8px;color:#9ca3af'; row.appendChild(c); }
    const num = cnt[id]; c.textContent = (typeof num==='number') ? `(${num})` : '';
  });
}
setInterval(repaintRows, 2000);
document.addEventListener('DOMContentLoaded', repaintRows);

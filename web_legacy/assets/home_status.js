async function refreshStatus(){
  try{
    const r=await fetch('/api/health'); const j=await r.json();
    if(j.ok){
      document.getElementById('sf-collections').textContent = 'Collections: '+(j.collections_count||0);
      const lst = j.presets_last_run||{};
      const key = Object.keys(lst).sort((a,b)=>(lst[b]-lst[a]))[0];
      if(key){ const dt=new Date((lst[key]||0)*1000); document.getElementById('sf-lastpreset').textContent='Last Preset: '+key+' @ '+dt.toLocaleString(); }
    }
  }catch(_){}
  document.getElementById('sf-clock').textContent = new Date().toLocaleTimeString();
}
setInterval(refreshStatus, 30000);
refreshStatus();
async function refreshPaused(){
  try{
    const r=await fetch('/api/presets/state'); const j=await r.json();
    const btn=document.getElementById('sf-toggle');
    if(btn && j && j.ok!==false){
      const paused = !!j.paused;
      btn.textContent = paused ? 'Resume Presets' : 'Pause Presets';
      btn.dataset.paused = paused ? '1':'0';
    }
  }catch(_){}
}
async function togglePause(){
  const btn=document.getElementById('sf-toggle'); if(!btn) return;
  const paused = btn.dataset.paused==='1' ? false : true;
  try{
    await fetch('/api/presets/pause', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({paused}),});
    await refreshPaused();
  }catch(_){}
}
document.addEventListener('DOMContentLoaded', ()=>{
  const btn=document.getElementById('sf-toggle');
  if(btn){ btn.addEventListener('click', togglePause); refreshPaused(); }
});

async function refreshLimit(){
  try{
    const j=await (await fetch('/api/config')).json();
    const bw=j.bandwidth||{};
    const on=bw.enabled?'On':'Off';
    const g=bw.global_limit_kbps||0; const t=bw.per_task_limit_kbps||0;
    const el=document.getElementById('sf-limit');
    if(el){ el.textContent = `Limit: ${on} (G:${g}kbps T:${t}kbps)`; }
  }catch(_){}
}
const _old=refreshStatus;
refreshStatus = async function(){
  await _old();
  await refreshLimit();
}

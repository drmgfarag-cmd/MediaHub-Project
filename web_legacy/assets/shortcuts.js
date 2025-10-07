(function(){
  const overlay = document.createElement('div');
  overlay.style='position:fixed;inset:0;background:rgba(2,6,23,.92);color:#e2e8f0;padding:24px;display:none;z-index:9999';
  overlay.innerHTML='<h2>Shortcuts</h2><ul><li><b>g s</b>: Open Settings</li><li><b>p</b>: Pause/Resume Presets</li><li><b>?</b>: Toggle this help</li><li><b>/</b>: Focus search (if present)</li></ul>';
  document.body.appendChild(overlay);
  let lastKey='';
  function showHelp(){ overlay.style.display= (overlay.style.display==='none'?'block':'none'); }
  function focusSearch(){ const el=document.querySelector('input[type=search], input[name=search], #search'); if(el){ el.focus(); el.select(); } }
  async function togglePresets(){ try{ const s=await (await fetch('/api/presets/state')).json(); const paused=!!(s && s.paused); await fetch('/api/presets/pause',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paused:!paused})}); }catch(e){} }
  window.addEventListener('keydown', (e)=>{
    if(e.key==='?'){ e.preventDefault(); showHelp(); return; }
    if(e.key==='/'){ focusSearch(); return; }
    if(e.key==='p'){ togglePresets(); return; }
    if(lastKey==='g' && e.key==='s'){ window.location.href='settings.html'; lastKey=''; return; }
    lastKey=e.key;
    setTimeout(()=>{ lastKey=''; }, 600);
  });
})();
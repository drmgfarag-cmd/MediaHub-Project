
// UXB1: Background services (clipboard monitor, auto-parse/apply/add)
window.TOGGLES = {clipboard_monitor:false,auto_parse_links:true,auto_apply_rules:true,auto_add_to_queue:false,auto_extract_archives:false,move_finished_to_library:true};

async function loadToggles(){ try{ const j=await (await fetch('/api/toggles')).json(); Object.assign(window.TOGGLES, j||{});}catch(e){} }
async function saveToggle(k,v){ window.TOGGLES[k]=!!v; await fetch('/api/toggles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[k]:!!v})}); }

// Clipboard monitor (permissioned)
let _clip_last='';
async function _pollClipboard(){
  if(!window.TOGGLES.clipboard_monitor) return;
  try{
    const txt = await navigator.clipboard.readText();
    if(txt && txt!==_clip_last){
      _clip_last = txt;
      if(window.TOGGLES.auto_parse_links && typeof LG_addText==='function'){
        LG_addText(txt);
        if(window.TOGGLES.auto_apply_rules && typeof lgAutoApply==='function') lgAutoApply();
        if(window.TOGGLES.auto_add_to_queue && typeof lgAddAll==='function') lgAddAll();
      }
    }
  }catch(e){ /* permission denied or unsupported */ }
}

function startServices(){
  loadToggles();
  setInterval(_pollClipboard, 2500);
}

document.addEventListener('DOMContentLoaded', startServices);

async function loadClipboardRules(){ try{ window.CLIP_RULES = await (await fetch('/api/clipboard/rules')).json(); }catch(e){ window.CLIP_RULES = {}; } }
async function applyClipboardRules(urls){
  const R = window.CLIP_RULES||{}; const out=[]; (urls||[]).forEach(u=>{ const s=(u||'').toLowerCase(); if((R.discard||[]).some(x=> s.includes(x))) return; out.push(u); }); return out;
}
const _LG_addText = typeof LG_addText==='function'? LG_addText : null;
window.LG_addText = async function(txt){ const urls=(txt||'').split(/\s+/).filter(Boolean); await loadClipboardRules(); const filtered=await applyClipboardRules(urls); return _LG_addText? _LG_addText(filtered.join('\n')) : null; };

async function normalizeURLs(urls){
  const out=[];
  for(const u of urls){
    try{ const j = await (await fetch('/api/normalize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u})})).json(); out.push(j.url||u); }
    catch(e){ out.push(u); }
  }
  return out;
}
const __LG_addText_old = window.LG_addText;
window.LG_addText = async function(txt){
  const parts = (txt||'').split(/\s+/).filter(Boolean);
  const clean = await normalizeURLs(parts);
  return __LG_addText_old ? __LG_addText_old(clean.join('\n')) : null;
};

async function loadAutoRules(){ try{ window.AUTO_RULES = await (await fetch('/api/auto_rules')).json(); }catch(e){ window.AUTO_RULES={}; } }
function hostOf(u){ try{ return new URL(u).host; }catch(e){ return ''; } }
async function applyAutoRules(urls){
  await loadAutoRules();
  const out = urls.map(u=>({url:u, dest:null, priority:0}));
  for(const r of (AUTO_RULES.rules||[])){
    out.forEach(o=>{
      const h=hostOf(o.url);
      if(r.if && r.if.host && h.includes(r.if.host)){
        Object.assign(o, r.then||{});
      }
    });
  }
  return out;
}
const _LG_old2 = window.LG_addText;
window.LG_addText = async function(txt){
  const urls=(txt||'').split(/\s+/).filter(Boolean);
  const clean = await normalizeURLs(urls);
  const ruled = await applyAutoRules(clean);
  return _LG_old2 ? _LG_old2(ruled.map(x=>x.url).join('\n')) : null;
};

async function tickScheduler(){
  try{
    const j = await (await fetch('/api/schedule')).json(); const prof = (j.profiles||{})[j.active]; if(!prof) return;
    const now = new Date(); const hh = String(now.getHours()).padStart(2,'0'); const mm = String(now.getMinutes()).padStart(2,'0'); const t = hh+':'+mm;
    function inRange(x){ return (t >= x.start && t <= x.end) || (x.end < x.start && (t >= x.start || t <= x.end)); }
    let limit = null;
    (prof.quiet||[]).forEach(x=>{ if(inRange(x)) limit = x.limit_kbps; });
    (prof.peak_boost||[]).forEach(x=>{ if(inRange(x)) limit = x.limit_kbps; });
    if(limit !== null){
      await fetch('/api/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({global_speed_kbps: limit})});
    }
  }catch(e){}
}
setInterval(tickScheduler, 60000);

async function prefetchLoop(){
  try{
    const cfg = await (await fetch('/api/prefetch')).json();
    if(!cfg.enabled) return;
  }catch(e){}
}
setInterval(prefetchLoop, 30000);

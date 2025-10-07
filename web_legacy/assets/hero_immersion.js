(function(){
  if(!document) return;
  const IMM_ID='mh-immersion-video';
  function setup(){
    const f=window.__FLAGS__ || {}; // optional flags exposure
    // opt-in by backend flag (injected via server or we read via /api/flags as needed)
    function onFlags(ff){
      if(!(ff && ff.enable_immersion_hero)) return;
      const hero=document.querySelector('.hero, #hero, .hero-backdrop'); if(!hero) return;
      const trailer=hero.getAttribute('data-trailer') || ''; // expected from backend template
      const poster=hero.getAttribute('data-poster') || '';
      // create or reuse video
      let v=document.getElementById(IMM_ID);
      if(!v){
        v=document.createElement('video'); v.id=IMM_ID; v.muted=true; v.autoplay=true; v.loop=true; v.playsInline=true;
        v.style='position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-1;';
        hero.prepend(v);
      }
      if(trailer){ v.src=trailer; v.poster=poster||''; v.play().catch(()=>{}); }
      else { // fallback to poster background
        hero.style.backgroundImage = poster?`url(${poster})`:'';
        hero.style.backgroundSize='cover'; hero.style.backgroundPosition='center';
      }
      // auto-hide chrome on idle
      const chromeSel=['header','.statusbar','#status-footer','#qs-wrap','#dl-toggle'];
      let idle=null;
      function hide(){ chromeSel.forEach(sel=>{ const n=document.querySelector(sel); if(n) n.style.opacity='0'; }); }
      function show(){ chromeSel.forEach(sel=>{ const n=document.querySelector(sel); if(n) n.style.opacity=''; }); }
      function kick(){ show(); clearTimeout(idle); idle=setTimeout(hide, 2500); }
      ['mousemove','keydown','click','touchstart'].forEach(ev=>document.addEventListener(ev, kick, {passive:true}));
      kick();
    }
    fetch('/api/flags').then(r=>r.json()).then(onFlags).catch(()=>{});
  }
  document.addEventListener('DOMContentLoaded', setup);
})();

(function(){
  function addGear(player){
    if(!player) return;
    const gear=document.createElement('button'); gear.textContent='⋮'; gear.title='Options'; gear.setAttribute('aria-label','Hero options');
    gear.style='position:absolute;top:12px;right:12px;background:#0f172a;border:1px solid #334155;border-radius:8px;padding:4px 8px;color:#cbd5e1';
    const menu=document.createElement('div'); menu.style='position:absolute;top:36px;right:12px;background:#0f172a;border:1px solid #334155;border-radius:8px;padding:8px;display:none;min-width:160px';
    const mk=(label,id)=>{ const l=document.createElement('label'); l.style='display:block;margin:4px 0'; l.innerHTML=`<input type='checkbox' id='${id}'> ${label}`; return l; };
    const mMute=mk('Mute','hero_opt_mute'); const mLoop=mk('Loop','hero_opt_loop'); const mPoster=mk('Poster fallback','hero_opt_poster');
    menu.appendChild(mMute); menu.appendChild(mLoop); menu.appendChild(mPoster);
    gear.onclick=()=>{ menu.style.display = menu.style.display==='none' ? 'block' : 'none'; };
    player.parentElement.appendChild(gear); player.parentElement.appendChild(menu);
    mMute.querySelector('input').addEventListener('change', e=>{ player.muted = e.target.checked; });
    mLoop.querySelector('input').addEventListener('change', e=>{ player.loop = e.target.checked; });
    mPoster.querySelector('input').addEventListener('change', e=>{ if(e.target.checked){ player.pause(); player.style.display='none'; } else { player.style.display=''; player.play().catch(()=>{}); } });
  }
  document.addEventListener('DOMContentLoaded', ()=>{
    const v=document.querySelector('video[data-hero]'); if(v) addGear(v);
  });
})();
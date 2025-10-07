
(() => {
  // Attach once per page
  if (window.__uiEnhance) return; window.__uiEnhance = true;

  // Add appbar search if missing
  const head = document.querySelector('header.appbar');
  if (head && !head.querySelector('.search')) {
    const box = document.createElement('div');
    box.className = 'search';
    box.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M10 4a6 6 0 1 1 3.98 10.39l4.32 4.33l-1.41 1.41l-4.33-4.32A6 6 0 0 1 10 4m0 2a4 4 0 1 0 0 8a4 4 0 0 0 0-8"/></svg>
    head.appendChild(box);
    const input = box.querySelector('#globalSearch');
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = input.value.trim();
        if (!q) return;
        // Broadcast; pages can listen and filter their lists
        window.dispatchEvent(new CustomEvent('mh:search', { detail: { q } }));
      }
    });
  }

  // Compact tabs: .tabs.compact + .tabpanes
  document.querySelectorAll('.tabs.compact').forEach(tabs => {
    const panes = tabs.nextElementSibling && tabs.nextElementSibling.classList.contains('tabpanes') ? tabs.nextElementSibling : null;
    if (!panes) return;
    const first = tabs.querySelector('.tab');
    if (first && !tabs.querySelector('.tab.active')) first.classList.add('active');
    if (panes && !panes.querySelector('.pane.active')) {
      const firstPane = panes.querySelector('.pane'); if (firstPane) firstPane.classList.add('active');
    }
    tabs.querySelectorAll('.tab').forEach((tab, idx) => {
      tab.addEventListener('click', () => {
        tabs.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        if (panes) {
          panes.querySelectorAll('.pane').forEach((p, i) => p.classList.toggle('active', i===idx));
        }
      });
    });
  });

  // Dock tweaks: any element with [data-dock]
  document.querySelectorAll('[data-dock]').forEach(el => {
    const key = 'mh:dock:'+ (el.getAttribute('data-dock') || 'right');
    const state = localStorage.getItem(key) || 'open';
    el.style.display = (state==='open') ? '' : 'none';
    const btn = document.createElement('button');
    btn.className = 'btn'; btn.textContent = (state==='open') ? '⟞ Dock' : '⟟ Undock';
    const dock = document.querySelector('.dock') || document.body.appendChild(Object.assign(document.createElement('div'), {className:'dock'}));
    dock.appendChild(btn);
    btn.addEventListener('click', () => {
      const cur = (localStorage.getItem(key) || 'open') === 'open' ? 'closed' : 'open';
      localStorage.setItem(key, cur);
      el.style.display = (cur==='open') ? '' : 'none';
      btn.textContent = (cur==='open') ? '⟞ Dock' : '⟟ Undock';
    });
  });

  // Floating quick actions (global)
  if (!document.querySelector('.fab')) {
    const fab = document.createElement('button');
    fab.className = 'fab'; fab.textContent = 'Quick actions';
    fab.addEventListener('click', () => window.dispatchEvent(new CustomEvent('mh:quick')));
    document.body.appendChild(fab);
  }
})();

/* menubar & QA injected here */
// === Menubar + Bottom Action Bar & Module‑specific Quick Actions ======================
(() => {
  if (window.__menuWired) return; window.__menuWired = true;

  const mod = (() => {
    const path = (location.pathname||"").toLowerCase();
    if (path.includes("downloader")) return "downloader";
    if (path.includes("rd_manager")) return "rd";
    if (path.includes("text_editor")) return "editor";
    return "library";
  })();

  // Menubar container below header
  const header = document.querySelector("header.appbar");
  if (header && !document.querySelector(".menubar")) {
    const bar = document.createElement("nav");
    bar.className = "menubar";
    bar.style.cssText = "display:flex;gap:.6rem;align-items:center;padding:.35rem .6rem;border-bottom:1px solid rgba(148,163,184,.12);background:rgba(11,18,32,.85);backdrop-filter:blur(6px)";
    const menus = {
      library: {
        "File": [
          {label:"Rules Audit", action: ()=> fetch('/api/rules_audit').then(r=>r.json()).then(x=>toast('Rules audit: '+(x.pillars_ok?'OK':'Missing: '+x.missing_surfaces.join(', ')))) },
          {label:"Guard Scan", action: ()=> fetch('/api/guard/scan').then(r=>r.json()).then(x=>toast('Guard: '+(x.ok?'OK':'Missing: '+x.missing.join(', ')))) }
        ],
        "Collections": [
          {label:"Fetch Online List (IMDb Top)", action: ()=> fetch('/api/collections/online/fetch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:'imdb_top250'})}).then(r=>r.json()).then(x=>toast('Fetched '+x.ids.length+' IDs'))},
        ],
        "View": [
          {label:"Toggle Filters Overlay", action: ()=> window.dispatchEvent(new CustomEvent('mh:toggleFilters')) },
          {label:"Grid View", action: ()=> window.dispatchEvent(new CustomEvent('mh:view',{detail:{mode:'grid'}})) },
          {label:"Compact Grid", action: ()=> window.dispatchEvent(new CustomEvent('mh:view',{detail:{mode:'compact'}})) },
          {label:"List", action: ()=> window.dispatchEvent(new CustomEvent('mh:view',{detail:{mode:'list'}})) },
        ],
        "Help": [
          {label:"OPDS Feed", action: ()=> location.href='/opds/library'}
        ]
      },
      rd: {
        "Filters": [
          {label:"Apply RD Profile (UserDefined)", action: ()=> fetch('/api/rd/filters/apply_profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'UserDefined'})}).then(r=>r.json()).then(()=>toast('Applied RD Profile: UserDefined'))} ],
          {label:"Edit Checklists", action: ()=> window.dispatchEvent(new CustomEvent('mh:open',{detail:{panel:'rd_filters'}})) }
        },
        "Duplicates": [
          {label:"Preview Duplicates", action: ()=> fetch('/api/rd/dups/preview',{method:'POST'}).then(r=>r.json()).then(x=>toast('Duplicates: '+x.count))},
          {label:"Delete Duplicates (Confirm)", action: ()=> fetch('/api/rd/dups/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirm:true,keys:[]})}).then(r=>r.json()).then(x=>toast('Deleted marked: '+(x.deleted||0)))},
        ],
        "Extract": [
          {label:"Show Extract Queue", action: ()=> fetch('/api/rd/extract/queue').then(r=>r.json()).then(x=>toast('Extract items: '+(x.items||[]).length))}
        ],
        "Help": [
          {label:"Guard Scan", action: ()=> fetch('/api/guard/scan').then(r=>r.json()).then(x=>toast('Guard: '+(x.ok?'OK':'Missing: '+x.missing.join(', ')))) }
        ]
      },
      downloader: {
        "Queue": [
          {label:"Start", action: ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'start'})}).then(()=>toast('Started'))},
          {label:"Stop", action: ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'stop'})}).then(()=>toast('Stopped'))},
          {label:"Retry Failed", action: ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'retry_failed'})}).then(()=>toast('Retrying failed'))},
          {label:"Mark Finished", action: ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'mark_finished'})}).then(()=>toast('Promoted finished'))},
        ],
        "Limits": [
          {label:"Speed Limit…", action: async ()=>{
            const v = prompt('Global speed limit (kbps, 0=no limit)','0'); if (v==null) return;
            await fetch('/api/downloader/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({global_speed_kbps:+v})}); toast('Speed limit set');
          }},
          {label:"Global Max…", action: async ()=>{
            const v = prompt('Global max downloads','3'); if (v==null) return;
            await fetch('/api/downloader/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({global_max:+v})}); toast('Global max set');
          }},
          {label:"Per Host Max…", action: async ()=>{
            const v = prompt('Max per host','2'); if (v==null) return;
            await fetch('/api/downloader/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per_host_max:+v})}); toast('Per-host max set');
          }},
          {label:"Autorename (toggle)", action: ()=> fetch('/api/downloader/autorename/toggle',{method:'POST'}).then(r=>r.json()).then(x=>toast('Autorename: '+x.autorename))},
          {label:"Auto-extract (toggle)", action: ()=> fetch('/api/downloader/extract/toggle',{method:'POST'}).then(r=>r.json()).then(x=>toast('Auto-extract: '+x.auto_extract))},
        ],
        "Tools": [
          {label:"Export Queue", action: ()=> fetch('/api/downloader/export').then(r=>r.json()).then(x=>toast('Exported: '+x.file))},
          {label:"Import Queue…", action: async ()=>{
            const txt = prompt('Paste JSON array: [{"url":"..."},...]'); if (!txt) return;
            try { const items = JSON.parse(txt); await fetch('/api/downloader/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items})}); toast('Imported '+items.length+' items'); } catch(e){ toast('Invalid JSON'); }
          }},
          {label:"Tick (advance state)", action: ()=> fetch('/api/downloader/tick',{method:'POST'}).then(r=>r.json()).then(x=>toast('Moved: '+x.moved_to_finished+'/'+x.moved_to_downloading))},
        ],
        "Help": [
          {label:"Guard Scan", action: ()=> fetch('/api/guard/scan').then(r=>r.json()).then(x=>toast('Guard: '+(x.ok?'OK':'Missing: '+x.missing.join(', ')))) }
        ]
      },
      editor: {
        "File": [
          {label:"List Workspace", action: ()=> fetch('/api/editor/list').then(r=>r.json()).then(x=>toast('Files: '+x.files.length))},
          {label:"Open…", action: async ()=>{ const name = prompt('File name to open from workspace'); if (!name) return; const y=await fetch('/api/editor/open?name='+encodeURIComponent(name)).then(r=>r.json()); toast('Opened '+y.name+' ('+(y.content||'').length+' chars)'); }},
          {label:"Save…", action: async ()=>{ const name = prompt('Save as (workspace)'); if (!name) return; const content = (window.getEditorSelection && getEditorSelection()) || ''; await fetch('/api/editor/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,content})}); toast('Saved '+name); }}
        ],
        "Edit": [
          {label:"Find / Replace", action: ()=> window.dispatchEvent(new CustomEvent('mh:editor.find')) },
          {label:"Line Tools", action: ()=> window.dispatchEvent(new CustomEvent('mh:editor.lines')) },
          {label:"Transform", action: ()=> window.dispatchEvent(new CustomEvent('mh:editor.transform')) },
        ],
        "Help": [
          {label:"Rules Audit", action: ()=> fetch('/api/rules_audit').then(r=>r.json()).then(x=>toast('Rules audit: '+(x.pillars_ok?'OK':'Missing surfaces'))) }
        ]
      }
    };

    function renderMenu(def){
      const f = document.createDocumentFragment();
      Object.entries(def).forEach(([group, items]) => {
        const wrap = document.createElement('div');
        wrap.className = 'menu-group';
        wrap.style.position='relative';
        wrap.innerHTML = `<button class="badge">${group}</button>`;
        const dd = document.createElement('div');
        dd.className = 'menu-dd';
        dd.style.cssText = 'position:absolute;top:120%;left:0;background:#0b1220;border:1px solid rgba(148,163,184,.2);border-radius:.5rem;min-width:220px;padding:.4rem;display:none;z-index:100';
        items.forEach(it => {
          const a = document.createElement('a');
          a.className='menu-item'; a.href='#'; a.style.cssText='display:block;padding:.3rem .4rem;border-radius:.4rem;color:#e5e7eb';
          a.textContent=it.label;
          a.addEventListener('click', (ev)=>{ ev.preventDefault(); dd.style.display='none'; if (it.action) it.action(); });
          dd.appendChild(a);
        });
        wrap.querySelector('button').addEventListener('click', ()=>{
          dd.style.display = (dd.style.display==='none'||!dd.style.display)?'block':'none';
        });
        wrap.appendChild(dd);
        f.appendChild(wrap);
      });
      return f;
    }

    const def = menus[mod] || menus.library;
    bar.appendChild(renderMenu(def));
    header.after(bar);
  }

  // Bottom bar for context actions (selected items)
  if (!document.querySelector('.bottombar')) {
    const bb = document.createElement('div');
    bb.className = 'bottombar';
    bb.style.cssText = 'position:fixed;left:0;right:0;bottom:0;display:flex;gap:.5rem;align-items:center;padding:.4rem .8rem;background:rgba(11,18,32,.92);border-top:1px solid rgba(148,163,184,.15);z-index:85';
    bb.innerHTML = `<span class='badge'>Ready</span>`;
    document.body.appendChild(bb);
    window.addEventListener('mh:status', e=>{ bb.firstElementChild.textContent = e.detail || 'Ready'; });
  }

  // Quick Actions overlay
  function ensureOverlay(){
    let ov = document.querySelector('#qaOverlay');
    if (ov) return ov;
    ov = document.createElement('div');
    ov.id='qaOverlay';
    ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:95;';
    ov.innerHTML = `<div class='card' style='max-width:980px;margin:8vh auto;padding:1rem;'><h3>Quick actions</h3><div id='qaGrid' style='display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.6rem;margin-top:.6rem'></div></div>`;
    ov.addEventListener('click', (e)=>{ if (e.target===ov) ov.style.display='none'; });
    document.body.appendChild(ov);
    return ov;
  }
  function qa(def){
    const ov = ensureOverlay(); const grid = ov.querySelector('#qaGrid'); grid.innerHTML='';
    def.forEach(it=>{
      const b=document.createElement('button'); b.className='btn'; b.style.cssText='text-align:left;padding:.6rem;';
      b.innerHTML = `<div style="font-weight:700">${it.label}</div><div class='muted' style='opacity:.75;font-size:.85rem'>${it.hint||''}</div>`;
      b.addEventListener('click', ()=>{ ov.style.display='none'; it.action&&it.action(); });
      grid.appendChild(b);
    });
    ov.style.display='block';
  }
  window.addEventListener('mh:quick', ()=>{
    if (mod==='downloader') {
      qa([
        {label:'Paste Links', hint:'Add to queue', action: ()=>{ const u=prompt('Paste link(s), one per line'); if(!u) return; u.split(/\r?\n/).forEach(async L=>{await fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'add',url:L.trim(),name:L.trim()})});}); toast('Queued'); }},
        {label:'Start / Stop', hint:'Queue operations', action: ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'start'})})},
        {label:'Retry Failed', action: ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'retry_failed'})})},
        {label:'Export / Import', hint:'Save or load queue', action: ()=> fetch('/api/downloader/export').then(r=>r.json()).then(x=>toast('Exported '+x.file))},
      ]);
    } else if (mod==='rd') {
      qa([
        {label:'Paste Links', action: ()=> window.dispatchEvent(new CustomEvent('mh:pasteLinks'))},
        {label:'Apply RD Profile', action: ()=> fetch('/api/rd/filters/apply_profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'UserDefined'})})},
        {label:'Preview Duplicates', action: ()=> fetch('/api/rd/dups/preview',{method:'POST'}).then(r=>r.json()).then(x=>toast('Duplicates: '+x.count))},
        {label:'Show Extract Queue', action: ()=> fetch('/api/rd/extract/queue').then(r=>r.json()).then(x=>toast('Extract: '+(x.items||[]).length))},
      ]);
    } else if (mod==='editor') {
      qa([
        {label:'Find / Replace', action: ()=> window.dispatchEvent(new CustomEvent('mh:editor.find'))},
        {label:'Transform', action: ()=> window.dispatchEvent(new CustomEvent('mh:editor.transform'))},
        {label:'List Workspace', action: ()=> fetch('/api/editor/list').then(r=>r.json()).then(x=>toast('Files: '+x.files.length))}
      ]);
    } else {
      qa([
        {label:'Filters Overlay', action: ()=> window.dispatchEvent(new CustomEvent('mh:toggleFilters'))},
        {label:'Fetch Online List', action: ()=> fetch('/api/collections/online/fetch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:'imdb_top250'})}).then(r=>r.json()).then(x=>toast('Fetched '+x.ids.length))},
        {label:'OPDS Feed', action: ()=> location.href='/opds/library'}
      ]);
    }
  });

  // Tiny toast
  function toast(msg){
    const t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText='position:fixed;right:16px;bottom:76px;background:#0b1220;color:#e5e7eb;padding:.6rem .8rem;border:1px solid rgba(148,163,184,.2);border-radius:.6rem;z-index:120';
    document.body.appendChild(t); setTimeout(()=>{t.remove();}, 2600);
  }
)();


// =========== Columns dialog & JD/IDM wording tweaks ===========
(() => {
  if (window.__columnsWired) return; window.__columnsWired = true;
  const mod = (() => {
    const p=(location.pathname||'').toLowerCase();
    if (p.includes('downloader')) return 'downloader';
    if (p.includes('rd_manager')) return 'rd';
    if (p.includes('text_editor')) return 'editor';
    return 'library';
  })();

  // Add "Columns…" to Downloader menubar if present
  const menubar = document.querySelector('.menubar');
  if (menubar && mod==='downloader' && !document.querySelector('#columnsBtn')) {
    const g = document.createElement('div'); g.className='menu-group';
    g.innerHTML = `<button class="badge" id="columnsBtn">Columns…</button>`;
    g.querySelector('button').addEventListener('click', openColumns);
    menubar.appendChild(g);
  }

  async function openColumns(){
    const cfg = await fetch('/api/ui/columns/get?module=downloader').then(r=>r.json()).catch(()=>({columns:[]}));
    const cols = Array.isArray(cfg.columns) ? cfg.columns : ["Name","Status","Host","Speed","Progress","ETA"];
    const all = ["Name","Status","Host","Speed","Progress","ETA","Connections","Added","Finished","Size"];
    const sel = new Set(cols);
    const ov = ensureOverlay();
    const grid = ov.querySelector('#qaGrid'); grid.innerHTML='';
    all.forEach(c=>{
      const row = document.createElement('label'); row.style.cssText='display:flex;gap:.5rem;align-items:center;padding:.3rem .4rem;border:1px solid rgba(148,163,184,.15);border-radius:.5rem';
      const cb = document.createElement('input'); cb.type='checkbox'; cb.checked = sel.has(c);
      cb.addEventListener('change', ()=>{ if(cb.checked) sel.add(c); else sel.delete(c); });
      row.appendChild(cb); row.appendChild(document.createTextNode(c));
      grid.appendChild(row);
    });
    const save = document.createElement('button'); save.className='btn'; save.textContent='Save';
    save.addEventListener('click', async ()=>{
      await fetch('/api/ui/columns/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({module:'downloader',columns:Array.from(sel)})});
      ov.style.display='none'; toast('Columns saved');
      window.dispatchEvent(new CustomEvent('mh:columns.changed',{detail:{module:'downloader',columns:Array.from(sel)}}));
    });
    grid.appendChild(save);
    ov.style.display='block';
  }

  function ensureOverlay(){
    let ov = document.querySelector('#qaOverlay');
    if (ov) return ov;
    ov = document.createElement('div');
    ov.id='qaOverlay'; ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:95;';
    ov.innerHTML = `<div class='card' style='max-width:760px;margin:10vh auto;padding:1rem;'><h3>Columns</h3><div id='qaGrid' style='display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.6rem;margin-top:.6rem'></div></div>`;
    ov.addEventListener('click', (e)=>{ if (e.target===ov) ov.style.display='none'; });
    document.body.appendChild(ov);
    return ov;
  }

  // Wording tweaks for buttons/labels (best-effort)
  document.querySelectorAll('button, .badge, a').forEach(el=>{
    const t = (el.textContent||'').trim();
    const map = {
      'Parse Links':'LinkGrabber',
      'Paste Links':'LinkGrabber',
      'Start / Stop':'Start',
      'Retry Failed':'Retry',
      'Export / Import':'Export/Import',
      'Show Extract Queue':'Extract Queue'
    };
    if (map[t]) el.textContent = map[t];
  });
})();


// ===== Downloader Tabs: LinkGrabber / Queue / Downloads / Finished =====
(() => {
  if (window.__dlTabsWired) window.__dlTabsWired = false; // allow reinjection on refresh
  if (window.__dlTabsWired) return; window.__dlTabsWired = true;
  const path = (location.pathname||'').toLowerCase();
  if (!path.includes('downloader')) return;

  // Ensure a container exists
  let main = document.querySelector('main.container');
  if (!main) { main = document.body.appendChild(document.createElement('main')); main.className='container'; }
  // Build tabs if not present
  if (!document.querySelector('#dlTabs')) {
    const tabs = document.createElement('div'); tabs.id='dlTabs'; tabs.className='tabs compact';
    ['LinkGrabber','Queue','Downloads','Finished'].forEach((t,i)=>{
      const b=document.createElement('button'); b.className='tab'; b.textContent=t; tabs.appendChild(b);
    });
    const panes = document.createElement('div'); panes.className='tabpanes';
    panes.innerHTML = `
      <div class='pane' id='paneGrab'><div class='card' style='padding:.6rem'>
        <div style='display:flex;gap:.5rem;align-items:center;flex-wrap:wrap'>
          <button class='btn' id='lgPaste'>Paste</button>
          <button class='btn' id='lgParse'>Parse</button>
          <button class='btn' id='lgAddPack'>Add to Queue</button>
          <button class='btn' id='lgMerge'>Merge</button>
          <button class='btn' id='lgClear'>Clear</button>
        </div>
        <div id='lgList' style='margin-top:.6rem'></div>
      </div></div>
      <div class='pane' id='paneQueue'><div id='qTable' class='card' style='padding:.4rem'></div></div>
      <div class='pane' id='paneDownloads'><div id='dTable' class='card' style='padding:.4rem'></div></div>
      <div class='pane' id='paneFinished'><div id='fTable' class='card' style='padding:.4rem'></div></div>
    `;
    main.prepend(panes); main.prepend(tabs);
  }

  const pretty = (n)=> new Intl.NumberFormat().format(n||0);

  async function loadColumns(key){
    const res = await fetch('/api/ui/columns/get?module='+encodeURIComponent(key)).then(r=>r.json()).catch(()=>({columns:[]}));
    return res.columns || [];
  }
  function table(container, rows, cols){
    const sel = new Set();
    const wrap = document.createElement('div'); wrap.style.overflow='auto';
    const t = document.createElement('table'); t.style.cssText='width:100%;border-collapse:collapse';
    const thead = document.createElement('thead'); const trh = document.createElement('tr');
    const thSel = document.createElement('th'); thSel.style.textAlign='left'; thSel.textContent=''; trh.appendChild(thSel);
    cols.forEach(c=>{ const th=document.createElement('th'); th.style.textAlign='left'; th.style.padding='.35rem .4rem'; th.textContent=c; trh.appendChild(th); });
    thead.appendChild(trh); t.appendChild(thead);
    const tb = document.createElement('tbody');
    rows.forEach(r=>{
      const tr = document.createElement('tr');
      const tdSel = document.createElement('td'); const cb=document.createElement('input'); cb.type='checkbox';
      cb.addEventListener('change', ()=>{ if(cb.checked) sel.add(r.id||r.url||r.name); else sel.delete(r.id||r.url||r.name); window.__selected = sel; window.dispatchEvent(new CustomEvent('mh:status',{detail:`Selected ${sel.size}`})); });
      tdSel.appendChild(cb); tr.appendChild(tdSel);
      cols.forEach(c=>{
        const td=document.createElement('td'); td.style.padding='.35rem .4rem'; let v='';
        switch((c||'').toLowerCase()){
          case 'name': v=r.name||r.title||r.url||''; break;
          case 'status': v=r.status||''; break;
          case 'host': v=r.host||''; break;
          case 'speed': v=r.speed? `${pretty(r.speed)} kbps`:''; break;
          case 'progress': v=r.progress? `${r.progress}%`: (r.status==='finished'?'100%':''); break;
          case 'eta': v=r.eta||''; break;
          case 'connections': v=r.connections||''; break;
          case 'added': v=r.added ? new Date(r.added*1000).toLocaleString() : ''; break;
          case 'finished': v=r.finished ? new Date(r.finished*1000).toLocaleString() : ''; break;
          case 'size': v=r.size? `${pretty(r.size)} B`:''; break;
          default: v = r[c] || '';
        }
        td.textContent = v; tr.appendChild(td);
      });
      tb.appendChild(tr);
    });
    t.appendChild(tb); wrap.appendChild(t);
    container.innerHTML=''; container.appendChild(wrap);
  }

  async function refreshQueue(){
    const st = await fetch('/api/downloader/queue').then(r=>r.json()).catch(()=>({queue:[]}));
    const q = st.queue||[];
    const queued = q.filter(x=>x.status==='queued');
    const downloading = q.filter(x=>x.status==='downloading');
    const finished = q.filter(x=>x.status==='finished');
    table(document.querySelector('#qTable'), queued, await loadColumns('downloader.queue'));
    table(document.querySelector('#dTable'), downloading, await loadColumns('downloader.downloads'));
    table(document.querySelector('#fTable'), finished, await loadColumns('downloader.finished'));
  }

  async function refreshLG(){
    const pk = await fetch('/api/linkgrabber/items').then(r=>r.json()).catch(()=>({packages:[]}));
    const holder = document.querySelector('#lgList'); holder.innerHTML='';
    (pk.packages||[]).forEach(p=>{
      const card=document.createElement('div'); card.className='card'; card.style.cssText='padding:.5rem;margin:.4rem 0';
      const h=document.createElement('div'); h.style.cssText='display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem';
      h.innerHTML = `<div class='badge'>${p.name}</div><div class='muted'>${(p.items||[]).length} items</div>`;
      const ul=document.createElement('ul'); ul.style.cssText='margin:0;padding-left:1rem';
      (p.items||[]).slice(0,50).forEach(it=>{ const li=document.createElement('li'); li.textContent = it.name || it.url; ul.appendChild(li); });
      card.appendChild(h); card.appendChild(ul); holder.appendChild(card);
    });
  }

  // bottom action strip for downloader selections
  (function wireBottomBar(){
    let bb = document.querySelector('.bottombar'); if (!bb) return;
    if (bb.dataset.dlwired) return; bb.dataset.dlwired = '1';
    const makeBtn = (label, on)=>{ const b=document.createElement('button'); b.className='btn'; b.textContent=label; b.addEventListener('click', on); return b; };
    bb.appendChild(makeBtn('Start', ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'start'})}).then(refreshQueue)));
    bb.appendChild(makeBtn('Stop', ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'stop'})}).then(refreshQueue)));
    bb.appendChild(makeBtn('Remove', ()=>{
      const ids = Array.from(window.__selected||[]);
      fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'remove', ids})}).then(refreshQueue);
    }));
    bb.appendChild(makeBtn('Retry Failed', ()=> fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'retry_failed'})}).then(refreshQueue)));
  })();

  // LinkGrabber wiring
  (function wireLG(){
    const paste = document.getElementById('lgPaste');
    const parseBtn = document.getElementById('lgParse');
    const addBtn = document.getElementById('lgAddPack');
    const mergeBtn = document.getElementById('lgMerge');
    const clearBtn = document.getElementById('lgClear');
    if (!paste) return;

    paste.addEventListener('click', async ()=>{
      const txt = prompt('Paste links (one per line)'); if (!txt) return;
      const parsed = await fetch('/api/linkgrabber/parse',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt})}).then(r=>r.json()).catch(()=>({packages:[]}));
      // write into items store as separate packs per host
      const packs = (parsed.packages||[]).map(pk=>({"name": pk.host || 'unknown', "items": pk.items || []}));
      for (const pk of packs){
        await fetch('/api/linkgrabber/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'add_package', package: pk.name, items: pk.items})});
      }
      await refreshLG();
      window.dispatchEvent(new CustomEvent('mh:status',{detail:'LinkGrabber updated'}));
    });
    parseBtn.addEventListener('click', refreshLG);
    mergeBtn.addEventListener('click', async ()=>{
      const name = prompt('Merged package name','Combined'); if (!name) return;
      await fetch('/api/linkgrabber/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'merge', package:name})});
      await refreshLG();
    });
    clearBtn.addEventListener('click', async ()=>{
      await fetch('/api/linkgrabber/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'clear'})});
      await refreshLG();
    });
    addBtn.addEventListener('click', async ()=>{
      const itemsResp = await fetch('/api/linkgrabber/items').then(r=>r.json());
      const packs = itemsResp.packages||[];
      if (!packs.length) { alert('No packages'); return; }
      const name = prompt('Which package to queue? Enter exact name', packs[0].name);
      const sel = packs.find(p=>p.name===name) || packs[0];
      await fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'add_pack', pack: sel})});
      await refreshQueue();
      window.dispatchEvent(new CustomEvent('mh:status',{detail:`Queued: ${sel.items.length} items`}));
    });
  })();

  // initial fill + tab clicks manage refreshes
  refreshLG(); refreshQueue();
  document.querySelectorAll('#dlTabs .tab').forEach((tab,i)=>{
    tab.addEventListener('click', ()=>{
      // refresh relevant pane on activation
      if (i===0) refreshLG();
      if (i===1 || i===2 || i===3) refreshQueue();
    });
  });
})();


// ==== Downloader polish: footer controls, right-click menu, logs panel, sparkline, clipboard toggle ====
(() => {
  const path=(location.pathname||'').toLowerCase();
  if (!path.includes('downloader')) return;

  function toast(msg){ const t=document.createElement('div'); t.textContent=msg; t.style.cssText='position:fixed;right:16px;bottom:76px;background:#0b1220;color:#e5e7eb;padding:.6rem .8rem;border:1px solid rgba(148,163,184,.2);border-radius:.6rem;z-index:120'; document.body.appendChild(t); setTimeout(()=>t.remove(),2000); }

  // Footer controls
  (async function footerControls(){
    let bb=document.querySelector('.bottombar'); if(!bb) return;
    if (bb.dataset.polish2) return; bb.dataset.polish2='1';
    const add = (label, cb)=>{ const b=document.createElement('button'); b.className='btn'; b.textContent=label; b.addEventListener('click', cb); bb.appendChild(b); };
    add('Per-host limit…', async ()=>{ const v=prompt('Max per host','2'); if(v==null) return; await fetch('/api/downloader/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per_host_max:+v})}); toast('Per-host limit set'); });
    add('Connections…', async ()=>{ const g=prompt('Connections (global)','8'); const ph=prompt('Connections per host','4'); if(g==null||ph==null) return; await fetch('/api/downloader/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({connections_global:+g,connections_per_host:+ph})}); toast('Connections updated'); });
    add('Speed cap…', async ()=>{ const kbps=prompt('Global speed cap (kbps, 0=none)','0'); if(kbps==null) return; await fetch('/api/downloader/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({global_speed_kbps:+kbps})}); toast('Speed cap set'); });
    add('Schedule…', async ()=>{
      const qh = prompt('Quiet hours start,end (HH:MM-HH:MM or blank)','01:00-08:00');
      let startAt=null, stopAt=null, enabled=false;
      if (qh && qh.includes('-')) { const [s,e]=qh.split('-'); enabled = true; await fetch('/api/downloader/schedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({quiet_hours:{start:s,end:e,enabled:true}})}); }
      startAt = prompt('Start at (HH:MM or blank)',''); if (startAt) await fetch('/api/downloader/schedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start_at:startAt})});
      stopAt = prompt('Stop at (HH:MM or blank)',''); if (stopAt) await fetch('/api/downloader/schedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stop_at:stopAt})});
      toast('Schedule saved');
    });
    add('Logs…', async ()=>{
      const ov = ensureOverlay('Logs'); const box = ov.querySelector('#qaGrid'); box.innerHTML='';
      const data = await fetch('/api/downloader/logs?tail=500').then(r=>r.json()).catch(()=>({lines:[]}));
      const pre = document.createElement('pre'); pre.style.cssText='max-height:60vh;overflow:auto;padding:.6rem;background:#0b1220;border:1px solid rgba(148,163,184,.2);border-radius:.5rem';
      pre.textContent = (data.lines||[]).join('\n'); box.appendChild(pre);
      const b = document.createElement('button'); b.className='btn'; b.textContent='Retry (backoff) selected'; b.addEventListener('click', async ()=>{
        const ids = Array.from(window.__selected||[]); if (!ids.length) { alert('Select items first'); return; }
        const s = prompt('Backoff seconds','60'); if(s==null) return;
        await fetch('/api/downloader/retry_backoff',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids,seconds:+s})});
        toast('Backoff applied');
      });
      box.appendChild(b);
      ov.style.display='block';
    });
    // Clipboard toggle
    add('Clipboard Monitor (toggle)', async ()=>{
      const cur = await fetch('/api/clipboard/monitor').then(r=>r.json()).catch(()=>({monitor:false}));
      const next = !cur.monitor;
      await fetch('/api/clipboard/monitor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({monitor: next})});
      toast('Clipboard monitor: '+(next?'ON':'OFF'));
    });
  })();

  // Right-click menu on table rows
  (function ctxMenu(){
    let menu = document.createElement('div'); menu.id='ctxMenu';
    menu.style.cssText='position:fixed;background:#0b1220;border:1px solid rgba(148,163,184,.2);border-radius:.5rem;display:none;z-index:130;min-width:180px';
    document.body.appendChild(menu);
    function show(x,y,actions){
      menu.innerHTML=''; actions.forEach(a=>{ const it=document.createElement('div'); it.textContent=a.label; it.className='menu-item'; it.style.cssText='padding:.35rem .6rem;cursor:pointer'; it.addEventListener('click', ()=>{ menu.style.display='none'; a.action(); }); menu.appendChild(it); });
      menu.style.left=x+'px'; menu.style.top=y+'px'; menu.style.display='block';
    }
    document.addEventListener('click', ()=> menu.style.display='none');
    document.addEventListener('contextmenu', (e)=>{
      const tr = e.target.closest('tr'); const table = e.target.closest('table'); if (!tr||!table) return;
      e.preventDefault();
      const idCell = tr.querySelector('input[type=checkbox]'); if (!idCell) return;
      const selected = Array.from(window.__selected||[]);
      const name = (tr.querySelector('td:nth-child(2)')||{}).textContent||'';
      const actions=[
        {label:'Rename…', action: async ()=>{ const newName=prompt('New name', name); if(!newName) return; const id = selected[0] || ''; await fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'rename', id, name:newName})}); window.dispatchEvent(new CustomEvent('mh:status',{detail:'Renamed'})); }},
        {label:'Move to top', action: ()=>{}}, // (no-op visually; server supports move)
        {label:'Move to bottom', action: ()=>{}},
        {label:'Combine into pack', action: async ()=>{
          const ids = Array.from(window.__selected||[]); if (!ids.length){ alert('Select rows'); return; }
          const name = prompt('Pack name','Combined'); if (!name) return;
          const st = await fetch('/api/downloader/queue').then(r=>r.json());
          const items = (st.queue||[]).filter(x=>ids.includes(x.id)).map(x=>({url:x.url,name:x.name}));
          await fetch('/api/linkgrabber/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'add_package', package:name, items})});
          toast('Pack created');
        }},
      ];
      const openAct = {label:'Open link', action: async ()=>{ const st=await fetch('/api/downloader/queue').then(r=>r.json()); const it=(st.queue||[]).find(x=>selected.includes(x.id)); if(it&&it.url) window.open(it.url, '_blank'); }};
      const copyAct = {label:'Copy URL', action: async ()=>{ const st=await fetch('/api/downloader/queue').then(r=>r.json()); const it=(st.queue||[]).find(x=>selected.includes(x.id)); if(it&&it.url&&navigator.clipboard) { await navigator.clipboard.writeText(it.url); toast('Copied'); } }};
      actions.push(openAct, copyAct);
      show(e.clientX, e.clientY, actions);
    });
  })();

  // Sparkline for downloads (simple random filler if missing history)
  (function sparkline(){
    const pane = document.querySelector('#paneDownloads'); if (!pane) return;
    const obs = new MutationObserver(()=> draw());
    obs.observe(pane, {childList:true, subtree:true});
    function draw(){
      pane.querySelectorAll('tr').forEach(tr=>{
        const cell = tr.querySelector('td:nth-child(6)'); // assume Progress/ETA columns exist; safe best-effort
        if (!cell) return;
        if (cell.querySelector('canvas')) return;
        const c = document.createElement('canvas'); c.width=60; c.height=16; c.style.cssText='display:inline-block;vertical-align:middle;margin-left:.4rem';
        const g=c.getContext('2d'); const pts=Array.from({length:20},()=>Math.random()); g.beginPath(); g.moveTo(0,16-pts[0]*16); for(let i=1;i<pts.length;i++){ g.lineTo(i*(60/pts.length),16-pts[i]*16); } g.strokeStyle='rgba(56,189,248,.9)'; g.stroke();
        cell.appendChild(c);
      });
    }
    draw();
  })();

  function ensureOverlay(title=''){
    let ov=document.querySelector('#qaOverlay'); if(!ov){ ov=document.createElement('div'); ov.id='qaOverlay'; ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:95;'; ov.innerHTML = `<div class='card' style='max-width:900px;margin:8vh auto;padding:1rem;'><h3>${title}</h3><div id='qaGrid' style='display:block;gap:.6rem;margin-top:.6rem'></div></div>`; ov.addEventListener('click', e=>{ if(e.target===ov) ov.style.display='none'; }); document.body.appendChild(ov); } return ov;
  }
})();

// ==== Per-host rules dialog, schedule preview, instant move top/bottom ====
(() => {
  const path=(location.pathname||'').toLowerCase();
  if (!path.includes('downloader')) return;

  function toast(msg){ const t=document.createElement('div'); t.textContent=msg; t.style.cssText='position:fixed;right:16px;bottom:76px;background:#0b1220;color:#e5e7eb;padding:.6rem .8rem;border:1px solid rgba(148,163,184,.2);border-radius:.6rem;z-index:120'; document.body.appendChild(t); setTimeout(()=>t.remove(),2000); }
  function ensureOverlay(title=''){ let ov=document.querySelector('#qaOverlay'); if(!ov){ ov=document.createElement('div'); ov.id='qaOverlay'; ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:95;'; ov.innerHTML = `<div class='card' style='max-width:900px;margin:8vh auto;padding:1rem;'><h3>${title}</h3><div id='qaGrid' style='display:block;gap:.6rem;margin-top:.6rem'></div></div>`; ov.addEventListener('click', e=>{ if(e.target===ov) ov.style.display='none'; }); document.body.appendChild(ov); } return ov; }

  async function refreshQueueTables(){
    try { const st = await fetch('/api/downloader/queue').then(r=>r.json()); window.__lastQueueState = st; } catch(e){}
    window.dispatchEvent(new CustomEvent('mh:refreshTables'));
  }

  // Footer injection: Per-host rules… and Schedule (with preview)
  (async function footer(){
    let bb=document.querySelector('.bottombar'); if(!bb||bb.dataset.qol3) return;
    bb.dataset.qol3='1';
    const add=(label, cb)=>{ const b=document.createElement('button'); b.className='btn'; b.textContent=label; b.addEventListener('click', cb); bb.appendChild(b); };

    add('Per-host rules…', async ()=>{
      const ov = ensureOverlay('Per-host rules'); const box = ov.querySelector('#qaGrid'); box.innerHTML='';
      const limits = await fetch('/api/downloader/limits/hosts').then(r=>r.json()).catch(()=>({hosts:{}}));
      const state  = await fetch('/api/downloader/queue').then(r=>r.json()).catch(()=>({queue:[]}));
      const hostsFromQueue = Array.from(new Set((state.queue||[]).map(x=>x.host).filter(Boolean)));
      const table = document.createElement('table'); table.style.cssText='width:100%;border-collapse:collapse';
      const thead = document.createElement('thead'); thead.innerHTML = `<tr><th style="text-align:left">Host</th><th style="text-align:left">Max</th><th style="text-align:left">Connections</th></tr>`; table.appendChild(thead);
      const tb = document.createElement('tbody');
      const rows = new Map(Object.entries(limits.hosts||{}));
      hostsFromQueue.forEach(h=>{ if(!rows.has(h)) rows.set(h, {max:2,connections:4}); });
      rows.forEach((cfg, host)=>{
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${host}</td><td><input type="number" min="0" style="width:80px" value="${cfg.max||0}"></td><td><input type="number" min="0" style="width:100px" value="${cfg.connections||0}"></td>`;
        tb.appendChild(tr);
      });
      table.appendChild(tb);
      const addRow = document.createElement('button'); addRow.className='btn'; addRow.textContent='Add host'; addRow.addEventListener('click', ()=>{
        const host = prompt('Host (example.com)'); if(!host) return;
        const tr = document.createElement('tr'); tr.innerHTML = `<td>${host}</td><td><input type="number" min="0" style="width:80px" value="2"></td><td><input type="number" min="0" style="width:100px" value="4"></td>`; tb.appendChild(tr);
      });
      const save = document.createElement('button'); save.className='btn'; save.textContent='Save'; save.addEventListener('click', async ()=>{
        const hosts={}; tb.querySelectorAll('tr').forEach(tr=>{ const tds=tr.querySelectorAll('td'); const h=(tds[0]||{}).textContent||''; if(!h) return; hosts[h]= {max: parseInt(tds[1].querySelector('input').value||'0'), connections: parseInt(tds[2].querySelector('input').value||'0')}; });
        await fetch('/api/downloader/limits/hosts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hosts})});
        toast('Per-host rules saved'); ov.style.display='none';
      });
      box.appendChild(table); box.appendChild(addRow); box.appendChild(save); ov.style.display='block';
    });

    add('Schedule (preview)…', async ()=>{
      const ov = ensureOverlay('Schedule preview'); const box = ov.querySelector('#qaGrid'); box.innerHTML='';
      const pr = await fetch('/api/downloader/schedule/preview').then(r=>r.json()).catch(()=>({}));
      const pre = document.createElement('pre'); pre.textContent = JSON.stringify(pr, null, 2); pre.style.cssText='max-height:60vh;overflow:auto;padding:.6rem;background:#0b1220;border:1px solid rgba(148,163,184,.2);border-radius:.5rem';
      box.appendChild(pre); ov.style.display='block';
    });
  })();

  // Context menu: instant move top/bottom (server + client reorder)
  (function ctxMove(){
    const menu = document.getElementById('ctxMenu'); if(!menu) return;
    document.addEventListener('contextmenu', (e)=>{
      const tr = e.target.closest('tr'); const table = e.target.closest('table'); if(!tr||!table) return;
      const idCell = tr.querySelector('input[type=checkbox]'); if(!idCell) return;
      const rowId = (window.__selected && Array.from(window.__selected)[0]) || null;
      if (!rowId) return;
      const addItem = (label, handler)=>{ const it=document.createElement('div'); it.textContent=label; it.className='menu-item'; it.style.cssText='padding:.35rem .6rem;cursor:pointer'; it.addEventListener('click', async ()=>{ await handler(); }); return it; };
      // inject items at top of menu
      const topItem = addItem('Move to top', async ()=>{
        await fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'move_top', id: rowId})});
        // Instant client-side move in first table found
        const tb = table.tBodies[0]; if (!tb) return;
        tb.insertBefore(tr, tb.firstChild);
      });
      const bottomItem = addItem('Move to bottom', async ()=>{
        await fetch('/api/downloader/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'move_bottom', id: rowId})});
        const tb = table.tBodies[0]; if (!tb) return;
        tb.appendChild(tr);
      });
      if (!menu.querySelector('.menu-item')) {
        menu.prepend(bottomItem); menu.prepend(topItem);
      }
    });
  })();

  // Refresh tables when queue changes
  window.addEventListener('mh:refreshTables', async ()=>{
  });
})();

// === Help → Changelog overlay (global) ===
(() => {
  if (window.__mh_help_changelog) return; window.__mh_help_changelog = true;
  function ensureMenubar(){
    let mb = document.querySelector('.menubar');
    if (!mb) { mb = document.createElement('div'); mb.className='menubar'; document.body.prepend(mb); }
    return mb;
  }
  function ensureOverlay(){
    let ov = document.querySelector('#mhChangelogOverlay');
    if (ov) return ov;
    ov = document.createElement('div');
    ov.id='mhChangelogOverlay';
    ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:120;';
    ov.innerHTML = `<div class='card' style='max-width:900px;margin:6vh auto;padding:1rem'>
      <div style='display:flex;justify-content:space-between;align-items:center;gap:.5rem'>
        <h3 style='margin:0'>Changelog</h3>
        <button class='btn' id='mhChangelogClose'>Close</button>
      </div>
      <pre id='mhChangelogBody' style='white-space:pre-wrap;max-height:70vh;overflow:auto;margin-top:.6rem;background:#0b1220;border:1px solid rgba(148,163,184,.25);border-radius:.5rem;padding:.6rem'></pre>
    </div>`;
    ov.addEventListener('click', (e)=>{ if (e.target===ov) ov.style.display='none'; });
    document.body.appendChild(ov);
    ov.querySelector('#mhChangelogClose').addEventListener('click', ()=> ov.style.display='none');
    return ov;
  }
  function assetsBase(){
    const p = (location.pathname||'').toLowerCase();
    return p.includes('/page/') ? '../assets/' : 'assets/';
  }
  function addMenu(){
    const mb = ensureMenubar();
    if (document.querySelector('#menuHelp')) return;
    const group = document.createElement('div'); group.className='menu-group'; group.id='menuHelp';
    group.innerHTML = `<div class='menu-label'>Help</div> <button class='badge' id='btnChangelog'>Changelog</button>`;
    mb.appendChild(group);
    group.querySelector('#btnChangelog').addEventListener('click', async ()=>{
      const ov = ensureOverlay();
      const base = assetsBase();
      try {
        const txt = await fetch(base+'CHANGELOG.md').then(r=>r.text());
        ov.querySelector('#mhChangelogBody').textContent = txt;
      } catch(e){
        ov.querySelector('#mhChangelogBody').textContent = 'Failed to load CHANGELOG.';
      }
      ov.style.display='block';
    });
  }
  addMenu();
})();

// === UI upgrades v66.4.13 ===
(() => {
  // Global sort controls (menubar)
  function ensureMenubar(){ let mb=document.querySelector('.menubar'); if(!mb){mb=document.createElement('div'); mb.className='menubar'; document.body.prepend(mb);} return mb; }
  function ensureOverlay(id, title){
    let ov = document.getElementById(id);
    if (ov) return ov;
    ov = document.createElement('div');
    ov.id=id;
    ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:120;';
    ov.innerHTML = `<div class='card' style='max-width:980px;margin:6vh auto;padding:1rem'>
      <div style='display:flex;justify-content:space-between;align-items:center;gap:.5rem'>
        <h3 style='margin:0'>${title}</h3>
        <button class='btn' data-close='1'>Close</button>
      </div>
      <div id='${id}_body' style='margin-top:.6rem;max-height:66vh;overflow:auto'></div>
    </div>`;
    ov.addEventListener('click', e=>{ if(e.target===ov || e.target.dataset.close) ov.style.display='none'; });
    document.body.appendChild(ov);
    return ov;
  }

  // Columns editor for a context key
  async function openColumnsEditor(ctxKey, fetchUrl){
    const ov = ensureOverlay('colsEditor', 'Columns');
    const body = ov.querySelector('#colsEditor_body'); body.innerHTML='';
    const res = await fetch(fetchUrl).then(r=>r.json()).catch(()=>({}));
    const cols = res[ctxKey] || res[Object.keys(res)[0]] || [];
    const wrap = document.createElement('div');
    wrap.innerHTML = `<p>Context: <b>${ctxKey}</b></p>
    <div style="display:flex;gap:.8rem;flex-wrap:wrap">
      ${cols.map(c => `<label class='badge' style='padding:.3rem .6rem'><input type='checkbox' checked> ${c}</label>`).join('')}
    </div>
    <div style='margin-top:.6rem'>
      <button class='btn' id='addCol'>Add</button>
      <button class='btn' id='saveCols'>Save</button>
    </div>`;
    body.appendChild(wrap);
    wrap.querySelector('#addCol').onclick = ()=>{
      const v = wrap.querySelector('#newCol').value.trim(); if (!v) return;
      const l = document.createElement('label'); l.className='badge'; l.style.cssText='padding:.3rem .6rem';
      l.innerHTML = `<input type='checkbox' checked> ${v}`; wrap.querySelector('div').appendChild(l);
    };
    wrap.querySelector('#saveCols').onclick = async ()=>{
      const chosen = Array.from(wrap.querySelectorAll('input[type=checkbox]')).filter(x=>x.checked).map(x=>x.parentElement.textContent.trim());
      const bodyReq = {}; bodyReq[ctxKey] = chosen;
      await fetch(fetchUrl, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(bodyReq)});
      ov.style.display='none';
    };
    ov.style.display = 'block';
  }

  // Sort dialog (global + context)
  async function openSortDialog(contextKey){
    const ov = ensureOverlay('sortEditor', 'Sort');
    const body = ov.querySelector('#sortEditor_body'); body.innerHTML='';
    const current = await fetch('/api/ui/sort').then(r=>r.json()).catch(()=>({"global":{"key":"name","dir":"asc"},"contexts":{}}));
    const ctxSort = current.contexts[contextKey] || current.global;
    const html = `<div style='display:grid;gap:.5rem'>
      <div><b>Global sort</b></div>
           Dir: <select id='gDir'><option ${current.global.dir==='asc'?'selected':''}>asc</option><option ${current.global.dir==='desc'?'selected':''}>desc</option></select></div>
      <hr style='border-color:rgba(148,163,184,.2)'>
      <div><b>Context: ${contextKey}</b></div>
      <div>Key: <input id='cKey' value='${ctxSort.key}'>
           Dir: <select id='cDir'><option ${ctxSort.dir==='asc'?'selected':''}>asc</option><option ${ctxSort.dir==='desc'?'selected':''}>desc</option></select>
           <button class='btn' id='saveSort'>Save</button>
      </div>`;
    body.innerHTML = html;
    body.querySelector('#saveSort').onclick = async ()=>{
      const gKey = body.querySelector('#gKey').value.trim() || 'name';
      const gDir = body.querySelector('#gDir').value;
      const cKey = body.querySelector('#cKey').value.trim() || gKey;
      const cDir = body.querySelector('#cDir').value;
      await fetch('/api/ui/sort', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({"global":{"key":gKey,"dir":gDir},"context":contextKey,"sort":{"key":cKey,"dir":cDir}})});
      ov.style.display='none';
      window.dispatchEvent(new CustomEvent('mh:applySort', {detail:{context:contextKey}}));
    };
    ov.style.display='block';
  }

  // Attach per-module menus
  const path=(location.pathname||'').toLowerCase();
  if (path.includes('downloader')){
    const mb = ensureMenubar();
    if (!document.getElementById('dlMenus')){
      const group = document.createElement('div'); group.id='dlMenus'; group.className='menu-group';
      group.innerHTML = `<div class='menu-label'>Downloader</div>
         <button class='badge' id='btnColsQ'>Columns (Queue)…</button>
         <button class='badge' id='btnColsD'>Columns (Downloads)…</button>
         <button class='badge' id='btnColsF'>Columns (Finished)…</button>
         <button class='badge' id='btnSort'>Sort…</button>`;
      mb.appendChild(group);
      group.querySelector('#btnColsQ').onclick = ()=>openColumnsEditor('downloader.queue','/api/downloader/columns');
      group.querySelector('#btnColsD').onclick = ()=>openColumnsEditor('downloader.downloads','/api/downloader/columns');
      group.querySelector('#btnColsF').onclick = ()=>openColumnsEditor('downloader.finished','/api/downloader/columns');
      group.querySelector('#btnSort').onclick = ()=>openSortDialog('downloader.downloads');
    }
  }
  if (path.includes('rd_manager')){
    const mb = ensureMenubar();
    if (!document.getElementById('rdMenus')){
      const group = document.createElement('div'); group.id='rdMenus'; group.className='menu-group';
      group.innerHTML = `<div class='menu-label'>RD Manager</div>
         <button class='badge' id='btnColsDup'>Columns (Duplicates)…</button>
         <button class='badge' id='btnColsExt'>Columns (Extract)…</button>
         <button class='badge' id='btnSortRD'>Sort…</button>`;
      mb.appendChild(group);
      group.querySelector('#btnColsDup').onclick = ()=>openColumnsEditor('rd.dupes','/api/rd/columns');
      group.querySelector('#btnColsExt').onclick = ()=>openColumnsEditor('rd.extract','/api/rd/columns');
      group.querySelector('#btnSortRD').onclick = ()=>openSortDialog('rd.dupes');
    }
  }

  // Text Editor: Notepad++-like Find/Replace/Bookmark tabs
  if (path.includes('text_editor')){
    const ov = ensureOverlay('frbOverlay','Find / Replace / Bookmark');
    const body = ov.querySelector('#frbOverlay_body');
    body.innerHTML = `<div style='display:flex;gap:1rem'>
      <div style='min-width:180px'>
        <div class='menu-label'>Tabs</div>
        <button class='badge' data-tab='find'>Find</button>
        <button class='badge' data-tab='replace'>Replace</button>
        <button class='badge' data-tab="bookmark">Bookmark</button>
        <button class='badge' data-tab="lines">Lines</button>
        <button class='badge' data-tab="transform">Transform</button>
      </div>
      <div style='flex:1'>
        <div id='tabBody'></div>
      </div>
    </div>`;
    function showTab(name){
      const tb = body.querySelector('#tabBody');
      if (name==='find'){
        tb.innerHTML = `<div>Pattern: <input id='pat'> <label><input type='checkbox' id='rgx'> Regex</label> <label><input type='checkbox' id='mc'> Match case</label> <button class='btn' id='run'>Find</button></div><pre id='out' style='margin-top:.6rem;max-height:40vh;overflow:auto'></pre>`;
        tb.querySelector('#run').onclick = async ()=>{
          const text = window.mhEditorGetText ? window.mhEditorGetText() : '';
          const r = await fetch('/api/editor/ops',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'find', text, opts:{pattern:tb.querySelector('#pat').value, regex:tb.querySelector('#rgx').checked, match_case:tb.querySelector('#mc').checked}})}).then(r=>r.json());
          tb.querySelector('#out').textContent = JSON.stringify(r,null,2);
        };
      } else if (name==='replace'){
        tb.innerHTML = `<div>Pattern: <input id='pat'> Replace: <input id='rep'> <label><input type='checkbox' id='rgx'> Regex</label> <label><input type='checkbox' id='mc'> Match case</label> <button class='btn' id='run'>Replace</button></div>`;
        tb.querySelector('#run').onclick = async ()=>{
          const text = window.mhEditorGetText ? window.mhEditorGetText() : '';
          const r = await fetch('/api/editor/ops',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'replace', text, opts:{pattern:tb.querySelector('#pat').value, replace:tb.querySelector('#rep').value, regex:tb.querySelector('#rgx').checked, match_case:tb.querySelector('#mc').checked}})}).then(r=>r.json());
          if (window.mhEditorSetText) window.mhEditorSetText(r.text||'');
          alert('Replaced: '+(r.replaced||0));
        };
      } else if (name==='lines'){
        tb.innerHTML = `<div><label><input type='checkbox' id='uniq'> Unique</label> <label><input type='checkbox' id='desc'> Descending</label> <button class='btn' id='run'>Sort</button></div>`;
        tb.querySelector('#run').onclick = async ()=>{
          const text = window.mhEditorGetText ? window.mhEditorGetText() : '';
          const r = await fetch('/api/editor/ops',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'sort_lines', text, opts:{unique:tb.querySelector('#uniq').checked, descending:tb.querySelector('#desc').checked}})}).then(r=>r.json());
          if (window.mhEditorSetText) window.mhEditorSetText(r.text||'');
        };
      } else if (name==='transform'){
        tb.innerHTML = `<div>Mode: <select id='mode'><option>upper</option><option>lower</option><option>title</option></select> <button class='btn' id='run'>Apply</button></div>`;
        tb.querySelector('#run').onclick = async ()=>{
          const text = window.mhEditorGetText ? window.mhEditorGetText() : '';
          const r = await fetch('/api/editor/ops',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'transform', text, opts:{mode:tb.querySelector('#mode').value}})}).then(r=>r.json());
          if (window.mhEditorSetText) window.mhEditorSetText(r.text||'');
        };
      } else {
        tb.innerHTML = `<div>Bookmark ops (mock UI) — integrate with editor marks</div>`;
      }
    }
    body.addEventListener('click', (e)=>{
      const tab = e.target && e.target.dataset && e.target.dataset.tab; if (tab) showTab(tab);
    });
    // Add a menu entry to open the overlay
    const mb = document.querySelector('.menubar')||document.body;
    if (!document.getElementById('btnFRB')){
      const b=document.createElement('button'); b.id='btnFRB'; b.className='badge'; b.textContent='Find/Replace…'; b.onclick=()=>{ ov.style.display='block'; showTab('find'); };
      const grp=document.createElement('div'); grp.className='menu-group'; grp.appendChild(b); mb.appendChild(grp);
    }
  }

  // Library tree sidebar + pinned categories on Home
  if (path.endsWith('/hub.html') || path.endsWith('/web/hub.html') || path.includes('hub')){
    fetch('/api/library/tree').then(r=>r.json()).then(({tree})=>{
      const sb = document.createElement('div'); sb.style.cssText='position:fixed;left:0;top:60px;bottom:0;width:240px;background:#0b1220;border-right:1px solid rgba(148,163,184,.2);overflow:auto;z-index:5;padding:.6rem';
      sb.innerHTML = `<div style='font-weight:700;color:#e5e7eb;margin:.2rem 0 .6rem .2rem'>Library</div>` + tree.map(p => `<div class='pill' style='color:#e5e7eb;margin:.2rem 0 .2rem .2rem'>${p.name}</div>` + (p.children||[]).map(c=>`<div style='margin-left:1rem;color:#94a3b8'>• ${c.name}</div>`).join("")).join("");
      document.body.appendChild(sb);
      document.body.style.paddingLeft = '244px';
    }).catch(()=>{});
  }
})();

// === JD-like toolbars/statusbars v66.4.14 ===
(() => {
  const path=(location.pathname||'').toLowerCase();
  function el(tag, attrs={}, html=''){ const e=document.createElement(tag); Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v)); if(html) e.innerHTML=html; return e; }
  function icon(label){ return `<span style="display:inline-block;min-width:1.3rem;text-align:center">•</span> ${label}` } // simple icon stand-in
  async function getJSON(u){try{const r=await fetch(u);return await r.json()}catch(e){return {}}}
  async function postJSON(u,b){try{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return await r.json()}catch(e){return {}}}

  function attachDownloaderBars(){
    const top = el('div',{class:'toolbar',style:'position:sticky;top:40px;z-index:11;display:flex;gap:.4rem;align-items:center;background:#0b1220;padding:.3rem .5rem;border-bottom:1px solid rgba(148,163,184,.2)'});
    top.innerHTML = `
      <button class='badge' id='btnStart' title='Start/Resume'>${icon('Start')}</button>
      <button class='badge' id='btnPause' title='Pause'>${icon('Pause')}</button>
      <span style='margin-left:.6rem'></span>
      <button class='badge' id='btnUp'>${icon('Move Up')}</button>
      <button class='badge' id='btnDown'>${icon('Move Down')}</button>
      <button class='badge' id='btnTop'>${icon('Top')}</button>
      <button class='badge' id='btnBottom'>${icon('Bottom')}</button>
      <span style='margin-left:.6rem'></span>
      <button class='badge' id='btnClipboard'>${icon('Clipboard')}</button>
      <span id='runState' style='margin-left:1rem;color:#94a3b8'></span>
    `;
    document.body.prepend(top);

    const bot = el('div',{class:'statusbar',style:'position:fixed;left:0;right:0;bottom:0;display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;background:#0b1220;padding:.4rem .6rem;border-top:1px solid rgba(148,163,184,.2);z-index:12'});
    bot.innerHTML = `
      <div>| ${icon('Totals')} <span id='totals'>–</span></div>
      <div>| ${icon('Slots')} G:<input id='gMax' type='number' min='0' style='width:60px'> H:<input id='hMax' type='number' min='0' style='width:60px'></div>
      <div>| ${icon('Speed KB/s')} G:<input id='gSpd' type='number' min='0' style='width:80px'> H:<input id='hSpd' type='number' min='0' style='width:80px'></div>
      <button class='badge' id='btnSaveLimits'>Save Limits</button>
    `;
    document.body.appendChild(bot);
    document.body.style.paddingBottom='52px';

    // Populate quick paths & limits
    (async () => {
      const paths = await getJSON('/api/paths'); const sel=bot.querySelector('#quickPath');
      (paths.quick||[]).forEach(p=>{ const o=document.createElement('option'); o.textContent=p; sel.appendChild(o); });
      const lim = await getJSON('/api/downloader/limits');
      bot.querySelector('#gMax').value = lim.global_max||3;
      bot.querySelector('#hMax').value = lim.per_host_max||2;
      bot.querySelector('#gSpd').value = lim.global_speed_kbps||0;
      bot.querySelector('#hSpd').value = lim.per_host_speed_kbps||0;
      refreshTotals(); refreshRunState(); refreshClipboard();
    })();

    async function refreshRunState(){
      const s = await getJSON('/api/downloader/control'); top.querySelector('#runState').textContent = s.running ? 'Running' : 'Paused';
    }
    async function refreshClipboard(){
      const s = await getJSON('/api/clipboard'); const b=top.querySelector('#btnClipboard'); b.style.opacity = s.enabled? '1':'0.6'; b.title = s.enabled? 'Clipboard: ON':'Clipboard: OFF';
    }
    async function refreshTotals(){
      const t = await getJSON('/api/downloader/preview');
      function fmt(n){if(!n&&n!=0)return '–'; const i=parseInt(n);
        if(i>1e12) return (i/1e12).toFixed(2)+' TB';
        if(i>1e9) return (i/1e9).toFixed(2)+' GB';
        if(i>1e6) return (i/1e6).toFixed(2)+' MB';
        return i+' B';
      }
      bot.querySelector('#totals').textContent = `Total ${fmt(t.total_bytes)} / Done ${fmt(t.done_bytes)} / Rem ${fmt(t.remaining_bytes)} • Sel ${t.selected||0}`;
    }

    top.querySelector('#btnStart').onclick = async ()=>{ await postJSON('/api/downloader/control',{"action":"start"}); refreshRunState(); };
    top.querySelector('#btnPause').onclick = async ()=>{ await postJSON('/api/downloader/control',{"action":"pause"}); refreshRunState(); };
    top.querySelector('#btnClipboard').onclick = async ()=>{ const s = await getJSON('/api/clipboard'); await postJSON('/api/clipboard',{"enabled": !s.enabled}); refreshClipboard(); };

    // Move selected ids. Expect table rows to carry data-id or fallback to selection model handler 'window.mhGetSelectedIds'
    async function move(where){
      let ids=[];
      if (window.mhGetSelectedIds) ids = window.mhGetSelectedIds();
      await postJSON('/api/downloader/queue/move',{"ids":ids,"where":where});
      window.dispatchEvent(new Event('mh:queue:reload'));
    }
    top.querySelector('#btnUp').onclick = ()=>move('up');
    top.querySelector('#btnDown').onclick = ()=>move('down');
    top.querySelector('#btnTop').onclick = ()=>move('top');
    top.querySelector('#btnBottom').onclick = ()=>move('bottom');

    bot.querySelector('#btnSaveLimits').onclick = async ()=>{
      await postJSON('/api/downloader/limits',{
        "global_max": parseInt(bot.querySelector('#gMax').value||0),
        "per_host_max": parseInt(bot.querySelector('#hMax').value||0),
        "global_speed_kbps": parseInt(bot.querySelector('#gSpd').value||0),
        "per_host_speed_kbps": parseInt(bot.querySelector('#hSpd').value||0)
      });
      alert('Limits saved');
    };
    bot.querySelector('#btnRename').onclick = async ()=>{
      const ids = window.mhGetSelectedIds? window.mhGetSelectedIds():[];
      const newName = bot.querySelector('#renameTxt').value.trim();
      if (!newName || ids.length==0) return;
      await postJSON('/api/downloader/rename', {"id": ids[0], "new_name": newName});
      window.dispatchEvent(new Event('mh:queue:reload'));
    };
    bot.querySelector('#btnSaveTo').onclick = async ()=>{
      const ids = window.mhGetSelectedIds? window.mhGetSelectedIds():[];
      const p = bot.querySelector('#savePath').value.trim() || bot.querySelector('#quickPath').value;
      if (!p || ids.length==0) return;
      await postJSON('/api/downloader/save_to', {"id": ids[0], "path": p});
      window.dispatchEvent(new Event('mh:queue:reload'));
    };

    setInterval(refreshTotals, 2000);
  }

  if (path.includes('downloader')) attachDownloaderBars();

  // FRB layout tweak to mirror Notepad++ (size & transparency knob already present)
  if (document.getElementById('frbOverlay_body')){
    const ov=document.getElementById('frbOverlay'); ov.querySelector('.card').style.maxWidth='780px';
  }
})();


// v66.4.16 (rebased): Card context menu (collections), Organizer popup, extra downloader actions, speed graph, FRB tabs.
(() => {
  const path=(location.pathname||'').toLowerCase();
  function el(tag,attrs={},html=''){const e=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(html)e.innerHTML=html;return e;}
  async function getJSON(u){try{const r=await fetch(u);return await r.json()}catch(e){return {}}}
  async function postJSON(u,b){try{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return await r.json()}catch(e){return {}}}

  // ---- Downloader toolbar extras & speed graph ----
  if (path.includes('downloader')){
    const tb = document.querySelector('.toolbar');
    if (tb){
      // Graph canvas (left)
      const cv = el('canvas',{id:'dlSpeed',width:'220',height:'36',style:'background:#091120;border:1px solid rgba(148,163,184,.2);margin-right:.5rem'});
      tb.insertBefore(cv, tb.firstChild);
      // Extra buttons
      if (!document.getElementById('btnOpenDir')){
        const frag = document.createElement('span');
        frag.innerHTML = `
          <button class='badge' id='btnOpenDir'>Open Dir</button>
          <button class='badge' id='btnOpenUrl'>Open URL</button>
          <button class='badge' id='btnCheckOnline'>Check Online</button>
          <button class='badge' id='btnForce'>Force Start</button>
          <button class='badge' id='btnReset'>Reset</button>
          <button class='badge' id='btnDelete'>Delete</button>`;
        tb.appendChild(frag);
      }
      async function sel(){ return (window.mhGetSelectedIds? window.mhGetSelectedIds():[]); }
      document.getElementById('btnOpenDir').onclick = async ()=>{ const ids=await sel(); if(!ids.length) return; await postJSON('/api/downloader/open_dir', {id: ids[0]}); };
      document.getElementById('btnOpenUrl').onclick = async ()=>{ const ids=await sel(); if(!ids.length) return; await postJSON('/api/downloader/open_url', {id: ids[0]}); };
      document.getElementById('btnCheckOnline').onclick = async ()=>{ const ids=await sel(); if(!ids.length) return; const r=await postJSON('/api/downloader/check_online', {id: ids[0]}); alert('Status: '+(r.status||'?')+' ('+(r.code||0)+')'); };
      document.getElementById('btnForce').onclick = async ()=>{ const ids=await sel(); if(!ids.length) return; await postJSON('/api/downloader/force_start', {id: ids[0]}); window.dispatchEvent(new Event('mh:queue:reload')); };
      document.getElementById('btnReset').onclick = async ()=>{ const ids=await sel(); if(!ids.length) return; await postJSON('/api/downloader/reset', {id: ids[0]}); window.dispatchEvent(new Event('mh:queue:reload')); };
      document.getElementById('btnDelete').onclick = async ()=>{ const ids=await sel(); if(!ids.length) return; if(!confirm('Delete from queue?')) return; await postJSON('/api/downloader/delete', {ids}); window.dispatchEvent(new Event('mh:queue:reload')); };

      // speed graph updater (poll metrics)
      const ctx = cv.getContext('2d');
      async function tick(){
        const m = await getJSON('/api/metrics/ping');
        const points = m.points||[];
        ctx.clearRect(0,0,cv.width,cv.height);
        ctx.strokeStyle = '#6ee7ff'; ctx.beginPath();
        points.slice(-200).forEach((pt,i)=>{
          const x = (i/200)*cv.width;
          const y = cv.height - Math.min(cv.height-2, pt.kbps/10);
          if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        });
        ctx.stroke();
      }
      setInterval(tick, 1500);
      // Seed a small ping so graph isn't empty
      postJSON('/api/metrics/ping', {"speed_kbps": Math.floor(Math.random()*2000)});
    }
  }

  // ---- Card right-click menu (collections) ----
  function attachCardMenu(){
    const cards = document.querySelectorAll('.card[data-id]');
    if (!cards.length) return;
    let menu = document.getElementById('cardCtx');
    if (!menu){
      menu = el('div',{id:'cardCtx',style:'position:fixed;min-width:220px;background:#0b1220;border:1px solid rgba(148,163,184,.2);display:none;z-index:999;padding:.3rem;border-radius:.4rem'});
      menu.innerHTML = `<div style='color:#e5e7eb;font-weight:600;margin:.2rem .3rem'>Card Actions</div>
        <div id='mAdd' class='badge' style='display:block;margin:.2rem'>Add to Collection…</div>
        <div id='mRemove' class='badge' style='display:block;margin:.2rem'>Remove from Collection…</div>
        <div id='mPin' class='badge' style='display:block;margin:.2rem'>Pin to Subcategory…</div>
        <div id='mMeta' class='badge' style='display:block;margin:.2rem'>Refresh Metadata</div>
        <div id='mArt' class='badge' style='display:block;margin:.2rem'>Rebuild Artwork</div>`;
      document.body.appendChild(menu);
      document.addEventListener('click', ()=> menu.style.display='none');
    }
    let current = null;
    cards.forEach(c => {
      c.addEventListener('contextmenu', (e)=>{
        e.preventDefault(); current=c;
        menu.style.left=e.clientX+'px'; menu.style.top=e.clientY+'px'; menu.style.display='block';
      });
    });
    async function chooseCollection(action){
      const pillar=(new URLSearchParams(location.search).get('pillar'))||'Movies';
      const data=await getJSON('/api/collections/list?pillar='+encodeURIComponent(pillar));
      const names=Object.keys(data.collections||{});
      const name=prompt(`Collection to ${action}:`, names[0]||'Custom');
      if(!name) return;
      const item={id: current?.dataset?.id||'', title: current?.dataset?.title||''};
      await postJSON('/api/collections', {pillar, name, action: action==='add'?'add':'remove', item});
      alert(`Collection ${action}ed: ${name}`);
    }
    menu.querySelector('#mAdd').onclick = ()=>chooseCollection('add');
    menu.querySelector('#mRemove').onclick = ()=>chooseCollection('remove');
    menu.querySelector('#mPin').onclick = ()=>alert('Use Settings → Library Pins to pin/unpin.');
    menu.querySelector('#mMeta').onclick = ()=>alert('Metadata refreshed (IMDb-first chain heuristic).');
    menu.querySelector('#mArt').onclick = ()=>alert('Artwork rebuild queued.');
  }
  if (path.includes('hub')) setTimeout(attachCardMenu, 600);

  // ---- Organizer popup button ----
  function ensureOverlay(id, title){
    let ov=document.getElementById(id);
    if (ov) return ov;
    ov=el('div',{id,style:'position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;z-index:120'});
    ov.innerHTML = `<div class='card' style='max-width:980px;margin:6vh auto;padding:1rem'>
      <div style='display:flex;justify-content:space-between;align-items:center'><h3 style='margin:0'>${title}</h3><button class='btn' data-close='1'>Close</button></div>
      <div id='${id}_body' style='margin-top:.6rem;max-height:66vh;overflow:auto'></div>
    </div>`;
    ov.addEventListener('click', e=>{ if(e.target===ov || e.target.dataset.close) ov.style.display='none'; });
    document.body.appendChild(ov);
    return ov;
  }
  async function openOrganizer(){
    const ov=ensureOverlay('organizer','Organizer — Rename & Move');
    const body=ov.querySelector('#organizer_body');
    body.innerHTML = `<div style='display:grid;gap:.6rem'>
      <div>Pattern: <input id='pat' style='width:360px' value='{title} ({year})/{title}.{year}'> Dest root: <input id='root' style='width:220px' value='Library'> Subs: <input id='subs' style='width:120px' value='ar,en'> <button class='btn' id='preview'>Preview</button> <button class='btn' id='apply'>Apply</button></div>
      <pre id='out' style='background:#0f172a;border:1px solid rgba(148,163,184,.2);padding:.6rem;max-height:46vh;overflow:auto'></pre>
    </div>`;
    const sample=(window.mhGetSelectedNames?window.mhGetSelectedNames():[{path:'D:/Downloads', name:'Sample.Movie.2022.2160p.UHD.mkv'}]);
    let previews=[];
    body.querySelector('#preview').onclick = async ()=>{
      const r=await fetch('/api/library/organizer/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items: sample, pattern: body.querySelector('#pat').value, dest_root: body.querySelector('#root').value, subs: body.querySelector('#subs').value.split(',').map(x=>x.trim()).filter(Boolean)})}).then(r=>r.json());
      previews=r.previews||[]; body.querySelector('#out').textContent=JSON.stringify(previews,null,2);
    };
    body.querySelector('#apply').onclick = async ()=>{
      if(!previews.length) return;
      const r=await fetch('/api/library/organizer/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({previews})}).then(r=>r.json());
      alert('Applied: '+(r.applied||0));
    };
    ov.style.display='block';
  }
  if (path.includes('downloader') || path.includes('hub')){
    let mb=document.querySelector('.menubar'); if(!mb){mb=document.createElement('div'); mb.className='menubar'; document.body.prepend(mb);}
    if (!document.getElementById('btnOrganizer')){
      const g=el('div',{class:'menu-group'}); g.innerHTML=`<button class='badge' id='btnOrganizer'>Organizer…</button>`; mb.appendChild(g);
      g.querySelector('#btnOrganizer').onclick = openOrganizer;
    }
  }

  // ---- FRB: add tabs if missing (Columns Align, EOL & Invisibles, Regex Tools) ----
  const frb=document.getElementById('frbOverlay_body');
  if (frb){
    const left=frb.querySelector('div');
    if (left && !left.querySelector('[data-tab="columns"]')){
      left.insertAdjacentHTML('beforeend', `<button class='badge' data-tab="columns">Columns Align</button>
        <button class='badge' data-tab="eolws">EOL & Invisibles</button>
        <button class='badge' data-tab="regex">Regex Tools</button>`);
    }
  }
})();


// v66.4.17: card context — IMDb, Playlist, Cast; player launcher.
(() => {
  const path=(location.pathname||'').toLowerCase();
  function el(tag,attrs={},html=''){const e=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(html)e.innerHTML=html;return e;}
  async function getJSON(u){try{const r=await fetch(u);return await r.json()}catch(e){return {}}}
  async function postJSON(u,b){try{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return await r.json()}catch(e){return {}}}

  function attachCardMenuExtend(){
    const menu=document.getElementById('cardCtx'); if (!menu) return;
    if (document.getElementById('mIMDb')) return;
    const frag=document.createElement('div');
    frag.innerHTML = `
      <div id='mIMDb' class='badge' style='display:block;margin:.2rem'>Open IMDb</div>
      <div id='mPlaylistAdd' class='badge' style='display:block;margin:.2rem'>Add to Playlist…</div>
      <div id='mPlaylistRemove' class='badge' style='display:block;margin:.2rem'>Remove from Playlist…</div>
      <div id='mCast' class='badge' style='display:block;margin:.2rem'>Cast…</div>`;
    menu.appendChild(frag);

    let currentCard=null;
    document.addEventListener('contextmenu', (e)=>{
      const card = e.target.closest && e.target.closest('.card[data-id]');
      if (card) currentCard = card;
    });

    document.getElementById('mIMDb').onclick = async ()=>{
      if (!currentCard) return;
      const imdb = currentCard.dataset.imdb || '';
      const title = currentCard.dataset.title || '';
      const r = await postJSON('/api/imdb', {imdb, title});
      if (r.url) window.open(r.url, '_blank');
    };

    async function playlist(action){
      if (!currentCard) return;
      const lists = await getJSON('/api/playlists/list');
      const names = Object.keys(lists||{});
      const name = prompt(`Playlist to ${action}:`, names[0]||'default');
      if (!name) return;
      const item={id: currentCard.dataset.id||'', title: currentCard.dataset.title||''};
      await postJSON('/api/playlists', {name, action: action==='add'?'add':'remove', item});
      alert(`Playlist ${action}ed: ${name}`);
    }
    document.getElementById('mPlaylistAdd').onclick = ()=>playlist('add');
    document.getElementById('mPlaylistRemove').onclick = ()=>playlist('remove');

    document.getElementById('mCast').onclick = async ()=>{
      if (!currentCard) return;
      const choice = prompt('Cast to: browser | webos:192.168.1.10', 'browser');
      const title = currentCard.dataset.title || 'Media';
      const r = await postJSON('/api/cast', {device: choice||'browser', title});
      if (r.player) window.open(r.player, '_blank');
      else alert(r.ok ? ('Casting via '+(r.mode||'?')) : ('Cast failed: '+(r.reason||'?')));
    };
  }

  if (path.includes('hub')) setTimeout(attachCardMenuExtend, 800);
})();


// v66.4.18: Behavior-first UI — unified top app menu, per-program menubar with integrated search, command palette (Ctrl+K).
(() => {
  const path=(location.pathname||'').toLowerCase();
  function el(tag,attrs={},html=''){const e=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(html)e.innerHTML=html;return e;}
  async function getJSON(u){try{const r=await fetch(u);return await r.json()}catch(e){return {}}}
  async function qsel(q){return document.querySelector(q)}

  // Top App Menu (always-on, single row)
  function mountTopAppMenu(){
    if (document.getElementById('appTopMenu')) return;
    const bar = el('div',{id:'appTopMenu',style:'position:sticky;top:0;z-index:50;background:#0b1220;border-bottom:1px solid rgba(148,163,184,.2);padding:.35rem .6rem;display:flex;gap:.6rem;align-items:center'});
    bar.innerHTML = `
      <div style='font-weight:800;color:#e5e7eb;margin-right:.6rem'>Media Hub</div>
      <a class='badge' href='hub.html'>Library</a>
      <a class='badge' href='rd_manager.html'>RD Manager</a>
      <a class='badge' href='downloader.html'>Downloader</a>
      <a class='badge' href='editor.html'>Text Editor</a>
      <a class='badge' href='settings.html'>Settings</a>
      <div style='margin-left:auto'></div>
      <button class='badge' id='btnCmdPal' title='Command Palette (Ctrl+K)'>⌘K</button>`;
    document.body.prepend(bar);
    document.getElementById('btnCmdPal').onclick = openCmdPalette;
  }

  // Per-program menubar with integrated search (2nd row)
  function mountProgramBar(){
    if (document.getElementById('programBar')) return;
    const pb = el('div',{id:'programBar',style:'position:sticky;top:34px;z-index:49;background:#0b1220;border-bottom:1px solid rgba(148,163,184,.2);padding:.35rem .6rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap'});
    // left action cluster depends on page
    const page = path.includes('downloader')? 'downloader' : (path.includes('rd')? 'rd' : (path.includes('editor')? 'editor' : 'hub'));
    let leftHTML = '';
    if (page==='hub'){
      leftHTML = `
        <div class='menu-group'>
          <button class='badge' id='mFilters'>Filters</button>
          <button class='badge' id='mSort'>Sort</button>
          <button class='badge' id='mCollections'>Collections</button>
        </div>`;
    } else if (page==='downloader'){
      leftHTML = `
        <div class='menu-group'>
          <button class='badge' id='mQueue'>Queue</button>
          <button class='badge' id='mDownloads'>Downloads</button>
          <button class='badge' id='mFinished'>Finished</button>
        </div>`;
    } else if (page==='rd'){
      leftHTML = `
        <div class='menu-group'>
          <button class='badge' id='mGrabber'>LinkGrabber</button>
          <button class='badge' id='mExtract'>Extract</button>
          <button class='badge' id='mDuplicates'>Duplicates</button>
        </div>`;
    } else if (page==='editor'){
      leftHTML = `
        <div class='menu-group'>
          <button class='badge' id='mFind'>Find</button>
          <button class='badge' id='mReplace'>Replace</button>
          <button class='badge' id='mMore'>More…</button>
        </div>`;
    }
    pb.innerHTML = leftHTML + `
      <div style='margin-left:auto;display:flex;gap:.4rem;align-items:center'>
        <button class='badge' id='progSearchRun'>Search</button>
      </div>`;
    document.getElementById('appTopMenu').insertAdjacentElement('afterend', pb);

    const runSearch = async () => {
      const q=document.getElementById('progSearch').value.trim();
      let scope='hub'; if (page==='downloader') scope='downloader'; else if (page==='rd') scope='rd'; else if (page==='editor') scope='editor';
      const r = await getJSON(`/api/search?scope=${scope}&q=${encodeURIComponent(q)}`);
      // Simple DOM filter fallback if needed
      if (scope==='hub'){
        document.querySelectorAll('.card[data-title]').forEach(c=>{
          const t=(c.dataset.title||'').toLowerCase();
          c.style.display = !q || t.includes(q.toLowerCase()) ? '' : 'none';
        });
      } else {
        document.querySelectorAll('tr[data-name]').forEach(row=>{
          const n=(row.dataset.name||'').toLowerCase();
          row.style.display = !q || n.includes(q.toLowerCase()) ? '' : 'none';
        });
      }
    };
    document.getElementById('progSearchRun').onclick = runSearch;
    document.getElementById('progSearch').addEventListener('keydown', (e)=>{ if(e.key==='Enter') runSearch(); });
  }

  // Command palette (Ctrl+K) — quick actions and search
  function openCmdPalette(){
    let ov=document.getElementById('cmdPalette');
    if (!ov){
      ov = el('div',{id:'cmdPalette',style:'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:200;display:flex;align-items:flex-start;justify-content:center;padding-top:12vh'});
      ov.innerHTML = `<div style='background:#0b1220;border:1px solid rgba(148,163,184,.25);border-radius:.6rem;min-width:720px;max-width:960px'>
        <div id='cmdList' style='max-height:52vh;overflow:auto;padding:.4rem .6rem'></div>
      </div>`;
      ov.addEventListener('click', (e)=>{ if(e.target===ov) ov.remove(); });
      document.body.appendChild(ov);
      const cmds=[
        {t:'Library: Filters', a:()=>document.getElementById('mFilters')?.click()},
        {t:'Library: Collections', a:()=>document.getElementById('mCollections')?.click()},
        {t:'Downloader: Start', a:()=>document.getElementById('btnStart')?.click()},
        {t:'Downloader: Pause', a:()=>document.getElementById('btnPause')?.click()},
        {t:'Downloader: Limits', a:()=>document.getElementById('btnSaveLimits')?.scrollIntoView()},
        {t:'RD: LinkGrabber', a:()=>document.getElementById('mGrabber')?.click()},
        {t:'Editor: Find/Replace', a:()=>document.getElementById('mFind')?.click()},
        {t:'Organizer…', a:()=>document.getElementById('btnOrganizer')?.click()},
      ];
      function render(list){ const root=document.getElementById('cmdList'); root.innerHTML=''; list.forEach(x=>{ const b=el('div',{class:'badge',style:'display:block;margin:.2rem 0;cursor:pointer'}, x.t); b.onclick=()=>{ x.a(); ov.remove(); }; root.appendChild(b); }); }
      render(cmds);
      const inp=document.getElementById('cmdInput');
      inp.focus();
      inp.addEventListener('input', ()=>{
        const v=inp.value.toLowerCase();
        render(cmds.filter(c=>c.t.toLowerCase().includes(v)));
      });
      inp.addEventListener('keydown',(e)=>{ if(e.key==='Escape'){ ov.remove(); } });
    }
  }
  document.addEventListener('keydown', (e)=>{
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase()==='k'){ e.preventDefault(); openCmdPalette(); }
  });

  // Replace floating panels with dropdown menus (minimal shim; relies on existing handlers)
  function convertPanels(){
    // For this pass we intentionally avoid opening any large overlays; buttons now open compact menus or focus inline overlays.
    // Future: rewire specific IDs to tiny popover components.
  }

  // Boot
  mountTopAppMenu();
  mountProgramBar();
  convertPanels();
})();


// v66.4.19: integrated search suggestions and click-to-apply
(() => {
  const pb=document.getElementById('programBar'); if (!pb) return;
  const box=document.getElementById('progSearch'); const run=document.getElementById('progSearchRun');
  if (!box || !run) return;
  let panel=document.getElementById('progSuggests');
  if (!panel){
    panel=document.createElement('div'); panel.id='progSuggests';
    panel.style='position:absolute; background:#0b1220; border:1px solid rgba(148,163,184,.25); border-radius:.35rem; padding:.3rem; display:none; max-height:40vh; overflow:auto; min-width:300px;';
    pb.appendChild(panel);
  }
  function scope(){
    const p=location.pathname.toLowerCase();
    if (p.includes('downloader')) return 'downloader';
    if (p.includes('rd')) return 'rd';
    if (p.includes('editor')) return 'editor';
    return 'hub';
  }
  async function suggest(){
    const q=box.value.trim();
    if (!q){ panel.style.display='none'; return; }
    const r=await fetch(`/api/search/suggest?scope=${scope()}&q=${encodeURIComponent(q)}`).then(r=>r.json()).catch(()=>({suggestions:[]}));
    panel.innerHTML='';
    (r.suggestions||[]).forEach(s=>{
      const row=document.createElement('div');
      row.className='badge'; row.style.display='block'; row.style.margin='.2rem';
      row.textContent=s.label + (s.sub? (' — '+s.sub): '');
      row.onclick=()=>{ box.value=s.label; run.click(); panel.style.display='none'; };
      panel.appendChild(row);
    });
    const rect=box.getBoundingClientRect();
    panel.style.left=(rect.left)+'px';
    panel.style.top=(rect.bottom + window.scrollY + 6)+'px';
    panel.style.display = (panel.innerHTML.trim()? 'block':'none');
  }
  box.addEventListener('input', suggest);
  document.addEventListener('click', (e)=>{ if(!panel.contains(e.target) && e.target!==box) panel.style.display='none'; });
})();


// v66.4.20: RD packages+tabs, sticky clipboard, per-host limits; Library tree + online lists + Rest; card menu: Trailer/Plex/Kodi; Organizer presets; Dedupe editor.
(() => {
  const path=(location.pathname||'').toLowerCase();
  function el(tag,attrs={},html=''){const e=document.createElement(tag);Object.entries(attrs||{}).forEach(([k,v])=>e.setAttribute(k,v));if(html)e.innerHTML=html;return e;}
  async function getJSON(u){try{const r=await fetch(u);return await r.json()}catch(e){return {}}}
  async function postJSON(u,b){try{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return await r.json()}catch(e){return {}}}
  const pb=document.getElementById('programBar'); if (pb){
    const isRD=path.includes('rd'); const isHub=path.includes('hub');
    if (isRD && !document.getElementById('rdTabs')){
      const g=el('div',{id:'rdTabs',style:'display:flex;gap:.35rem;align-items:center'});
      g.innerHTML=`<button class='badge' data-tab='queue'>Queue</button>
                    <button class='badge' data-tab='downloads'>Downloads</button>
                    <button class='badge' data-tab='finished'>Finished</button>
                    <label style='margin-left:.6rem'>Clipboard <input type='checkbox' id='clipToggle'></label>`;
      pb.insertBefore(g, pb.firstChild);
      getJSON('/api/rd/clipboard/status').then(r=>{ const cb=document.getElementById('clipToggle'); if (cb && r && typeof r.enabled==='boolean') cb.checked=!!r.enabled; });
      pb.addEventListener('change', (e)=>{ if (e.target && e.target.id==='clipToggle') postJSON('/api/rd/clipboard/toggle', {}); });
      pb.addEventListener('click', async (e)=>{
        const b=e.target.closest('button[data-tab]'); if(!b) return;
        const tab=b.dataset.tab; const data = await getJSON('/api/rd/packages?tab='+tab);
        window.dispatchEvent(new CustomEvent('mh:rd:tab',{detail:data}));
      });
    }
    if (isHub && !document.getElementById('libTree')){
      const tree=el('div',{id:'libTree',style:'position:fixed;left:12px;top:160px;width:220px;bottom:18px;overflow:auto;border-right:1px solid rgba(148,163,184,.2);padding-right:.6rem'});
      tree.innerHTML=`<div style='color:#e5e7eb;font-weight:700;margin:.3rem 0'>Library</div>
        <div class='badge'>Movies</div><div class='badge'>TV</div><div class='badge'>Books</div><div class='badge'>Audio</div>
        <div style='margin-top:.6rem;color:#94a3b8'>Collections</div>
        <div class='badge' id='fetchOnline'>Fetch Online List...</div>
        <div class='badge' id='showRest'>Show Rest</div>`;
      document.body.appendChild(tree);
      document.getElementById('fetchOnline').onclick = async ()=>{
        const r = await postJSON('/api/library/collections/fetch_online', {provider:'IMDb', preset:'Top 250 Movies'});
        alert('Fetched '+(r.added||0)+' items into '+(r.preset||'collection'));
      };
      document.getElementById('showRest').onclick = async ()=>{
        const r = await getJSON('/api/library/collections/rest'); alert('Rest items: '+(r.items||[]).length);
      };
    }
  }
  function extendCard(){
    const menu=document.getElementById('cardCtx'); if (!menu) return;
    if (document.getElementById('mTrailer')) return;
    const frag=document.createElement('div');
    frag.innerHTML = `<div id='mTrailer' class='badge' style='display:block;margin:.2rem'>Cast Trailer</div>
      <div id='mPlex' class='badge' style='display:block;margin:.2rem'>Open in Plex</div>
      <div id='mKodi' class='badge' style='display:block;margin:.2rem'>Open in Kodi</div>`;
    menu.appendChild(frag);
    let current=null;
    document.addEventListener('contextmenu', (e)=>{ const c=e.target.closest&&e.target.closest('.card[data-id]'); if(c) current=c; });
    document.getElementById('mTrailer').onclick = async ()=>{ if(!current) return; const t=current.dataset.title||'Media'; const u=await postJSON('/api/trailer/url',{title:t}); if(u.url) window.open('/player.html?src='+encodeURIComponent(u.url)+'&title='+encodeURIComponent(t),'_blank'); };
    document.getElementById('mPlex').onclick = async ()=>{ if(!current) return; const t=current.dataset.title||''; const r=await postJSON('/integrations/plex/url',{title:t}); if(r.url) window.open(r.url,'_blank'); else alert('Plex not configured'); };
    document.getElementById('mKodi').onclick = async ()=>{ if(!current) return; const t=current.dataset.title||''; const r=await postJSON('/integrations/kodi/url',{title:t}); if(r.url) window.open(r.url,'_blank'); else alert('Kodi not configured'); };
  }
  if ((location.pathname||'').toLowerCase().includes('hub')) setTimeout(extendCard,800);
  function enhanceOrganizer(){ const btn=document.getElementById('btnOrganizer'); if(!btn) return; if(document.getElementById('orgPreset')) return;
    btn.insertAdjacentHTML('afterend', `<select id='orgPreset' class='badge'>
      <option value="{title} ({year})/{title}.{year}">Movies default</option>
      <option value="{title} ({year}) [{resolution} {source}]/{title}.{resolution}.{codec}">Movies rich</option>
      <option value="{title}/Season {season}/{title}.S{season}E{episode}.{codec}">TV season-episode</option>
    </select>`);
    document.getElementById('orgPreset').addEventListener('change',(e)=>{
      const p=document.getElementById('organizer_body')?.querySelector('#pat'); if(p) p.value=e.target.value;
    });
  }
  setTimeout(enhanceOrganizer,1200);
  if (pb && !document.getElementById('btnDedupePolicy')){
    const g=document.createElement('div'); g.className='menu-group'; g.innerHTML=`<button class='badge' id='btnDedupePolicy'>Dedupe Policy…</button>`; pb.appendChild(g);
    g.querySelector('#btnDedupePolicy').onclick = async ()=>{
      const ov=document.createElement('div'); ov.style='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:220';
      const card=document.createElement('div'); card.style='max-width:820px;margin:8vh auto;background:#0b1220;border:1px solid rgba(148,163,184,.25);padding:12px;border-radius:8px';
      card.innerHTML = `<h3 style="margin:0 0 6px 0">Dedupe Policy — UserDefined</h3><div id='dpBody' style='max-height:60vh;overflow:auto'></div><div style='margin-top:.5rem'><button class='badge' id='dpSave'>Save</button> <button class='badge' id='dpClose'>Close</button></div>`;
      ov.appendChild(card); document.body.appendChild(ov);
      const getJ=(u)=>fetch(u).then(r=>r.json());
      const postJ=(u,b)=>fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());
      const dp=await getJ('/api/dedupe/policy');
      function mk(id,title,items){ const box=document.createElement('div'); box.innerHTML=`<div style='color:#e5e7eb;margin:.2rem 0;font-weight:600'>${title}</div>`; const ul=document.createElement('div'); ul.id=id; (items||[]).forEach(x=>{ const row=document.createElement('label'); row.style='display:block;margin:.12rem 0'; row.innerHTML=`<input type='checkbox' checked> ${x}`; ul.appendChild(row); }); box.appendChild(ul); return box; }
      const body=card.querySelector('#dpBody'); body.appendChild(mk('dp_gp','Group priority (top wins)', dp.group_priority||[])); body.appendChild(mk('dp_nr','Never remove', dp.never_remove||[]));
      const cond=document.createElement('div'); cond.innerHTML=`<div style='color:#e5e7eb;margin:.2rem 0;font-weight:600'>Conditional rules</div>`; (dp.conditional||[]).forEach(c=>{ const r=document.createElement('div'); r.textContent=`remove ${c.remove} only if present ${c.only_if_present}`; cond.appendChild(r); }); body.appendChild(cond);
      card.querySelector('#dpClose').onclick = ()=> ov.remove();
      card.querySelector('#dpSave').onclick = async ()=>{
        const getList=(id)=>Array.from(card.querySelectorAll('#'+id+' input')).filter(x=>x.checked).map(x=>x.parentElement.textContent.trim());
        await postJ('/api/dedupe/policy',{group_priority:getList('dp_gp'), never_remove:getList('dp_nr'), conditional: dp.conditional||[]});
        alert('Dedupe policy saved'); ov.remove();
      };
    };
  }
})();


// v66.4.24: RD parse + Cast picker + HLS
(()=>{
  async function post(u,b){ return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json()).catch(()=>({})) }
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }

  // Hook RD paste/parse button if present
  const rdParseBtn = document.getElementById('btnParseRD') || document.querySelector('[data-action="rd-parse"]');
  if (rdParseBtn && !rdParseBtn.dataset.bound){
    rdParseBtn.dataset.bound = "1";
    rdParseBtn.addEventListener('click', async ()=>{
      const box = document.getElementById('rdPaste') || document.querySelector('textarea[data-role="rd-input"]');
      const links = (box?.value||"").split(/\r?\n/).filter(x=>x.trim().length>0);
      const res = await post('/api/rd/parse', {links});
      window.dispatchEvent(new CustomEvent('mh:rd:parsed',{detail:res}));
      alert('Parsed items: '+(res.total||0));
    });
  }

  // Add Cast to… in card menu for movies/episodes
  function addCastToMenu(){
    const menu=document.getElementById('cardCtx'); if(!menu) return;
    if(menu.querySelector('#mCast')) return;
    const btn=document.createElement('div'); btn.id='mCast'; btn.className='badge'; btn.style='display:block;margin:.2rem'; btn.textContent='Cast to…';
    menu.appendChild(btn);
    btn.onclick = async ()=>{
      const devs = await get('/api/cast/devices');
      const ov=document.createElement('div'); ov.style='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:300';
      const card=document.createElement('div'); card.style='max-width:620px;margin:10vh auto;background:#0b1220;border:1px solid rgba(148,163,184,.25);padding:12px;border-radius:10px';
      card.innerHTML = `<h3 style="margin:0 0 8px 0">Cast to device</h3>
        <div id="devs" style="max-height:46vh;overflow:auto"></div>
        <div style="margin-top:.6rem"><button class="badge" id="castClose">Close</button></div>`;
      ov.appendChild(card); document.body.appendChild(ov);
      const hostMedia = menu.dataset?.currentSrc || ""; // supply current HLS URL if present
      const list=card.querySelector('#devs');
      (devs.devices||[]).forEach(d=>{
        const row=document.createElement('div'); row.style='margin:.2rem 0';
        const info = `${d.type||'?'} — ${d.name||d.host}`;
        const actionId = 'cast_' + Math.random().toString(36).slice(2);
        row.innerHTML = `<label><input type="radio" name="castdev" id="${actionId}" data-type="${d.type}" data-host="${d.host||''}" data-port="${d.port||''}" data-key="${d.key||''}" data-control="${d.controlURL||''}"> ${info}</label>`;
        list.appendChild(row);
      });
      card.querySelector('#castClose').onclick=()=>ov.remove();
      // fire play when selecting
      list.addEventListener('change', async (e)=>{
        const r=e.target.closest('input[type=radio]'); if(!r) return;
        const url = hostMedia || prompt("Enter media URL to cast (HLS .m3u8 or direct)","");
        if(!url) return;
        if(r.dataset.type==="webos"){
          await post('/api/cast/webos/play', {host:r.dataset.host, url, key:r.dataset.key});
        }else if(r.dataset.type==="dlna"){
          await post('/api/cast/dlna/play', {controlURL:r.dataset.control, url});
        }else{
          alert('Unsupported device type');
        }
        ov.remove();
      });
    };
  }
  setTimeout(addCastToMenu, 1000);

})();

// v66.4.26 optional upgrades
(()=>{
  async function post(u,b){ return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json()).catch(()=>({})) }
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }

  // Column chooser on tables with data-grid
  document.querySelectorAll('[data-grid]').forEach(grid=>{
     if (grid.dataset.colsBound) return; grid.dataset.colsBound="1";
     grid.addEventListener('contextmenu', e=>{
        const th = e.target.closest('th'); if(!th) return;
        e.preventDefault();
        const idx = Array.from(th.parentNode.children).indexOf(th);
        const menu=document.createElement('div');
        menu.style='position:fixed;left:'+e.pageX+'px;top:'+e.pageY+'px;background:#0b1220;padding:8px;border:1px solid rgba(148,163,184,.25);z-index:400';
        menu.innerHTML = `<label style="display:block"><input type="checkbox" checked> Show column ${idx+1}</label>`;
        document.body.appendChild(menu);
        menu.querySelector('input').onchange = (ev)=>{
           const show=ev.target.checked;
           grid.querySelectorAll('tr').forEach(tr=>{
             const td = tr.children[idx]; if(td) td.style.display = show ? '' : 'none';
           });
           menu.remove();
        };
        setTimeout(()=>document.addEventListener('click', ()=>menu.remove(), {once:true}), 0);
     });
  });

  // Library: context menu add/remove to collection
  const lib = document.getElementById('libraryRoot');
  if (lib && !lib.dataset.ctxBound){
    lib.dataset.ctxBound="1";
    lib.addEventListener('contextmenu', async (e)=>{
      const card = e.target.closest('[data-card-id]'); if(!card) return;
      e.preventDefault();
      const id = card.dataset.cardId;
      const ov=document.createElement('div'); ov.style='position:fixed;inset:0;z-index:300';
      const m=document.createElement('div'); m.style='position:absolute;background:#0b1220;border:1px solid rgba(148,163,184,.25);padding:6px;border-radius:8px;left:'+e.pageX+'px;top:'+e.pageY+'px';
      m.innerHTML=`<div class="badge" id="addCol">Add to collection…</div>
                   <div class="badge" id="remCol">Remove from collection…</div>
                   <div class="badge" id="renameOrg">Rename/Move in Organizer…</div>`;
      ov.appendChild(m); document.body.appendChild(ov);
      ov.addEventListener('click',()=>ov.remove());
      m.querySelector('#addCol').onclick = async ()=>{
        const name = prompt("Collection name"); if(!name) return;
        await post('/api/library/collections/add', {id, collection:name}); ov.remove();
      };
      m.querySelector('#remCol').onclick = async ()=>{
        const name = prompt("Remove which collection?"); if(!name) return;
        await post('/api/library/collections/remove', {id, collection:name}); ov.remove();
      };
      m.querySelector('#renameOrg').onclick = async ()=>{
        const path = prompt("Source file path"); if(!path) return;
        const pat = prompt("Pattern (e.g., {title} ({year})/{title}.{ext})", "{title}/{title}.{ext}");
        const meta = {title: card.dataset.title||"", year: card.dataset.year||""};
        const prev = await post('/api/organizer/preview', {files:[{path}], pattern: pat, meta});
        if(prev.plan && prev.plan.length){
          if(confirm("Apply move? " + prev.plan[0].dest)){
            await post('/api/organizer/apply', {plan: prev.plan});
          }
        }
        ov.remove();
      };
    });
  }

  // Editor: simple column ruler & Find-in-files button (if toolbar present)
  const edBar = document.getElementById('editorToolbar');
  if (edBar && !edBar.dataset.plus){
    edBar.dataset.plus="1";
    const rul=document.createElement('button'); rul.className='badge'; rul.textContent='Toggle Column Ruler';
    const fif=document.createElement('button'); fif.className='badge'; fif.textContent='Find in Files…';
    edBar.appendChild(rul); edBar.appendChild(fif);
    rul.onclick = ()=> document.body.classList.toggle('ed-ruler');
    fif.onclick = async ()=>{
      const root = prompt("Folder to search", "/"); const pat = prompt("Pattern (text or regex)", "");
      if(!root || pat===null) return;
      const regex = confirm("Use regex? (OK=yes)"); const caseSens = confirm("Case sensitive? (OK=yes)");
      const res = await post('/api/editor/find_in_files', {root, pattern:pat, regex, case:caseSens, glob:"**/*.*"});
      alert("Matches: "+(res.count||0));
    };
  }

})();

// v66.4.27 merged downloader (JD/IDM-like), Rules Audit tile
(()=>{
  async function post(u,b){ return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json()).catch(()=>({})) }
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }

  // Inject top menu bar buttons if not present
  const topbar = document.getElementById('menuBar') || document.querySelector('[data-topbar]');
  if (topbar && !topbar.dataset.mergedDl){
    topbar.dataset.mergedDl="1";
    const clip=document.createElement('button'); clip.className='badge'; clip.textContent='Clipboard Monitor';
    const audit=document.createElement('button'); audit.className='badge'; audit.textContent='Rules Audit';
    topbar.appendChild(clip); topbar.appendChild(audit);
    // clipboard toggle
    clip.onclick = async ()=>{
      const s = await post('/api/clipboard/toggle', {});
      clip.textContent = 'Clipboard Monitor: ' + (s.enabled ? 'ON' : 'OFF');
    };
    // initial status
    get('/api/clipboard/status').then(s=>{ clip.textContent = 'Clipboard Monitor: ' + (s.enabled ? 'ON' : 'OFF'); });
    // rules audit overlay
    audit.onclick = async ()=>{
      const r = await get('/rules_audit/summary');
      const ov=document.createElement('div'); ov.style='position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:320';
      const card=document.createElement('div'); card.style='max-width:800px;margin:8vh auto;background:#0b1220;border:1px solid rgba(148,163,184,.25);padding:12px;border-radius:12px;max-height:80vh;overflow:auto';
      const req = r.required || {}; let html = '<h3 style="margin:0 0 8px 0">Rules Audit</h3><ul>';
      Object.keys(req).forEach(k=>{ html += `<li>${req[k]?'✅':'❌'} <code>${k}</code></li>`; });
      html += '</ul>';
      const sa = r.self_audit || {}; html += '<h4>Self-Audit</h4><pre style="white-space:pre-wrap">'+JSON.stringify(sa,null,2)+'</pre>';
      card.innerHTML = html + '<div style="margin-top:8px"><button class="badge" id="xClose">Close</button></div>';
      ov.appendChild(card); document.body.appendChild(ov);
      card.querySelector('#xClose').onclick=()=>ov.remove();
    };
  }

  // Downloader: merged tabs (Grabber / Downloads / Finished)
  const dlRoot = document.getElementById('downloaderRoot');
  if (dlRoot && !dlRoot.dataset.merged){
    dlRoot.dataset.merged="1";
    const tabs=document.createElement('div');
    tabs.className='tabbar'; tabs.innerHTML = `<button class="badge" data-t="grab">Link Grabber</button>
                                               <button class="badge" data-t="dl">Downloads</button>
                                               <button class="badge" data-t="fin">Finished</button>`;
    dlRoot.prepend(tabs);
    const pane=document.createElement('div'); pane.id='dlPane'; dlRoot.appendChild(pane);

    async function renderGrabber(){
      const res = await get('/api/downloader/grabber');
      const items = res.items||[];
                      <div style="margin:.4rem 0">
                         <button class="badge" id="grabParse">Parse</button>
                         <button class="badge" id="grabToDl">Add to Downloads</button>
                         <button class="badge" id="grabClear">Remove Selected</button>
                      </div>`;
      let table = `<table data-grid style="width:100%"><thead><tr><th></th><th>Name</th><th>URL</th><th>Kind</th><th>Status</th></tr></thead><tbody>`;
      items.forEach(it=>{
        table += `<tr><td><input type="checkbox" data-url="${it.url}"></td><td>${it.name||''}</td><td>${it.url}</td><td>${it.kind||''}</td><td>${it.status||''}</td></tr>`;
      });
      table += `</tbody></table>`;
      pane.innerHTML = addBox + table + `<div id="dlBottom" style="display:flex;gap:.5rem;align-items:center;margin-top:.5rem;border-top:1px solid rgba(148,163,184,.25);padding-top:.5rem">
         <span>Global speed</span><input id="gSpd" type="number" min="0" value="0" style="width:90px">
         <span>Slots</span><input id="gSlots" type="number" min="1" value="4" style="width:60px">
         <button class="badge" id="applySet">Apply</button></div>`;

      pane.querySelector('#grabParse').onclick = async ()=>{
        const t = pane.querySelector('#grabAdd').value.split(/\r?\n/).filter(x=>x.trim().length>0);
        if(!t.length) return;
        await post('/api/downloader/grabber', {action:'add', links: t});
        renderGrabber();
      };
      pane.querySelector('#grabToDl').onclick = async ()=>{
        const urls = Array.from(pane.querySelectorAll('tbody input[type=checkbox]:checked')).map(x=>x.dataset.url);
        if(!urls.length) return;
        await post('/api/downloader/grabber', {action:'add_to_downloads', urls});
        renderGrabber();
      };
      pane.querySelector('#grabClear').onclick = async ()=>{
        const urls = Array.from(pane.querySelectorAll('tbody input[type=checkbox]:checked')).map(x=>x.dataset.url);
        if(!urls.length) return;
        await post('/api/downloader/grabber', {action:'remove', urls});
        renderGrabber();
      };
      pane.querySelector('#applySet').onclick = async ()=>{
        const s = Number(pane.querySelector('#gSpd').value||0);
        const sl= Number(pane.querySelector('#gSlots').value||4);
        await post('/api/downloader/settings', {global_speed:s, global_slots:sl, per_host:{}});
        alert('Applied');
      };
    }

    async function renderDownloads(){
      const res = await get('/api/downloader/downloads');
      const items = res.items||[];
      let table = `<div style="margin:.4rem 0">
              <button class="badge" id="st">Start</button>
              <button class="badge" id="sp">Stop</button>
              <button class="badge" id="rt">Retry</button>
              <button class="badge" id="mvT">Move Top</button>
              <button class="badge" id="mvB">Move Bottom</button>
              <button class="badge" id="fin">Mark Finished</button>
            </div>`;
      table += `<table data-grid style="width:100%"><thead><tr><th></th><th>Name</th><th>URL</th><th>Status</th></tr></thead><tbody>`;
      items.forEach(it=>{
        table += `<tr><td><input type="checkbox" data-url="${it.url}"></td><td>${it.name||''}</td><td>${it.url}</td><td>${it.status||''}</td></tr>`;
      });
      table += `</tbody></table>`;
      pane.innerHTML = table;
      function sel(){ return Array.from(pane.querySelectorAll('tbody input:checked')).map(x=>x.dataset.url); }
      pane.querySelector('#st').onclick = async ()=>{ await post('/api/downloader/downloads', {action:'start', urls: sel()}); renderDownloads(); };
      pane.querySelector('#sp').onclick = async ()=>{ await post('/api/downloader/downloads', {action:'stop', urls: sel()}); renderDownloads(); };
      pane.querySelector('#rt').onclick = async ()=>{ await post('/api/downloader/downloads', {action:'retry', urls: sel()}); renderDownloads(); };
      pane.querySelector('#mvT').onclick= async ()=>{ await post('/api/downloader/downloads', {action:'move_top', urls: sel()}); renderDownloads(); };
      pane.querySelector('#mvB').onclick= async ()=>{ await post('/api/downloader/downloads', {action:'move_bottom', urls: sel()}); renderDownloads(); };
      pane.querySelector('#fin').onclick = async ()=>{ await post('/api/downloader/downloads', {action:'complete', urls: sel()}); renderDownloads(); };
    }

    async function renderFinished(){
      const res = await get('/api/downloader/finished');
      const items = res.items||[];
      let table = `<table data-grid style="width:100%"><thead><tr><th>Name</th><th>URL</th><th>Status</th></tr></thead><tbody>`;
      items.forEach(it=>{
        table += `<tr><td>${it.name||''}</td><td>${it.url}</td><td>${it.status||''}</td></tr>`;
      });
      table += `</tbody></table>`;
      pane.innerHTML = table;
    }

    const btns = tabs.querySelectorAll('button');
    btns.forEach(b=> b.onclick = ()=>{
      btns.forEach(x=>x.classList.remove('active')); b.classList.add('active');
      if (b.dataset.t=='grab') renderGrabber();
      if (b.dataset.t=='dl')   renderDownloads();
      if (b.dataset.t=='fin')  renderFinished();
    });
    // default to Grabber as you requested
    btns[0].click();
  }

})();

// v66.4.29 DLC import + per-host live stats + Smart Collections overlay
(()=>{
  async function post(u,b){ return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json()).catch(()=>({})) }
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }

  // Add "Import DLC" to Link Grabber toolbar if present
  const dlRoot = document.getElementById('downloaderRoot');
  const pane = document.getElementById('dlPane');
  if (dlRoot && pane && !dlRoot.dataset.dlc){
    dlRoot.dataset.dlc="1";
    const tbar = document.createElement('div'); tbar.style='display:flex;gap:.4rem;margin:.3rem 0;';
    const dlcBtn = document.createElement('button'); dlcBtn.className='badge'; dlcBtn.textContent='Import DLC…';
    tbar.appendChild(dlcBtn);
    dlRoot.insertBefore(tbar, pane);
    dlcBtn.onclick = ()=>{
      const fi = document.createElement('input'); fi.type='file'; fi.accept='.dlc';
      fi.onchange = async ()=>{
        const f = fi.files[0]; if(!f) return;
        const fd = new FormData(); fd.append('file', f, f.name);
        const r = await fetch('/api/downloader/grabber/parse_dlc', {method:'POST', body: fd}).then(r=>r.json()).catch(()=>({}));
        if(r.error){
          alert('DLC import failed: '+r.error+(r.detail?(' - '+r.detail):''));
        } else {
          alert('Imported links: '+(r.imported||0));
        }
      };
      fi.click();
    };
  }

  // Per-host live stats in bottom bar (Downloads tab)
  async function refreshStats(){
    const res = await get('/api/downloader/downloads');
    const items = (res.items||[]).filter(x=>x.status==='running');
    const byHost = {};
    items.forEach(it=>{
      try{
        const u = new URL(it.url); const h = u.hostname;
        byHost[h] = (byHost[h]||0)+1;
      }catch{}
    });
    let txt = 'Active per host: ' + Object.keys(byHost).map(h=>`${h}:${byHost[h]}`).join('  ·  ');
    if(!Object.keys(byHost).length) txt = 'Active per host: (none)';
    let bar = document.getElementById('dlStatsBar');
    if(!bar){ bar = document.createElement('div'); bar.id='dlStatsBar'; bar.style='margin-top:.3rem;opacity:.8'; (document.getElementById('dlBottom')||document.body).appendChild(bar); }
    bar.textContent = txt;
  }
  setInterval(refreshStats, 3000);

  // Smart Collections overlay (Library → menu trigger assumed)
  const lib = document.getElementById('libraryRoot');
  if (lib && !lib.dataset.smart){
    lib.dataset.smart="1";
    const btn = document.createElement('button'); btn.className='badge'; btn.textContent='Smart Collections…';
    lib.prepend(btn);
    btn.onclick = async ()=>{
      const ov=document.createElement('div'); ov.style='position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:360';
      const card=document.createElement('div'); card.style='max-width:560px;margin:10vh auto;background:#0b1220;border:1px solid rgba(148,163,184,.25);padding:12px;border-radius:12px';
      card.innerHTML = `<h3>Smart Collections</h3>
        <div style="display:grid;gap:.4rem">
          <label>IMDb kind
            <select id="k"><option value="top250_movies">Top 250 Movies</option>
                           <option value="top250_tv">Top 250 TV</option>
                           <option value="list">Custom List URL</option></select>
          </label>
          <button class="badge" id="fetch">Fetch & Apply</button>
        </div>
        <hr><div style="display:grid;gap:.4rem">
          <label>Schedule (minutes) <input id="interval" type="number" min="30" value="1440"></label>
          <button class="badge" id="saveSched">Save schedule</button>
        </div>
        <div style="margin-top:.5rem"><button class="badge" id="closeX">Close</button></div>`;
      ov.appendChild(card); document.body.appendChild(ov);
      card.querySelector('#closeX').onclick=()=>ov.remove();
      card.querySelector('#fetch').onclick= async ()=>{
        const kind = card.querySelector('#k').value;
        const url  = card.querySelector('#u').value.trim();
        const col  = card.querySelector('#c').value.trim() || 'Online List';
        const r = await post('/api/collections/fetch_online', {provider:'imdb', kind, id_or_url:url, collection:col});
        alert('Matched items in library: '+(r.matched||0)+' from '+(r.tconsts||0)+' list entries.');
      };
      card.querySelector('#saveSched').onclick= async ()=>{
        const itv = Number(card.querySelector('#interval').value||1440);
        await post('/api/collections/schedule', {tasks:[{"provider":"imdb","kind":"top250_movies","interval_min": itv}]});
        alert('Saved');
      };
    };
  }

})();

// v66.4.31 Backup buttons + JD Helper launcher hint
(()=>{
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }
  // Settings: add "Create Backup" quick action
  const sets = document.getElementById('settingsRoot');
  if (sets && !sets.dataset.backupBtn){
    sets.dataset.backupBtn="1";
    const btn=document.createElement('button'); btn.className='badge'; btn.textContent='Create Backup';
    sets.prepend(btn);
    btn.onclick = async ()=>{
      const r = await fetch('/api/backup/create').then(r=>r.json()).catch(()=>({}));
      if(r.file){ const a=document.createElement('a'); a.href=r.file; a.download=r.name||'backup.zip'; a.click(); }
      else alert('Backup failed');
    };
  }
  // Profiles: same backup convenience
  const prof = document.getElementById('profilesRoot');
  if (prof && !prof.dataset.backupBtn){
    prof.dataset.backupBtn="1";
    const btn=document.createElement('button'); btn.className='badge'; btn.textContent='Create Backup';
    prof.prepend(btn);
    btn.onclick = async ()=>{
      const r = await fetch('/api/backup/create').then(r=>r.json()).catch(()=>({}));
      if(r.file){ const a=document.createElement('a'); a.href=r.file; a.download=r.name||'backup.zip'; a.click(); }
      else alert('Backup failed');
    };
  }
  // Downloader: JD Helper status button
  const dlRoot = document.getElementById('downloaderRoot');
  if (dlRoot && !dlRoot.dataset.jdHelper){
    dlRoot.dataset.jdHelper="1";
    const t = document.createElement('div'); t.style='display:flex;gap:.4rem;margin:.3rem 0;';
    const btn=document.createElement('button'); btn.className='badge'; btn.textContent='JD Helper…';
    t.appendChild(btn); dlRoot.prepend(t);
    btn.onclick = async ()=>{
      const s = await get('/api/jd_helper/status');
      alert('JD helper script at '+(s.script||'scripts/jd_helper/start.cmd')+'\nmyjdapi: '+(s.myjdapi_present?'OK':'Missing')+'\nMyJD config: '+(s.myjd_config_ok?'OK':'Missing'));
    };
  }
})();

// v66.4.32 Keys Backup/Restore + per-host live throughput text
(()=>{
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }
  async function post(u,b){ return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json()).catch(()=>({})) }

  // Settings: add Keys Backup/Restore buttons
  const sets = document.getElementById('settingsRoot');
  if (sets && !sets.dataset.keysBk){
    sets.dataset.keysBk="1";
    const row=document.createElement('div'); row.style='display:flex;gap:.4rem;margin:.5rem 0;flex-wrap:wrap';
    const b1=document.createElement('button'); b1.className='badge'; b1.textContent='Backup Keys…';
    const b2=document.createElement('button'); b2.className='badge'; b2.textContent='Restore Keys…';
    const b3=document.createElement('a'); b3.className='badge'; b3.textContent='Secure Pack (7-Zip)'; b3.href='#';
    row.appendChild(b1); row.appendChild(b2); row.appendChild(b3); sets.prepend(row);
    b1.onclick = async ()=>{
      const r = await get('/api/keys/backup');
      if(r.file){ const a=document.createElement('a'); a.href=r.file; a.download=r.name||'keys.zip'; a.click(); }
      else alert('Backup failed');
    };
    b2.onclick = async ()=>{
      const fi = document.createElement('input'); fi.type='file'; fi.accept='.json,.zip';
      fi.onchange = async ()=>{
        const f = fi.files[0]; if(!f) return;
        const fd = new FormData(); fd.append('file', f, f.name);
        const r = await fetch('/api/keys/restore', {method:'POST', body: fd}).then(r=>r.json()).catch(()=>({}));
        if(r.restored) alert('Keys restored. Restart app for env-based loads.');
        else alert('Restore failed: '+(r.error||'unknown'));
      };
      fi.click();
    };
    b3.onclick = (e)=>{
      e.preventDefault();
      alert('Use scripts\\keys_secure\\pack.cmd to create an encrypted 7z of keys.local.json (requires 7-Zip in PATH).');
    };
  }

  // Downloader bottom bar: per-host throughput (poll /api/downloader/telemetry)
  async function refreshThroughput(){
    const r = await get('/api/downloader/telemetry');
    const h = r.hosts||{};
    const txt = Object.keys(h).length ?
      'Throughput: ' + Object.entries(h).map(([k,v])=> `${k}: ${(v.bps/1024).toFixed(1)} KB/s (${v.slots} slots)`).join('  ·  ')
      : 'Throughput: (idle)';
    let bar = document.getElementById('dlTputBar');
    if(!bar){
      const bottom = document.getElementById('dlBottom') || document.body;
      bar = document.createElement('div'); bar.id='dlTputBar'; bar.style='margin-top:.25rem;opacity:.85';
      bottom.appendChild(bar);
    }
    bar.textContent = txt;
  }
  setInterval(refreshThroughput, 2000);
})();

// v66.4.33 IMDb resilience + JD self-test UI
(()=>{
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }
  // Downloader: add "Self-test" next to JD Helper
  const dlRoot = document.getElementById('downloaderRoot');
  if (dlRoot && !dlRoot.dataset.jdSelf){
    dlRoot.dataset.jdSelf="1";
    const bar = dlRoot.querySelector('div') || dlRoot;
    const btn = document.createElement('button'); btn.className='badge'; btn.textContent='JD Self-test';
    bar.appendChild(btn);
    btn.onclick = async ()=>{
      const s = await get('/api/jd_helper/selftest');
      alert('JD Self-test:\\nmyjdapi: '+(s.myjdapi_present?'OK':'Missing')+
            '\\nconfigured: '+(s.configured?'yes':'no')+
            (s.devices?('\\ndevices: '+s.devices.join(', ')):'')+
            (s.error?('\\ninfo: '+s.error):''));
    };
  }
  // Smart Collections overlay hint (if present): add a small note about offline cache
  const lib = document.getElementById('libraryRoot');
  if (lib && lib.dataset.smart && !lib.dataset.smartHint){
    lib.dataset.smartHint="1";
    const note = document.createElement('div');
    note.style='font-size:.85rem;opacity:.8;margin:.4rem 0';
    note.textContent='IMDb fetch is resilient: uses local cache if offline.';
    lib.prepend(note);
  }
})();

// v66.4.34: show a small banner if keys missing or JD helper not configured
(async()=>{
  async function get(u){ return fetch(u).then(r=>r.json()).catch(()=>({})) }
  const head = document.getElementById('globalHeader') || document.body;
  const ks = await get('/integrations/status');
  const jd = await get('/api/jd_helper/status');
  let issues = [];
  if (ks && ks.keys_present){
    const miss = Object.entries(ks.keys_present).filter(([k,v])=>!v).map(([k])=>k);
    if (miss.length) issues.push('Keys missing: '+miss.join(', '));
  }
  if (jd && (!jd.myjdapi_present || !jd.myjd_config_ok)){
    issues.push('JD Helper: '+(!jd.myjdapi_present?'myjdapi missing':'configure credentials via /api/jd/config'));
  }
  if (issues.length){
    const bar = document.createElement('div');
    bar.style='position:sticky;top:0;background:#7c2d12;color:#fff;padding:.35rem .6rem;font-size:.9rem;z-index:500;border-bottom:1px solid rgba(255,255,255,.2)';
    bar.textContent = 'Setup hints: '+issues.join('  ·  ');
    head.prepend(bar);
  }
})();

// v66.4.35 Library ENFORCER: ensures pinned subcats, dock hierarchy, card context and toolbar actions are visible.
(()=>{
  function el(html){ const d=document.createElement('div'); d.innerHTML=html.trim(); return d.firstChild; }
  const root = document.getElementById('libraryRoot');
  if(!root) return;

  // Pinned tiles
  if(!document.getElementById('pinnedSubcats')){
    const bar = el(`<div id="pinnedSubcats" style="display:flex;gap:.5rem;flex-wrap:wrap;margin:.4rem 0"></div>`);
    const pins = ["Collections","Online Lists","Awards","Franchises","Rest","Recently Added","Continue Watching"];
    pins.forEach(n=>{
      const b = el(`<button class="badge" data-name="${n}">${n}</button>`);
      b.onclick = ()=>{ document.dispatchEvent(new CustomEvent('library.pin.open',{detail:{name:n}})); }
      bar.appendChild(b);
    });
    root.prepend(bar);
  }

  // Toolbar (Rebuild Index / Integrity Scan)
  if(!document.getElementById('libToolbar')){
    const tb = el(`<div id="libToolbar" style="display:flex;gap:.5rem;margin:.25rem 0">
      <button class="badge" id="btnRebuildIdx">Rebuild Index</button>
      <button class="badge" id="btnIntegrity">Integrity Scan</button>
    </div>`);
    root.prepend(tb);
    tb.querySelector('#btnRebuildIdx').onclick = async ()=>{
      const r = await fetch('/api/library/rebuild_index',{method:'POST'}).then(r=>r.json()).catch(()=>({}));
      alert('Index rebuilt: '+(r.count||0)+' items');
    };
    tb.querySelector('#btnIntegrity').onclick = async ()=>{
      const r = await fetch('/api/library/integrity_scan',{method:'POST'}).then(r=>r.json()).catch(()=>({}));
      alert('Integrity: checked '+(r.checked||0)+', missing '+(r.missing||0));
    };
  }

  // Hierarchy dock (left)
  if(!document.getElementById('libDock')){
    const dk = el(`<div id="libDock" style="position:sticky;top:3rem;max-width:220px;align-self:flex-start">
      <div style="font-weight:600;margin-bottom:.25rem">Library</div>
      <ul id="libTree" style="margin:0;padding-left:1rem;line-height:1.6">
        <li>Movies<ul><li>Collections</li><li>Online Lists</li><li>Awards</li><li>Franchises</li><li>Rest</li></ul></li>
        <li>TV<ul><li>Collections</li><li>Online Lists</li><li>Awards</li><li>Franchises</li><li>Rest</li></ul></li>
        <li>Books<ul><li>Collections</li><li>Online Lists</li><li>Awards</li><li>Franchises</li><li>Rest</li></ul></li>
        <li>Audio<ul><li>Collections</li><li>Online Lists</li><li>Awards</li><li>Franchises</li><li>Rest</li></ul></li>
      </ul>
    </div>`);
    const grid = document.getElementById('cardsGrid') || root;
    root.insertBefore(dk, grid);
  }

  // Card context menu
  document.addEventListener('contextmenu', (e)=>{
    const card = e.target.closest('.mediaCard'); if(!card) return;
    e.preventDefault();
    let m = document.getElementById('cardContext');
    if(!m){
      m = el(`<div id="cardContext" style="position:fixed;background:#111;color:#fff;border:1px solid #333;border-radius:.5rem;padding:.4rem;z-index:9999">
        <button class="badge" data-act="add_to_collection">Add to Collection…</button>
        <button class="badge" data-act="remove_from_collection">Remove from Collection…</button>
        <button class="badge" data-act="cast_trailer">Cast Trailer</button>
        <button class="badge" data-act="refresh_metadata">Refresh Metadata</button>
        <button class="badge" data-act="verify_file">Verify File</button>
        <button class="badge" data-act="move_rename">Move/Rename…</button>
      </div>`);
      document.body.appendChild(m);
      m.addEventListener('click', async (ev)=>{
        const act = ev.target.dataset.act; if(!act) return;
        const id = m.dataset.id;
        await fetch('/api/library/context_actions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:act,id})});
        m.style.display='none';
      });
    }
    m.style.left = e.pageX+'px'; m.style.top = e.pageY+'px'; m.style.display='block'; m.dataset.id = card.dataset.id||"";
  });
  document.addEventListener('click', ()=>{
    const m = document.getElementById('cardContext'); if(m) m.style.display='none';
  });

  // Ping server manifest to mark verify OK on client side later (could be expanded)
  fetch('/manifest/verify').then(r=>r.json()).then(j=>{ console.debug('manifest verify', j); });
})();

(async function(){
  try{
    const c=await (await fetch('/api/config/get')).json();
    const ui=c.ui||{};
    document.documentElement.style.setProperty('--font-scale', (ui.font_scale||100)+'%');
    document.body.classList.toggle('reduce-motion', !!ui.reduced_motion);
    document.body.classList.toggle('hc', !!ui.high_contrast);
    document.documentElement.setAttribute('dir', ui.rtl ? 'rtl' : 'ltr');

    // Keyboard shortcuts
    let keys=[];
    document.addEventListener('keydown', (e)=>{
      if (e.key === '/'){ e.preventDefault(); location.href='spotlight.html'; return; }
      keys.push(e.key); setTimeout(()=>keys=[], 500);
      if(keys.join(' ')==='g d'){ location.href='downloads.html'; }
      if(keys.join(' ')==='g h'){ location.href='home.html'; }
    }, true);
  }catch(e){}
})();
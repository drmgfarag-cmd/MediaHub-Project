(function(){
  // Adjust hero gradient darkness based on poster brightness (simple canvas sample)
  function avgBrightness(img){
    try{
      const c=document.createElement('canvas'), ctx=c.getContext('2d'); c.width=32; c.height=32;
      ctx.drawImage(img,0,0,32,32);
      const d=ctx.getImageData(0,0,32,32).data;
      let sum=0, n=d.length/4;
      for(let i=0;i<d.length;i+=4){
        // perceptual luma
        sum += 0.2126*d[i] + 0.7152*d[i+1] + 0.0722*d[i+2];
      }
      return sum/n;
    }catch(e){ return 128; }
  }
  function apply(){
    const hero=document.querySelector('.hero, #hero, .hero-backdrop');
    const img=(hero && (hero.querySelector('img')||hero));
    if(!hero || !img) return;
    if(img.complete){
      const b=avgBrightness(img);
      const dark = b>150 ? 0.55 : (b>120 ? 0.65 : 0.75);
      hero.style.setProperty('--hero-darkness', dark);
      hero.classList.add('hero-auto-grad');
    }else{
      img.addEventListener('load', apply, {once:true});
    }
  }
  document.addEventListener('DOMContentLoaded', apply);
})();
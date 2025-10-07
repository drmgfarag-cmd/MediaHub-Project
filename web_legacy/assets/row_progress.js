function renderProgress(el, pct){
  const w=Math.max(0,Math.min(100,Math.round(pct||0)));
  el.innerHTML = `<div style="width:180px;height:8px;border-radius:6px;background:#1f2937;overflow:hidden;display:inline-block;vertical-align:middle;margin-left:6px">
    <div style="width:${w}%;height:100%;background:${w>=100?'#16a34a':'#3b82f6'}"></div></div>`;
}
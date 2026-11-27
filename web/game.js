"use strict";
const canvas = document.getElementById("room");
const ctx = canvas.getContext("2d");
const found = new Map();
const names = ["杯子", "盘子", "叉子", "小碗", "茶匙", "茶壶", "小碟"];
const chips = names.map(name => {
  const el = document.createElement("li");
  el.textContent = name;
  document.querySelector("#items").append(el);
  return el;
});
const art = new Image(), mask = new Image();
let px, w, h, cw = 1, ch = 1, dpi = 1, scale = 1, tx = 0, ty = 0, panX = 0, panY = 0, ready = false, drag;
const box = () => {
  scale = Math.max(cw / w, ch / h) * 1.15;
  const ex = (w * scale - cw) / 2, ey = (h * scale - ch) / 2;
  panX = Math.max(-ex, Math.min(ex, panX));
  panY = Math.max(-ey, Math.min(ey, panY));
  tx = -ex + panX; ty = -ey + panY;
};
function paint() {
  if (!ready) return;
  box();
  ctx.setTransform(dpi, 0, 0, dpi, 0, 0);
  ctx.clearRect(0, 0, cw, ch);
  ctx.drawImage(art, tx, ty, w * scale, h * scale);
  for (const [x,y] of found.values()) {
    const X = tx + x * scale, Y = ty + y * scale;
    ctx.beginPath(); ctx.arc(X, Y, 9, 0, Math.PI * 2); ctx.fillStyle = "#61846a"; ctx.fill();
    ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.beginPath();ctx.moveTo(X-4,Y);ctx.lineTo(X-1,Y+3);ctx.lineTo(X+4,Y-4);ctx.stroke();
  }
}
new ResizeObserver(() => {
  const bounds = canvas.getBoundingClientRect();
  cw = bounds.width; ch = bounds.height; dpi = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(cw * dpi); canvas.height = Math.round(ch * dpi);
  paint();
}).observe(canvas);
function sync() {
  chips.forEach((chip,i) => chip.classList.toggle("found", found.has(i + 1)));
  document.querySelector("#count").innerHTML = found.size + " <small>/ 7</small>";
  document.querySelector("#victory").hidden = found.size !== names.length;
  paint();
}
function pos(e) {
  const r = canvas.getBoundingClientRect();
  return [e.clientX - r.left, e.clientY - r.top];
}
function move(e) {
  if (drag?.id !== e.pointerId) return;
  const [x,y] = pos(e), dx = x - drag.x, dy = y - drag.y;
  if (Math.hypot(dx,dy) >= 7) drag.moved = true;
  if (drag.moved) { panX = drag.panX + dx; panY = drag.panY + dy; paint(); }
}
canvas.addEventListener("pointerdown", e => {
  if (!ready || drag || e.button !== 0) return;
  const [x,y] = pos(e);
  drag = {id:e.pointerId,x,y,panX,panY,moved:false};
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", move);
canvas.addEventListener("pointerup", e => {
  if (drag?.id !== e.pointerId) return;
  move(e);
  if (!drag.moved) {
    const [p,q] = pos(e), x = Math.floor((p-tx)/scale), y = Math.floor((q-ty)/scale), j = 4*(y*w+x);
    if (x>=0 && x<w && y>=0 && y<h) {
      const r=px[j], id=Math.round(r/32);
      if(id>=1 && id<=7 && Math.abs(r-id*32)<=2 && px[j+1]<4 && px[j+2]<4 && !found.has(id)) {found.set(id,[x,y]);sync();}
    }
  }
  drag=undefined;
});
for (const type of ["pointercancel","lostpointercapture"]) canvas.addEventListener(type,e=>{ if(drag?.id===e.pointerId) drag=undefined; });
document.getElementById("again").addEventListener("click", () => {found.clear();panX=panY=0;sync();});
Promise.all([new Promise((y,n)=>{art.onload=y;art.onerror=n;art.src="./assets/room.webp";}),new Promise((y,n)=>{mask.onload=y;mask.onerror=n;mask.src="./assets/pick.png";})]).then(()=>{
  w=art.naturalWidth;h=art.naturalHeight;
  if(w!==mask.naturalWidth||h!==mask.naturalHeight) throw Error("Misaligned pick map");
  const c=document.createElement("canvas");c.width=w;c.height=h;const d=c.getContext("2d",{willReadFrequently:true});d.drawImage(mask,0,0);px=d.getImageData(0,0,w,h).data;
  ready=true;document.getElementById("loading").hidden=true;paint();
}).catch(()=>{document.getElementById("loading").textContent="场景没有加载，请刷新重试。";});

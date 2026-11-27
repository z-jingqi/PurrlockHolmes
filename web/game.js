"use strict";
const canvas = document.getElementById("room");
const ctx = canvas.getContext("2d");
const found = new Map(), taken = new Set(), flying = new Map();
const layer = document.getElementById("flight-layer"), liftCtx = layer.getContext("2d");
const boxImg = document.getElementById("box");
const atlas = new Image();
let props, raf = 0, bump = -Infinity;
const LIFT = 140, DURATION = 580;
const ease = t => t*t*(3-2*t);
const mix = (a,b,t) => a+(b-a)*t;
const lerp2 = (a,b,t) => [mix(a[0],b[0],t),mix(a[1],b[1],t)];
const curve = (a,b,c,d,t) => lerp2(lerp2(lerp2(a,b,t),lerp2(b,c,t),t),lerp2(lerp2(b,c,t),lerp2(c,d,t),t),t);
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
  for (const id of taken) {
    const {patch:[x,y,pw,ph],origin:[ox,oy]} = props[id];
    ctx.drawImage(atlas,x,y,pw,ph,tx+ox*scale,ty+oy*scale,pw*scale,ph*scale);
  }
}
new ResizeObserver(() => {
  const bounds = canvas.getBoundingClientRect();
  cw = bounds.width; ch = bounds.height; dpi = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(cw * dpi); canvas.height = Math.round(ch * dpi);
  const q=layer.getBoundingClientRect(); layer.width=Math.round(q.width*dpi); layer.height=Math.round(q.height*dpi);
  paint();
}).observe(document.querySelector(".case"));
function sync() {
  chips.forEach((chip,i) => chip.classList.toggle("found", found.has(i + 1)));
  document.querySelector("#count").innerHTML = found.size + " <small>/ 7</small>";
  document.querySelector("#victory").hidden = found.size !== names.length;
  paint();
}
function frame(now) {
  raf = 0;
  liftCtx.setTransform(dpi,0,0,dpi,0,0);
  liftCtx.clearRect(0,0,layer.width/dpi,layer.height/dpi);
  const a=canvas.getBoundingClientRect(), b=layer.getBoundingClientRect();
  const k=boxImg.parentElement.getBoundingClientRect();
  const end=[k.left-b.left+k.width/2,k.top-b.top+k.height*.34];
  for (const [id,{at,x,y,f}] of flying) {
    const age=now-at;
    if (age>=DURATION) {
      flying.delete(id); found.set(id,true); bump=now; sync(); continue;
    }
    const p=[a.left-b.left+x,a.top-b.top+y], up=[p[0],p[1]-26];
    const [sx,sy,sw,sh]=props[id].sprite;
    let c,z,t;
    if (age<LIFT) {
      t=Math.max(0,age/LIFT); c=lerp2(p,up,1-(1-t)**3); z=mix(1,1.12,t); liftCtx.globalAlpha=1;
    } else {
      t=(age-LIFT)/(DURATION-LIFT);
      const dx=end[0]-up[0];
      c=curve(up,[up[0]+dx*.26,up[1]-40],[end[0]-dx*.26,end[1]-73],end,ease(t));
      z=mix(1.12,.17,t*t); liftCtx.globalAlpha=1-ease(Math.max(0,(t-.80)/.20));
    }
    const w=sw*f*z,h=sh*f*z;
    liftCtx.drawImage(atlas,sx,sy,sw,sh,c[0]-w/2,c[1]-h/2,w,h);
  }
  liftCtx.globalAlpha=1;
  const pulse=Math.max(0,1-(now-bump)/180);
  boxImg.style.transform=pulse>0?`scale(${1+Math.sin(pulse*Math.PI)*.09})`:"";
  if(flying.size||pulse>0) raf=requestAnimationFrame(frame);
}
function take(id) {
  if(taken.has(id))return;
  const [x,y]=props[id].center;
  taken.add(id);
  flying.set(id,{at:performance.now(),x:tx+x*scale,y:ty+y*scale,f:scale});
  if(!raf)raf=requestAnimationFrame(frame);
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
      if(id>=1 && id<=7 && Math.abs(r-id*32)<=2 && px[j+1]<4 && px[j+2]<4 ) take(id);
    }
  }
  drag=undefined;
});
for (const type of ["pointercancel","lostpointercapture"]) canvas.addEventListener(type,e=>{ if(drag?.id===e.pointerId) drag=undefined; });
document.getElementById("again").addEventListener("click", () => {found.clear();taken.clear();flying.clear();panX=panY=0;bump=-Infinity;
  if(raf){cancelAnimationFrame(raf);raf=0;}
  frame(performance.now());sync();});
const load=(img,path)=>new Promise((yes,no)=>{img.onload=yes;img.onerror=no;img.src=path;});
Promise.all([load(art,"./assets/room.webp"),load(mask,"./assets/pick.png"),load(atlas,"./assets/pickups.webp"),
  fetch("./assets/pickups.json").then(r=>{if(!r.ok)throw Error("Missing pickup data");return r.json();})
]).then(([, , , data])=>{
  props=data;
  w=art.naturalWidth;h=art.naturalHeight;
  if(w!==mask.naturalWidth||h!==mask.naturalHeight) throw Error("Misaligned pick map");
  const c=document.createElement("canvas");c.width=w;c.height=h;const d=c.getContext("2d",{willReadFrequently:true});d.drawImage(mask,0,0);px=d.getImageData(0,0,w,h).data;
  ready=true;document.getElementById("loading").hidden=true;paint();
}).catch(()=>{document.getElementById("loading").textContent="场景没有加载，请刷新重试。";});

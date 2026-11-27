"use strict";
const canvas = document.getElementById("room");
const ctx = canvas.getContext("2d");
const found = new Map(), taken = new Set(), flying = new Map();
const layer = document.getElementById("flight-layer"), liftCtx = layer.getContext("2d");
const boxImg = document.getElementById("box");
const atlas = new Image(), wrongArt = new Image(), wrongImage = new Image();
const hintButton = document.getElementById("hint");
const wrongMoves = new Map();
const TOTAL=7, HINT_TIME=3000, WRONG_TIME=300;
let hint, lastHint=0, wrongMeta, wrongPx;
let props, raf = 0, bump = -Infinity;
const LIFT = 140, DURATION = 580;
const ease = t => t*t*(3-2*t);
const mix = (a,b,t) => a+(b-a)*t;
const lerp2 = (a,b,t) => [mix(a[0],b[0],t),mix(a[1],b[1],t)];
const curve = (a,b,c,d,t) => lerp2(lerp2(lerp2(a,b,t),lerp2(b,c,t),t),lerp2(lerp2(b,c,t),lerp2(c,d,t),t),t);
const art = new Image(), mask = new Image();
let px, w, h, cw = 1, ch = 1, dpi = 1, scale = 1, tx = 0, ty = 0, panX = 0, panY = 0, ready = false, drag;
const box = () => {
  scale = Math.max(cw / w, ch / h) * 1.15;
  const ex = (w * scale - cw) / 2, ey = (h * scale - ch) / 2;
  panX = Math.max(-ex, Math.min(ex, panX));
  panY = Math.max(-ey, Math.min(ey, panY));
  tx = -ex + panX; ty = -ey + panY;
};
function paint(now=performance.now()) {
  if (!ready) return;
  box();
  ctx.setTransform(dpi, 0, 0, dpi, 0, 0);
  ctx.clearRect(0, 0, cw, ch);
  ctx.drawImage(art, tx, ty, w * scale, h * scale);
  for (const id of taken) {
    const {patch:[x,y,pw,ph],origin:[ox,oy]} = props[id];
    ctx.drawImage(atlas,x,y,pw,ph,tx+ox*scale,ty+oy*scale,pw*scale,ph*scale);
  }
  for (const [id,begin] of wrongMoves) {
    const t=Math.min(1,(now-begin)/WRONG_TIME);
    const p=wrongMeta[id], [x,y]=p.origin;
    stamp(wrongArt,p.patch,x,y);
    stamp(wrongArt,p.sprite,x,y,Math.sin(t*Math.PI*5)*5.5*(1-t));
  }
  if (hint) drawHint(now);
}
function stamp(image,[ax,ay,w,h],x,y,dx=0) {
  ctx.drawImage(image,ax,ay,w,h,tx+x*scale+dx,ty+y*scale,w*scale,h*scale);
}
function drawHint(now) {
  const d=props[hint.id], age=Math.max(0,now-hint.at);
  const alpha=Math.min(age/120,1)*(1-ease(Math.max(0,Math.min(1,(age-(HINT_TIME-320))/320))));
  ctx.save();
  ctx.globalAlpha=alpha;
  stamp(atlas,d.patch,...d.origin);
  const c=[tx+d.hint_center[0]*scale,ty+d.hint_center[1]*scale];
  const [x,y,w,h]=d.hint;
  const z=1+(.5+.5*Math.sin(age/1000*Math.PI*2*1.12))*.10*alpha;
  const W=w*scale*z, H=h*scale*z;
  ctx.drawImage(atlas,x,y,w,h,c[0]-W/2,c[1]-H/2,W,H);
  const radius=Math.hypot(W,H)/2+10, spin=age/1000*Math.PI*2*.53;
  ctx.lineCap="round";
  const at=(a,r)=>[c[0]+Math.cos(a)*r,c[1]+Math.sin(a)*r];
  const ray=(start,end,color,width)=>{ctx.beginPath();ctx.moveTo(...start);ctx.lineTo(...end);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();};
  for(let i=0;i<12;i++){
    const a=spin+i*Math.PI/6, r=radius+(i%2?11:5), lo=at(a-.10,r-4), hi=at(a+.075,r+7);
    ray(lo,hi,"#fab73440",5);
    ray(lo,hi,"#ffce5deb",2);
    ray(at(a+.082,r-5),at(a-.060,r+6),"#fff7dce6",1);
  }
  ctx.restore();
}
function setHint() {
  if (!ready || taken.size===TOTAL) return;
  const ids=Array.from({length:TOTAL},(_,k)=>(lastHint+k)%TOTAL+1).filter(id=>!taken.has(id));
  const seen=(id)=>{const [x,y]=props[id].hint_center;return x*scale+tx>29&&x*scale+tx<cw-29&&y*scale+ty>42&&y*scale+ty<ch-29;};
  const id=ids.find(seen)||ids[0];
  if(!seen(id)) {const [x,y]=props[id].hint_center;panX+=cw/2-(tx+x*scale);panY+=ch/2-(ty+y*scale);box();}
  lastHint=id;hint={id,at:performance.now()};
  if(!raf)raf=requestAnimationFrame(frame);
}
new ResizeObserver(() => {
  const bounds = canvas.getBoundingClientRect();
  cw = bounds.width; ch = bounds.height; dpi = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(cw * dpi); canvas.height = Math.round(ch * dpi);
  const q=layer.getBoundingClientRect(); layer.width=Math.round(q.width*dpi); layer.height=Math.round(q.height*dpi);
  paint();
}).observe(document.querySelector(".case"));
function sync() {
  document.querySelector("#count").textContent = found.size + "/" + TOTAL;
  document.querySelector("#victory").hidden = found.size !== TOTAL;
  hintButton.disabled = !ready || taken.size===TOTAL;
  paint();
}
function frame(now) {
  raf = 0;
  if(hint || wrongMoves.size) {
    if(hint && now-hint.at>=HINT_TIME) hint=undefined;
    for(const [id,at] of wrongMoves) if(now-at>=WRONG_TIME) wrongMoves.delete(id);
    paint(now);
  }
  liftCtx.setTransform(dpi,0,0,dpi,0,0);
  liftCtx.clearRect(0,0,layer.width/dpi,layer.height/dpi);
  const a=canvas.getBoundingClientRect(), b=layer.getBoundingClientRect();
  const k=boxImg.getBoundingClientRect();
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
  if(flying.size||pulse>0||hint||wrongMoves.size) raf=requestAnimationFrame(frame);
}
function take(id) {
  if(taken.has(id))return;
  const [x,y]=props[id].center;
  taken.add(id);
  if(hint?.id===id)hint=undefined;
  hintButton.disabled=taken.size===TOTAL;
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
      if(id>=1 && id<=TOTAL && Math.abs(r-id*32)<=2 && px[j+1]<4 && px[j+2]<4) take(id);
      else {
        const wrongId=Math.round(wrongPx[j]/8);
        if(Object.hasOwn(wrongMeta,wrongId)){
          wrongMoves.set(wrongId,performance.now());
          if(!raf)raf=requestAnimationFrame(frame);
        }
      }
    }
  }
  drag=undefined;
});
for (const type of ["pointercancel","lostpointercapture"]) canvas.addEventListener(type,e=>{ if(drag?.id===e.pointerId) drag=undefined; });
hintButton.addEventListener("click",setHint);
document.getElementById("again").addEventListener("click", () => {found.clear();taken.clear();flying.clear();wrongMoves.clear();hint=undefined;lastHint=0;panX=panY=0;bump=-Infinity;
  if(raf){cancelAnimationFrame(raf);raf=0;}
  frame(performance.now());sync();});
const load=(img,path)=>new Promise((yes,no)=>{img.onload=yes;img.onerror=no;img.src=path;});
const dataFrom=async path=>{const r=await fetch(path);if(!r.ok)throw Error("Missing scene data");return r.json();};
Promise.all([
  load(art,"./assets/room.webp"),load(mask,"./assets/pick.png"),
  load(atlas,"./assets/pickups.webp?v=3"),dataFrom("./assets/pickups.json?v=3"),
  load(wrongArt,"./assets/wrong.webp"),load(wrongImage,"./assets/wrong.png"),dataFrom("./assets/wrong.json")
]).then(([, , , data, , , decoys])=>{
  props=data;wrongMeta=decoys;
  w=art.naturalWidth;h=art.naturalHeight;
  function pixels(src) {
    if(w!==src.naturalWidth||h!==src.naturalHeight) throw Error("Misaligned pick map");
    const c=document.createElement("canvas");c.width=w;c.height=h;const d=c.getContext("2d",{willReadFrequently:true});d.drawImage(src,0,0);
    return d.getImageData(0,0,w,h).data;
  }
  px=pixels(mask);wrongPx=pixels(wrongImage);
  ready=true;document.getElementById("loading").hidden=true;sync();
}).catch(()=>{document.getElementById("loading").textContent="场景没有加载，请刷新重试。";});

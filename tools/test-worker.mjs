import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import worker from "../dist/worker.mjs";
for(const path of ["/","/style.css","/game.js","/assets/room.webp","/assets/pick.png","/assets/pickups.webp","/assets/pickups.json","/assets/paw-box.svg","/assets/wrong.webp","/assets/wrong.png","/assets/wrong.json","/assets/hint-ray.png"]){
  const res = await worker.fetch(new Request("https://example.invalid"+path));
  assert.equal(res.status, 200, path);
  assert.deepEqual(Buffer.from(await res.arrayBuffer()),readFileSync("dist"+(path==="/"?"/index.html":path)),path);
}
assert.equal((await worker.fetch(new Request("https://example.invalid/missing"))).status,404);
assert.equal((await worker.fetch(new Request("https://example.invalid/",{method:"POST"}))).status,405);
console.log("Worker routes and exact asset bytes verified");
const replay = await worker.fetch(new Request("https://example.invalid/physics/"));
assert.equal(replay.status,200);
assert.match(await replay.text(),/不是实时试玩/);
const full=readFileSync("dist/assets/physics.mp4");
const clip=await worker.fetch(new Request("https://example.invalid/assets/physics.mp4",{headers:{Range:"bytes=0-127"}}));
assert.equal(clip.status,206);
assert.equal(clip.headers.get("content-range"),"bytes 0-127/"+full.length);
assert.deepEqual(Buffer.from(await clip.arrayBuffer()),full.subarray(0,128));
assert.equal((await worker.fetch(new Request("https://example.invalid/assets/physics.mp4",{headers:{Range:"bytes="+full.length+"-"}}))).status,416);
console.log("Replay and partial media reads verified");

assert.equal((await worker.fetch(new Request("https://example.invalid/physics"))).status,308);
const assetBinding={async fetch(req) {
  const {pathname}=new URL(req.url);
  if(!pathname.startsWith("/physics/")||pathname.includes(".."))return new Response(null,{status:404});
  try {
    const file=readFileSync("dist/static"+pathname);
    const type=pathname.endsWith(".html")?"text/html":
      pathname.endsWith(".js")?"text/javascript":"application/octet-stream";
    return new Response(req.method==="HEAD"?null:file,{headers:{"Content-Type":type,"Content-Length":file.length}});
  } catch(e) {
    if(e.code!=="ENOENT")throw e;
    return new Response(null,{status:404});
  }
}};
if ((await assetBinding.fetch(new Request("https://example.invalid/physics/index.html",{method:"HEAD"}))).ok) {
  const request=(path,method)=>worker.fetch(new Request("https://example.invalid"+path,{method}),{ASSETS:assetBinding});
  const page=await request("/physics/");
  assert.equal(page.status,200);
  assert.match(await page.text(),/engine.startGame/);
  assert.match(page.headers.get("content-security-policy"),/wasm-unsafe-eval/);
  const engine=await request("/physics/engine.wasm");
  assert.equal(engine.headers.get("content-type"),"application/wasm");
  assert.equal(engine.headers.get("content-encoding"),"gzip");
  const {gunzipSync}=await import("node:zlib");
  assert.deepEqual([...gunzipSync(Buffer.from(await engine.arrayBuffer())).subarray(0,8)],[0,97,115,109,1,0,0,0]);
  assert.equal((await request("/physics/engine.wasm","HEAD")).status,200);
  for(const path of ["/physics/engine.js","/physics/engine.pck","/physics/engine.audio.worklet.js"]){
    assert.equal((await request(path,"HEAD")).status,200,path);
  }
  assert.match(await (await request("/physics/replay/")).text(),/不是实时试玩/);
  console.log("Playable Godot page, WASM decoding and replay fallback verified");
}

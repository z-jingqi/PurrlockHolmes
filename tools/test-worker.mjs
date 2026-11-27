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

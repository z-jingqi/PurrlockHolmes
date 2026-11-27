import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import worker from "../dist/worker.mjs";
for(const path of ["/","/style.css","/game.js","/assets/room.webp","/assets/pick.png"]){
  const res = await worker.fetch(new Request("https://example.invalid"+path));
  assert.equal(res.status, 200, path);
  assert.deepEqual(Buffer.from(await res.arrayBuffer()),readFileSync("dist"+(path==="/"?"/index.html":path)),path);
}
assert.equal((await worker.fetch(new Request("https://example.invalid/missing"))).status,404);
assert.equal((await worker.fetch(new Request("https://example.invalid/",{method:"POST"}))).status,405);
console.log("Worker routes and exact asset bytes verified");

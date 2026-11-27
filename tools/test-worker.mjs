import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {gunzipSync} from "node:zlib";
import worker from "../web/worker.mjs";
const ASSETS={async fetch(request) {
  const path=new URL(request.url).pathname;
  const body=readFileSync("dist/static"+path);
  const type=path.endsWith(".html")?"text/html":"application/octet-stream";
  return new Response(request.method==="HEAD"?null:body,{headers:{"Content-Type":type,"Content-Length":body.length}});
}};
const request=(path,method)=>worker.fetch(new Request("https://example.invalid"+path,{method}),{ASSETS});
const page=await request("/");
assert.equal(page.status,200);
assert.match(await page.text(),/engine.startGame/);
assert.match(page.headers.get("content-security-policy"),/wasm-unsafe-eval/);
const wasm=await request("/engine.wasm");
assert.equal(wasm.headers.get("content-type"),"application/wasm");
assert.equal(wasm.headers.get("content-encoding"),"gzip");
assert.deepEqual([...gunzipSync(Buffer.from(await wasm.arrayBuffer())).subarray(0,8)],[0,97,115,109,1,0,0,0]);
assert.equal((await request("/engine.wasm","HEAD")).status,200);
for(const path of ["/engine.js","/engine.pck","/engine.audio.worklet.js","/font-license.txt"])
  assert.equal((await request(path,"HEAD")).status,200,path);
for(const path of ["/physics/","/physics/replay/","/game.js","/missing"])
  assert.equal((await request(path)).status,404,path);
assert.equal((await request("/", "POST")).status,405);
console.log("Single playable game, assets, and removed legacy routes verified");

// The only game is the shared Godot scene. Host its compressed WASM under the normal engine URL.
const files=new Set(["/index.html","/engine.js","/engine.pck","/engine.audio.worklet.js",
  "/engine.audio.position.worklet.js","/font-license.txt"]);
export default {
  async fetch(request, env) {
    const url=new URL(request.url);
    const method=request.method;
    if(method!=="GET"&&method!=="HEAD")return new Response("Method not allowed",{status:405,headers:{Allow:"GET, HEAD"}});
    const route=url.pathname==="/" ? "/index.html" : url.pathname;
    const wasm=route==="/engine.wasm";
    if(!wasm&&!files.has(route))return new Response("Not found",{status:404});
    url.pathname=wasm?"/engine.wasm.gz":route;
    const asset=await env.ASSETS.fetch(new Request(url,{method,headers:wasm?{"Accept-Encoding":"identity"}:{}}));
    if (!asset.ok) return asset;
    const headers=new Headers(asset.headers);
    headers.set("X-Content-Type-Options","nosniff");
    if(wasm){
      headers.set("Content-Type","application/wasm");
      headers.set("Content-Encoding","gzip");
      headers.delete("Accept-Ranges");
    }else if(route==="/index.html"){
      headers.set("Cache-Control","no-cache");
      headers.set("Content-Security-Policy","default-src 'none'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self'; worker-src 'self' blob:; base-uri 'none'; form-action 'none'");
    }
    return new Response(asset.body,{status:asset.status,headers,encodeBody:wasm?"manual":"automatic"});
  }
};

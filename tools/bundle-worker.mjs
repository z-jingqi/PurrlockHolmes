// Same bundle for Wrangler and first deployment through the Cloudflare API.
import {readFileSync,writeFileSync} from "node:fs";
const types = {
  "/index.html":"text/html; charset=utf-8",
  "/physics.html":"text/html; charset=utf-8",
  "/assets/physics.mp4":"video/mp4",
  "/assets/physics-poster.webp":"image/webp",
  "/style.css":"text/css; charset=utf-8",
  "/game.js":"text/javascript; charset=utf-8",
  "/assets/room.webp":"image/webp",
  "/assets/pick.png":"image/png",
  "/assets/pickups.webp":"image/webp",
  "/assets/pickups.json":"application/json; charset=utf-8",
  "/assets/paw-box.svg":"image/svg+xml",
  "/assets/wrong.webp":"image/webp",
  "/assets/wrong.png":"image/png",
  "/assets/wrong.json":"application/json; charset=utf-8",
  "/assets/hint-ray.png":"image/png",
};
const files = Object.fromEntries(Object.entries(types).map(([p,t]) => [p,[t,readFileSync("dist"+p).toString("base64")]]));
writeFileSync("dist/worker.mjs", `const files=${JSON.stringify(files)};
export default {async fetch(req, env){
  if(req.method!=="GET"&&req.method!=="HEAD")return new Response("Method not allowed",{status:405,headers:{Allow:"GET, HEAD"}});
  const route=new URL(req.url).pathname;
  if(route==="/physics")return Response.redirect(new URL("/physics/",req.url),308);
  if(env?.ASSETS&&route==="/physics/"){
    const page=await env.ASSETS.fetch(new Request(new URL("/physics/index.html",req.url),{method:req.method}));
    const headers=new Headers(page.headers);
    headers.set("Cache-Control","no-cache");
    headers.set("X-Content-Type-Options","nosniff");
    headers.set("Content-Security-Policy","default-src 'none'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'unsafe-inline'; connect-src 'self'; worker-src 'self' blob:; base-uri 'none'; form-action 'none'");
    return new Response(page.body,{status:page.status,headers});
  }
  if(env?.ASSETS&&route==="/physics/engine.wasm"){
    const input=await env.ASSETS.fetch(new Request(new URL("/physics/engine.wasm.gz",req.url),{method:req.method,headers:{"Accept-Encoding":"identity"}}));
    if(!input.ok)return input;
    const headers=new Headers(input.headers);
    headers.set("Content-Type","application/wasm");
    headers.set("Content-Encoding","gzip");
    headers.delete("Accept-Ranges");
    headers.set("X-Content-Type-Options","nosniff");
    return new Response(input.body,{status:input.status,headers,encodeBody:"manual"});
  }
  if(env?.ASSETS&&route.startsWith("/physics/")&&route!=="/physics/replay/")return env.ASSETS.fetch(req);
  const p=route==="/"?"/index.html":route==="/physics/replay/"||route==="/physics/"?"/physics.html":route;
  const file=Object.hasOwn(files,p)?files[p]:null;
  if(!file)return new Response("Not found",{status:404});
  const bytes=Uint8Array.from(atob(file[1]),c=>c.charCodeAt(0));
  const headers={"Content-Type":file[0],"Cache-Control":"public, max-age=300",
      "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer",
      "Content-Security-Policy":"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; media-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'"};
  if(file[0]==="video/mp4"){
    headers["Accept-Ranges"]="bytes";
    const raw=req.headers.get("Range");
    if(raw){
      const m=/^bytes=([0-9]*)-([0-9]*)$/.exec(raw);
      const size=bytes.length;
      if(!m||(!m[1]&&!m[2]))return new Response(null,{status:416,headers:{"Content-Range":"bytes */"+size}});
      const min=m[1]?Number(m[1]):Math.max(0,size-Number(m[2]));
      const max=m[1]&&m[2]?Math.min(size-1,Number(m[2])):size-1;
      if(min>=size||max<min)return new Response(null,{status:416,headers:{"Content-Range":"bytes */"+size}});
      headers["Content-Range"]="bytes "+min+"-"+max+"/"+size;
      headers["Content-Length"]=String(max-min+1);
      return new Response(req.method==="HEAD"?null:bytes.subarray(min,max+1),{status:206,headers});
    }
  }
  headers["Content-Length"]=String(bytes.length);
  return new Response(req.method==="HEAD"?null:bytes,{headers});
}};
`);

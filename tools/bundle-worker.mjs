// Same bundle for Wrangler and first deployment through the Cloudflare API.
import {readFileSync,writeFileSync} from "node:fs";
const types = {
  "/index.html":"text/html; charset=utf-8",
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
export default {fetch(req){
  if(req.method!=="GET"&&req.method!=="HEAD")return new Response("Method not allowed",{status:405,headers:{Allow:"GET, HEAD"}});
  const p=new URL(req.url).pathname;
  const file=Object.hasOwn(files,p==="/"?"/index.html":p)?files[p==="/"?"/index.html":p]:null;
  if(!file)return new Response("Not found",{status:404});
  return new Response(req.method==="HEAD"?null:Uint8Array.from(atob(file[1]),c=>c.charCodeAt(0)),{
    headers:{"Content-Type":file[0],"Cache-Control":"public, max-age=300",
      "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer",
      "Content-Security-Policy":"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'"}});
}};
`);

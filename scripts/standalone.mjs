// Standalone personal server. Node.js standard library only; loopback access only.
import http from 'node:http';
import { readFile, mkdir, writeFile, rename } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../public/',import.meta.url));
const directory=fileURLToPath(new URL('../.local-data/',import.meta.url));
const file=resolve(directory,'progress.json');
await mkdir(directory,{recursive:true});
let records=new Map();
try { const data=JSON.parse(await readFile(file,'utf8')); records=new Map(data.items.map(r=>[r.key,r])); }
catch(e) { if(e.code!=='ENOENT') throw e; }
let queue=Promise.resolve();
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.webmanifest':'application/manifest+json'};
const server=http.createServer(async(req,res)=>{
 const json=(data,status=200)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
 try {
  const address=server.address();const allowed=`127.0.0.1:${address.port}`;
  if(req.headers.host!==allowed)return json({error:'invalid_host'},403);
  if(req.headers.origin&&req.headers.origin!==`http://${allowed}`)return json({error:'invalid_origin'},403);
  const url=new URL(req.url,`http://${allowed}`);
  if(url.pathname==='/api/sync'){
   if(req.method==='GET'){
    await queue;const after=url.searchParams.get('after')||'';
    const rows=[...records.values()].filter(r=>r.key>after).sort((a,b)=>a.key<b.key?-1:1);
    const items=rows.slice(0,1000);return json({items,next:rows.length>1000?items.at(-1).key:null});
   }
   if(req.method!=='POST')return json({error:'method_not_allowed'},405);
   let body='';for await(const chunk of req){body+=chunk;if(Buffer.byteLength(body)>2000000)return json({error:'too_large'},413);}
   let data;try{data=JSON.parse(body);}catch{return json({error:'invalid_json'},400);}
   if(!Array.isArray(data.items)||data.items.length>100||!data.items.every(r=>r&&typeof r.key==='string'&&/^[edcrhw]:/.test(r.key)&&r.key.length<300&&Number.isSafeInteger(r.stamp)&&r.stamp>0&&r.stamp<=Date.now()+300000&&r.value!==undefined))return json({error:'invalid_items'},400);
   const save=queue.then(async()=>{
    const next=new Map(records);
    for(const {key,value,stamp} of data.items)if(!next.has(key)||stamp>next.get(key).stamp)next.set(key,{key,value,stamp});
    await writeFile(file+'.tmp',JSON.stringify({version:1,items:[...next.values()]},null,2),{mode:0o600});
    await rename(file+'.tmp',file);records=next;
   });queue=save.catch(()=>{});await save;return json({ok:true,saved:data.items.length});
  }
  if(!['GET','HEAD'].includes(req.method))return json({error:'method_not_allowed'},405);
  let pathname;try{pathname=decodeURIComponent(url.pathname);}catch{return json({error:'bad_path'},400);}
  const target=resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(!target.startsWith(resolve(root)+sep))return json({error:'forbidden'},403);
  const content=await readFile(target);res.writeHead(200,{'Content-Type':types[extname(target)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(req.method==='HEAD'?undefined:content);
 }catch(e){if(e.code==='ENOENT'||e.code==='EISDIR')json({error:'not_found'},404);else{console.error(e.message);json({error:'server_error'},500);}}
});
server.listen(Number(process.env.PORT||3000),'127.0.0.1',()=>console.log(`Мой китайский: http://127.0.0.1:${server.address().port}\nПрогресс: ${file}`));

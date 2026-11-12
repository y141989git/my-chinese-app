import { env } from 'cloudflare:workers';
import { chatGPTSignInPath } from '../../chatgpt-auth';
export const dynamic='force-dynamic';
const json=(data:unknown,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}});
function user(request:Request){return request.headers.get('oai-authenticated-user-id')}
export async function GET(request:Request){
 const id=user(request);if(!id)return json({error:'sign_in_required',signInPath:chatGPTSignInPath('/index.html')},401);
 if(!env.DB)return json({error:'storage_unavailable'},503);
 const url=new URL(request.url),after=url.searchParams.get('after')||'';
 const result=await env.DB.prepare('SELECT record_key AS key, value, updated_at AS stamp FROM learning_records WHERE user_id = ? AND record_key > ? ORDER BY record_key LIMIT 1001').bind(id,after).all<{key:string,value:string,stamp:number}>();
 const rows=result.results||[],more=rows.length>1000,items=rows.slice(0,1000).map(r=>({...r,value:JSON.parse(r.value)}));
 return json({items,next:more?items[items.length-1].key:null});
}
export async function POST(request:Request){
 const id=user(request);if(!id)return json({error:'sign_in_required',signInPath:chatGPTSignInPath('/index.html')},401);
 if(!env.DB)return json({error:'storage_unavailable'},503);
 const origin=request.headers.get('Origin');if(origin&&origin!==new URL(request.url).origin)return json({error:'invalid_origin'},403);
 if(Number(request.headers.get('Content-Length')||0)>2000000)return json({error:'too_large'},413);
 let body;try{const text=await request.text();if(text.length>2000000)return json({error:'too_large'},413);body=JSON.parse(text)}catch{return json({error:'invalid_json'},400)}
 if(!Array.isArray(body.items)||body.items.length>100)return json({error:'invalid_items'},400);
 const items=body.items;
 if(!items.every((x:any)=>x&&typeof x.key==='string'&&/^[edcrhw]:/.test(x.key)&&x.key.length<300&&Number.isSafeInteger(x.stamp)&&x.stamp>0&&x.stamp<=Date.now()+300000&&x.value!==undefined&&JSON.stringify(x.value).length<1000000))return json({error:'invalid_record'},400);
 if(items.length)await env.DB.batch(items.map((x:any)=>env.DB.prepare('INSERT INTO learning_records (user_id, record_key, value, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, record_key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at WHERE excluded.updated_at > learning_records.updated_at').bind(id,x.key,JSON.stringify(x.value),x.stamp)));
 return json({ok:true,saved:items.length});
}

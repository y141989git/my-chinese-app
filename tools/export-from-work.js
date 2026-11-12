// Run in the browser console ON THE ORIGINAL SITE after signing in and syncing.
// Read-only: downloads a backup; never sends or changes records.
(async()=>{
 const read=(name,store,key)=>new Promise((resolve,reject)=>{
  const q=indexedDB.open(name);q.onerror=()=>reject(q.error);q.onsuccess=()=>{
   const db=q.result;if(!db.objectStoreNames.contains(store)){db.close();resolve(null);return;}
   const tx=db.transaction(store),r=key===undefined?tx.objectStore(store).getAll():tx.objectStore(store).get(key);
   r.onsuccess=()=>{resolve(r.result);db.close();};r.onerror=()=>reject(r.error);
  };
 });
 const source=await fetch('/source.json').then(r=>{if(!r.ok)throw Error('source.json недоступен');return r.json();});
 const raw=await fetch('/raw.json').then(r=>{if(!r.ok)throw Error('raw.json недоступен');return r.json();});
 const state=await read('my-chinese-workbench','settings','state')||JSON.parse(localStorage.getItem('chinese-workbench-v2')||'{}');
 const writing=Object.fromEntries((await read('chinese-writing-practice','cards')||[]).map(r=>[r.id,r]));
 const items=[];let after='';
 do {const r=await fetch('/api/sync'+(after?'?after='+encodeURIComponent(after):''),{cache:'no-store'});
  if(!r.ok)throw Error('Сначала войдите в ChatGPT и дождитесь синхронизации: '+r.status);
  const page=await r.json();items.push(...page.items);after=page.next;
 }while(after);
 // Synced server values first, then this device's latest saved state.
 const edits={},deleted=new Set(),completed=new Set(),extraRaw=[],history=[];
 for(const r of items){if(r.value===null)continue;const id=r.key.slice(2);
  if(r.key.startsWith('e:'))edits[id]=r.value;
  if(r.key.startsWith('d:')&&r.value)deleted.add(id);
  if(r.key.startsWith('c:')&&r.value)completed.add(id);
  if(r.key.startsWith('r:'))extraRaw.push(r.value);
  if(r.key.startsWith('h:'))history.push(r.value);
  if(r.key.startsWith('w:')&&!writing[id])writing[id]=r.value;
 }
 Object.assign(edits,state.edits||{});for(const id of state.deleted||[])deleted.add(id);for(const id of state.completed||[])completed.add(id);
 const data=new Map(source.clean.map(d=>[d.id,d]));for(const [id,d]of Object.entries(edits))data.set(id,{...data.get(id),...d});
 const byId=rows=>[...new Map(rows.map(r=>[r.id,r])).values()];
 const backup={version:2,exported:new Date().toISOString(),data:[...data.values()].filter(d=>!deleted.has(d.id)),raw:byId([...raw,...extraRaw,...(state.extraRaw||[])]),completed:[...completed],deleted:[...deleted],history:[...history,...(state.history||[])],writing,sheets:source.sheets,sourceUrl:source.sourceUrl};
 const blob=new Blob([JSON.stringify(backup)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='my-chinese-work-export.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
 console.log('Резервная копия скачана. Записей:',backup.data.length,'Результатов письма:',Object.keys(writing).length);
})().catch(console.error);

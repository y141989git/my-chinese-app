// Full original lesson notes, separate from the edited practice cards.
window.LessonNotes=(()=>{
 let opened=false,notes=null,loading=false,error='',query='',tab='',page=0;
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const normalize=s=>String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 async function load(){if(notes||loading)return;loading=true;error='';try{const response=await fetch('/lesson-notes.json');if(!response.ok)throw Error();notes=await response.json();}catch{error='Не удалось загрузить конспект. Попробуй ещё раз.'}finally{loading=false;render();}}
 function html(){
  let content='';
  if(opened){
   if(!notes)content=`<p class="notice">${error||'Загружаю полный конспект…'}</p>${error?'<button id="retryLessonNotes">Повторить</button>':''}`;
   else{
    const rows=notes.tabs.filter(t=>!tab||t.id===tab).flatMap(t=>t.paragraphs.map((p,i)=>({...p,tabId:t.id,tabTitle:t.title,number:i+1})));
    const found=rows.filter(p=>!query||normalize(p.text).includes(normalize(query)));
    const pages=Math.max(1,Math.ceil(found.length/60));page=Math.min(page,pages-1);
    content=`<p class="sub">Полный текст обеих вкладок. Здесь сохранены записи учителя и ученика, включая упражнения и черновики. Это отдельный конспект, без автоматического превращения всех фрагментов в словарные карточки.</p><div class="bar"><input id="lessonNotesSearch" type="search" aria-label="Поиск в полном конспекте" placeholder="Найти слово или правило в конспекте…" value="${esc(query)}"><select id="lessonNotesTab" aria-label="Вкладка конспекта"><option value="">Обе вкладки</option>${notes.tabs.map(t=>`<option value="${esc(t.id)}" ${t.id===tab?'selected':''}>${esc(t.title)}</option>`).join('')}</select></div><p id="lessonNotesCount" class="sub" aria-live="polite">Найдено абзацев: ${found.length} · Всего: ${notes.audit.paragraphs} · Страница ${page+1} / ${pages}</p><div>${found.slice(page*60,(page+1)*60).map(p=>`<div class="lesson-source-paragraph" style="padding:12px 0;border-bottom:1px solid var(--line)"><small class="sub">${esc(p.tabTitle)} · ${p.number}</small><div style="white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8">${esc(p.text)}</div></div>`).join('')||'<p>Ничего не найдено.</p>'}</div><div class="bar"><button id="lessonNotesPrev" ${page===0?'disabled':''}>← Назад</button><span>${page+1} / ${pages}</span><button id="lessonNotesNext" ${page+1===pages?'disabled':''}>Далее →</button></div>`;
   }
  }
  return `<section class="panel" style="margin:16px 0"><h2>Полный конспект 燕子</h2><button id="toggleLessonNotes" aria-expanded="${opened}">${opened?'Свернуть конспект':'Открыть полный конспект'}</button>${content}</section>`;
 }
 function bind(){const get=id=>document.getElementById(id);const toggle=get('toggleLessonNotes');if(!toggle)return;
  toggle.onclick=()=>{opened=!opened;render();if(opened&&!notes)load();};
  if(get('retryLessonNotes'))get('retryLessonNotes').onclick=load;
  if(get('lessonNotesSearch'))get('lessonNotesSearch').oninput=e=>{query=e.target.value;page=0;const pos=e.target.selectionStart;render();const input=get('lessonNotesSearch');input.focus();input.setSelectionRange(pos,pos);};
  if(get('lessonNotesTab'))get('lessonNotesTab').onchange=e=>{tab=e.target.value;page=0;render();};
  if(get('lessonNotesPrev'))get('lessonNotesPrev').onclick=()=>{page=Math.max(0,page-1);render();};
  if(get('lessonNotesNext'))get('lessonNotesNext').onclick=()=>{page++;render();};
 }
 return {html,bind};
})();

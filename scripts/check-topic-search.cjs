const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app=fs.readFileSync('public/app.js','utf8'),db=JSON.parse(fs.readFileSync('public/source.json','utf8'));
const context=vm.createContext({console,Promise,Set,Map,JSON,Math,Date,document:{addEventListener(){}},localStorage:{getItem:()=>null},crypto:require('node:crypto').webcrypto});
vm.runInContext(app.slice(0,app.indexOf('let sourcesLoading')),context);
context.records=db.clean;
vm.runInContext(`data=records.map(standard);for(const d of data)d._search=fold([d.zh,d.py,d.ru,...d.examples.map(e=>[e.zh,e.py,e.ru].join(' '))].join(' '));`,context);
for(const group of ['Все','Площадка','Жизнь','Идиомы','HSK 4–5']){
  context.group=group;
  const result=vm.runInContext(`quizMode=group;quizTopic='';const poolIds${group.length}=new Set(quizPool().map(d=>d.id));startQuiz(quizPool());({n:quiz.length,valid:quiz.every(q=>poolIds${group.length}.has(q.d.id)&&q.options.every(x=>poolIds${group.length}.has(x.id))&&new Set(q.options.map(x=>norm(x.zh))).size===4&&new Set(q.options.map(x=>norm(x.ru))).size===4)})`,context);
  assert.equal(result.n,10,group);assert.ok(result.valid,group);
}
assert.ok(vm.runInContext(`quizMode='Площадка';quizTopic='Электрика и КИП';startQuiz(quizPool());quiz.length>0&&quiz.every(q=>q.d.tags.includes(quizTopic)&&q.options.every(d=>d.tags.includes(quizTopic)))`,context));
assert.ok(vm.runInContext(`quizTopic='Несуществующая тема';quizStarted=false;quiz=[];!quizHTML().includes('data-answer=')&&quizHTML().includes('минимум 4')`,context));
assert.ok(vm.runInContext(`quizMode='Выборка';quizTopic='';quizSelection=data.filter(d=>d.tags.includes('Еда и кофе')).map(d=>d.id);startQuiz(quizPool());quiz.every(q=>quizSelection.includes(q.d.id))`,context));
for(const d of db.clean){
  const seen=new Set();
  for(const ex of d.examples){for(const key of ['zh','py','ru'])assert.ok(typeof ex[key]==='string'&&ex[key].trim(),d.zh+' '+key);assert.ok(!seen.has(ex.zh),d.zh+' duplicate');seen.add(ex.zh)}
}
assert.equal(db.clean.filter(d=>d.tags.includes('Идиомы')&&d.zh.length===4&&!d.examples.length).length,0);
// Global search uses all records and ignores currently selected categories.
const searchCode=app.slice(app.indexOf('function searchRank('),app.indexOf('function renderGlobalSearch()'));
context.document={querySelector:()=>({value:'lang tun hu yan'})};
vm.runInContext(searchCode,context);
assert.ok(vm.runInContext(`onlyWork=true;topic='Электрика и КИП';globalMatches().some(d=>d.zh==='狼吞虎咽')`,context));
console.log('Passed: five quiz groups, topic isolation, empty topic, saved selection, global search, complete examples and 99 idioms.');

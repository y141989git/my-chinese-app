const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app=fs.readFileSync('public/app.js','utf8'),cloud=fs.readFileSync('public/cloud.js','utf8');
const storage=new Map();let persists=0;
const context=vm.createContext({JSON,Object,Math,Date,Map,Set,structuredClone,localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},dailyToday:()=> '2026-11-13',activeDevice:()=> 'phone',activeTab:()=> 'tab1',persist:()=>persists++});
vm.runInContext(app.slice(app.indexOf("const ACTIVITY_KEY="),app.indexOf('function rankSidebar(')),context);
vm.runInContext("recordPractice('cards');recordPractice('tests');recordPractice('cards');mergeActivity({'2026-11-13:phone:tab1':{cards:1,tests:0},'2026-11-13:mac:tab2':{cards:4,tests:3},'2026-11-12:phone:tab1':{cards:100,tests:100}})",context);
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(practiceToday())',context)),{cards:6,tests:4});assert.equal(persists,3);
context.input={activity:{'2026-11-13:phone:tab1':{cards:2,tests:1}},history:[]};
vm.runInContext('let records=new Map();'+cloud.slice(cloud.indexOf('function toMap('),cloud.indexOf('function setBaseline('))+';records=new Map([...toMap(input)].map(([key,value])=>[key,{key,value}]));',context);
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(fromRecords().activity)',context)),context.input.activity);
const grammar=JSON.parse(fs.readFileSync('public/hsk5-grammar.json','utf8'));assert.equal(grammar.lessons.length,36);assert.equal(grammar.lessons.flatMap(l=>l.points).length,110);
for(const [i,l]of grammar.lessons.entries()){assert.equal(l.number,i+1);for(const p of l.points){assert.ok(p.note.length>100);assert.ok(p.formula);assert.equal(p.examples.length,2);for(const e of p.examples){assert.ok(/[\u4e00-\u9fff]/.test(e.zh));assert.ok(/[а-яё]/i.test(e.ru));assert.ok(/[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]/.test(e.py))}}}
const data=JSON.parse(fs.readFileSync('public/source.json','utf8')).clean;assert.equal(data.filter(d=>/^пример[.!\s]*$/i.test(d.ru)).length,0);assert.ok(app.includes('${deepSeekHTML(d)}'));assert.ok(!app.includes('${googleHTML(d)}'));
console.log('Passed: daily counters, device merge, sync round-trip, 36 lessons / 110 points / 220 examples, translations, share button.');

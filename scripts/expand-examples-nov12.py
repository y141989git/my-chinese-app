"""Fill empty cards with authored or meaning-matched source examples, preserving prior examples.
Run with pypinyin 0.55.0. TSVs and the extracted source JSON are reviewable inputs.
"""
import json,re,collections,subprocess
from pathlib import Path
from pypinyin import lazy_pinyin,Style,load_phrases_dict

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'public/source.json';db=json.loads(path.read_text());words=db['clean']
load_phrases_dict({k:[[x] for x in v.split()] for k,v in {
 '调试':'tiáo shì','调平':'tiáo píng','调配':'tiáo pèi','核对':'hé duì','重新':'chóng xīn','处理':'chǔ lǐ','供货':'gōng huò','荷载':'hè zài','相连':'xiāng lián','提供':'tí gōng','发酵':'fā jiào','地道':'dì dao','出差':'chū chāi','薄膜':'báo mó','载荷':'zài hè','称重':'chēng zhòng','进行':'jìn xíng','银行':'yín háng','同行':'tóng háng','转型':'zhuǎn xíng','转让':'zhuǎn ràng','传感器':'chuán gǎn qì','供电':'gōng diàn','供汽':'gōng qì','供水':'gōng shuǐ','供给':'gōng jǐ','记录':'jì lù','角色':'jué sè','给我':'gěi wǒ','待会儿':'dāi huì er','好玩':'hǎo wán','重做':'chóng zuò','热胀冷缩':'rè zhàng lěng suō','还要':'hái yào','还是':'hái shì','应以':'yīng yǐ','应分别':'yīng fēn bié','差别':'chā bié','空白':'kòng bái','放在':'fàng zài','很久':'hěn jiǔ','长时间':'cháng shí jiān','一米七':'yì mǐ qī','混合':'hùn hé',
}.items()})
normalize=lambda s:re.sub(r'[^\u3400-\u9fff]','',s)
def complete(e):return bool(e.get('zh') and e.get('py') and e.get('ru'))
def has_example(d):return any(complete(e) for e in d.get('examples',[])) or bool(d.get('ex') and d.get('ep') and d.get('er'))
by=collections.defaultdict(list)
for d in words:by[normalize(d['zh'])].append(d)
before=sum(has_example(d) for d in words);previous={d['id']:json.dumps(d.get('examples',[]),ensure_ascii=False,sort_keys=True) for d in words}
links=[];absent=[];authored=[]
def add(d,e,kind):
 if has_example(d):return False
 assert complete(e) and normalize(d['zh']) in normalize(e['zh']) and normalize(d['zh'])!=normalize(e['zh']), (d['zh'],e['zh'])
 d.setdefault('examples',[]).append(dict(e,batch='context-expansion-20261112'));d.update(ex=e['zh'],ep=e['py'],er=e['ru'])
 links.append({'id':d['id'],'term':d['zh'],'example':e['zh'],'ru':e['ru'],'kind':kind})
 return True
for name in ['context-expansion-nov12.tsv','life-expansion-nov12.tsv']:
 for number,line in enumerate((ROOT/'examples'/name).read_text().splitlines(),1):
  keys,zh,ru=line.split('\t');assert len(ru)>12 and re.search('[А-Яа-яЁё]',ru)
  example={'zh':zh,'py':' '.join(lazy_pinyin(zh,style=Style.TONE)),'ru':ru,'origin':'Новый пример для практики','pyOrigin':'Автоматически · pypinyin 0.55.0','batch':'context-expansion-20261112'}
  authored.append(example)
  for key in keys.split('|'):
   assert normalize(key) in normalize(zh), (name,number,key)
   matches=by[normalize(key)]
   if not matches:absent.append(key)
   for d in matches:add(d,example,'authored')

# Reuse complete sentences only if both the Chinese expression and a Russian meaning stem match.
# This rejects mere Chinese substrings whose gloss belongs to another sense.
stop={'очень','котор','чтобы','этого','можно','челов','слово','значе','выраж','также','более','нужно','здесь','себя','быть','какой','какие','может','каким','когда','этот','тоже','такой'}
def roots(s):return {w[:5] if len(w)>5 else w for w in re.findall('[а-яё]{4,}',s.lower())}-stop
sources=json.loads((ROOT/'examples/source-context-nov12.json').read_text())
for e in sources:e.update(origin='Пример из конспекта 广州',pyOrigin='Из учебного разбора')
pool=authored+sources
for d in words:
 for e in d.get('examples',[]):
  if e.get('origin','').startswith('Добавлен для практики') and complete(e):pool.append(e)
unique={}
for e in pool:
 z=normalize(e['zh'])
 if 8<=len(z)<=95 and complete(e) and len(re.findall('[А-Яа-яЁё]+',e['ru']))>=4 and not re.search(r'[А-Яа-я]|_{2}|\[|\]',e['zh']) and not re.search(r'\?|нужно уточнить|моя фраза',e['ru'],re.I):unique.setdefault(z,e)
seg_code='const fs=require("fs");const xs=JSON.parse(fs.readFileSync(0,"utf8"));const seg=new Intl.Segmenter("zh",{granularity:"word"});process.stdout.write(JSON.stringify(xs.map(s=>[s,[...seg.segment(s)].flatMap(x=>[x.index,x.index+x.segment.length])])));'
seg_result=subprocess.run(['node','-e',seg_code],input=json.dumps(list(unique)),text=True,capture_output=True,check=True)
boundaries={text:set(points) for text,points in json.loads(seg_result.stdout)}
index=collections.defaultdict(list)
for e in unique.values():
 z=normalize(e['zh']);e_roots=roots(e['ru'])
 for length in range(2,min(12,len(z)-3)+1):
  for i in range(len(z)-length+1):
   term=z[i:i+length]
   if term in by and i in boundaries[z] and i+length in boundaries[z]:index[term].append((e,e_roots))
for d in words:
 if has_example(d):continue
 z=normalize(d['zh']);d_roots=roots(d.get('ru',''))
 if not 2<=len(z)<=12 or re.search(r'нужно уточнить|фрагмент|моя фраза',d.get('ru',''),re.I):continue
 candidates=sorted(index.get(z,[]),key=lambda item:(len(normalize(item[0]['zh'])),item[0]['zh']))
 for e,e_roots in candidates:
  if d_roots&e_roots and z!=normalize(e['zh']) and not (z.endswith('罐') and z+'车' in normalize(e['zh'])):
   add(d,e,'source' if e.get('source') else 'reused-authored');break

after=sum(has_example(d) for d in words)
assert not absent,absent
assert len({x['id'] for x in links})==len(links)
assert after-before==len(links)
changed_ids={x['id'] for x in links}
for d in words:
 if d['id'] not in changed_ids:assert json.dumps(d.get('examples',[]),ensure_ascii=False,sort_keys=True)==previous[d['id']]
summary={'before':before,'after':after,'addedCards':after-before,'remaining':len(words)-after,'total':len(words),'authoredSentences':len(authored),'sourceSentences':len(sources),'linksByKind':dict(collections.Counter(x['kind'] for x in links))}
db['examplesRevision']=max(4,db.get('examplesRevision',0)+1)
db.setdefault('exampleAudit',{}).update(withExamples=after,withoutExamples=len(words)-after,lastExpansion={'date':'2026-11-12',**summary},status='Дополнение продолжается')
path.write_text(json.dumps(db,ensure_ascii=False,separators=(',',':')))
(ROOT/'examples/expansion-nov12-audit.json').write_text(json.dumps({'summary':summary,'links':links},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))

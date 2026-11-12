"""Apply explicitly authored examples to missing records; existing examples stay intact.
Run with Python + pypinyin 0.55.0. The TSV is the reviewable sentence source.
"""
import json,re,collections
from pathlib import Path
from pypinyin import lazy_pinyin,Style,load_phrases_dict
root=Path(__file__).resolve().parents[1]
load_phrases_dict({k:[[x] for x in v.split()] for k,v in {'调试':'tiáo shì','调平':'tiáo píng','核对':'hé duì','重新':'chóng xīn','处理':'chǔ lǐ','供货':'gōng huò','荷载':'hè zài','相连':'xiāng lián','当成':'dàng chéng','提供':'tí gōng','人事':'rén shì','长大':'zhǎng dà'}.items()})
p=root/'public/source.json';j=json.loads(p.read_text());norm=lambda s:re.sub(r'[\s，。！？、；：,.!?…“”「」《》\-—·()（）]','',s)
by=collections.defaultdict(list)
for d in j['clean']:by[norm(d['zh'])].append(d)
before=sum(bool(d.get('examples') or d.get('ex')) for d in j['clean']);links=[];absent=[]
for line in (root/'examples/context-nov12.tsv').read_text().splitlines():
 keys,zh,ru=line.split('\t');ex={'zh':zh,'py':' '.join(lazy_pinyin(zh,style=Style.TONE)),'ru':ru,'origin':'Добавлен для практики · 12.11.2026','pyOrigin':'Автоматически · pypinyin 0.55.0'}
 for key in keys.split('|'):
  assert norm(key) in norm(zh),(key,zh)
  matches=by[norm(key)]
  if not matches:absent.append(key)
  for d in matches:
   if d.get('examples') or d.get('ex'):continue
   d['examples']=[ex.copy()];d.update(ex=zh,ep=ex['py'],er=ru);links.append({'id':d['id'],'zh':d['zh'],'example':zh})
after=sum(bool(d.get('examples') or d.get('ex')) for d in j['clean'])
j.setdefault('exampleAudit',{}).update(withExamples=after,withoutExamples=len(j['clean'])-after,lastBatch={'date':'2026-11-12','sentences':len((root/'examples/context-nov12.tsv').read_text().splitlines()),'links':len(links),'newCoverage':after-before},status='Дополнение продолжается')
p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')))
report={'before':before,'after':after,'newCoverage':after-before,'remaining':len(j['clean'])-after,'absentKeys':absent,'links':links}
(root/'examples/context-nov12-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='links'},ensure_ascii=False))

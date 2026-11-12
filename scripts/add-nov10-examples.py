"""Apply authored examples and publish exact coverage, preserving all existing records."""
import json,re,collections
from pathlib import Path
from pypinyin import lazy_pinyin,Style,load_phrases_dict
root=Path(__file__).resolve().parents[1];p=root/'public/source.json';j=json.loads(p.read_text())
fixes={'调平':['tiáo','píng'],'供液':['gōng','yè'],'供液管':['gōng','yè','guǎn'],'重新':['chóng','xīn'],'重型':['zhòng','xíng'],'荷载':['hè','zài'],'传递':['chuán','dì'],'处理':['chǔ','lǐ'],'校准':['jiào','zhǔn'],'长大':['zhǎng','dà'],'角色':['jué','sè'],'便宜':['pián','yi'],'舍得':['shě','de'],'舍不得':['shě','bu','de'],'结实':['jiē','shi'],'点焊':['diǎn','hàn']}
load_phrases_dict({k:[[v] for v in vs] for k,vs in fixes.items()})
norm=lambda s:re.sub(r'[\s，。！？、；：,.!?…“”「」《》\-—·()（）]','',s).lower()
by={norm(d['zh']):d for d in j['clean']};before=sum(bool(d['examples']) for d in j['clean']);links=0;absent=[]
lines=(root/'examples/context-nov10.tsv').read_text().splitlines()
for line in lines:
 keys,zh,ru=line.split('\t');ex={'zh':zh,'py':' '.join(lazy_pinyin(zh,style=Style.TONE)),'ru':ru,'origin':'Добавлен для практики · 10.11.2026','pyOrigin':'Автоматически'}
 for key in keys.split('|'):
  d=by.get(norm(key))
  if not d:absent.append(key);continue
  if any('исходн' in e.get('origin','').lower() or 'таблиц' in e.get('origin','').lower() or (not e.get('origin') and e.get('source')) for e in d['examples']):continue
  if any(norm(e['zh'])==norm(zh) for e in d['examples']):continue
  d['examples'].append(ex.copy());links+=1
for d in j['clean']:
 if d['examples']:
  e=d['examples'][0];d.update(ex=e['zh'],ep=e['py'],er=e['ru'])
j['exampleAudit'].update(withExamples=sum(bool(d['examples']) for d in j['clean']),withoutExamples=sum(not d['examples'] for d in j['clean']),lastBatch={'date':'2026-11-10','sentences':len(lines),'links':links,'newCoverage':sum(bool(d['examples']) for d in j['clean'])-before},status='Дополнение продолжается')
j['audit']['complete']=sum(bool(d.get('ru') and d.get('py')) for d in j['clean']);p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')))
print(json.dumps({'batch':j['exampleAudit'],'absent':absent},ensure_ascii=False))

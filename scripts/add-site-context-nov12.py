import csv,json,re
from pathlib import Path
from pypinyin import lazy_pinyin, Style, load_phrases_dict
load_phrases_dict({'设备': [['shè'], ['bèi']], '重量': [['zhòng'], ['liàng']], '重新': [['chóng'], ['xīn']], '处理': [['chǔ'], ['lǐ']], '位置': [['wèi'], ['zhì']], '行业': [['háng'], ['yè']], '铺设': [['pū'], ['shè']]})
p=Path('public/source.json'); data=json.loads(p.read_text()); entries=data['clean']; by={}
for item in entries: by.setdefault(item.get('zh',''),[]).append(item)
added=[]
with open('examples/site-context-nov12.tsv',encoding='utf8') as f:
 for keys,zh,ru in csv.reader(f,delimiter='\t'):
  py=' '.join(lazy_pinyin(zh,style=Style.TONE,errors=lambda s:list(s)))
  py=re.sub(r'\s+([，。？！；：、])',r'\1',py)
  for key in keys.split('|'):
   for item in by.get(key,[]):
    if item.get('examples'): continue
    # Ellipsis expresses a pattern rather than a literal substring.
    if key!='以…为基础' and key not in zh: raise ValueError((key,zh))
    item['examples']=[{'zh':zh,'py':py,'ru':ru,'origin':'Добавлен для практики','pyOrigin':'Автоматически'}]
    added.append({'id':item['id'],'word':key,'example':zh})
p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
Path('examples/site-context-nov12-audit.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Added examples to',len(added),'cards')

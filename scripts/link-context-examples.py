"""Link sentence records to terms in the same original row; retain provenance."""
import collections
import json
import re
from pathlib import Path
from pypinyin import lazy_pinyin, Style

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'public/source.json'
db = json.loads(path.read_text())
words = db['clean']
by_row = collections.defaultdict(list)
normalize = lambda s: re.sub(r'[\s，。！？、；：,.!?…“”「」《》\-—·()（）]', '', s).lower()

def sentence(w):
    z = w['zh']
    return (9 <= len(z) <= 140 and
            bool(re.search(r'[。！？!?，,]|我们|你们|他们|这个|请|需要|应该|必须|已经|如果|以后', z)) and
            bool(w.get('py')) and bool(w.get('ru')) and
            not re.search(r'Перевод не|Нужно уточнить|需要翻译', w['ru']))

for w in words:
    if sentence(w):
        for src in w['sources']:
            by_row[src['sheet'], src['row']].append((w, src))

added_original = added_authored = 0
for w in words:
    if not (2 <= len(normalize(w['zh'])) <= 12):
        continue
    examples = w.setdefault('examples', [])
    seen = {normalize(e['zh']) for e in examples}
    for src in w['sources']:
        for candidate, location in by_row[src['sheet'], src['row']]:
            if (normalize(w['zh']) not in normalize(candidate['zh']) or
                normalize(candidate['zh']) in seen or
                normalize(candidate['zh']) == normalize(w['zh'])):
                continue
            examples.append(dict(zh=candidate['zh'], py=candidate['py'], ru=candidate['ru'],
                                 origin='Из исходной таблицы', source=location,
                                 pyOrigin=candidate.get('pyOrigin', 'Из таблицы'),
                                 translationOrigin=candidate.get('translationOrigin', 'Из учебной базы')))
            seen.add(normalize(candidate['zh']))
            added_original += 1

authored = []
for line in (ROOT / 'examples/context-examples.tsv').read_text().splitlines():
    keys, zh, ru = line.split('\t')
    ex = dict(zh=zh, py=' '.join(lazy_pinyin(zh, style=Style.TONE)), ru=ru,
              origin='Добавлен для практики', pyOrigin='Автоматически')
    authored.append((keys.split('|'), ex))
for w in words:
    for keys, ex in authored:
        if w['zh'] in keys and all(normalize(e['zh']) != normalize(ex['zh']) for e in w['examples']):
            w['examples'].append(dict(ex))
            added_authored += 1
    if w['examples']:
        first = w['examples'][0]
        w.update(ex=first['zh'], ep=first['py'], er=first['ru'])

db['examplesRevision'] = 1
db['exampleAudit'] = dict(originalLinksAdded=added_original, authoredLinksAdded=added_authored,
                          authoredSentences=len(authored),
                          withExamples=sum(bool(w['examples']) for w in words),
                          withoutExamples=sum(not w['examples'] for w in words),
                          status='Перенос и дополнение продолжаются')
path.write_text(json.dumps(db, ensure_ascii=False, separators=(',', ':')))
print(json.dumps(db['exampleAudit'], ensure_ascii=False))

"""Add authored contextual sentences and reuse complete source sentences."""
import collections
import json
import re
from pathlib import Path
from pypinyin import lazy_pinyin, Style, load_phrases_dict
load_phrases_dict({k: [[v] for v in vals] for k, vals in {"饿得": ["è", "de"], "忙得": ["máng", "de"], "讨论得": ["tǎo", "lùn", "de"], "玩得": ["wán", "de"], "听得": ["tīng", "de"]}.items()})

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'public/source.json'
db = json.loads(path.read_text())
words = db['clean']
normalize = lambda s: re.sub(r'[\s，。！？、；：,.!?…“”「」《》\-—·()（）]', '', s).lower()
terms = {w['zh']: w for w in words if re.fullmatch(r'[\u4e00-\u9fff]{2,8}', w['zh'])}
added = collections.Counter()

def add(w, example, kind):
    examples = w.setdefault('examples', [])
    if any(normalize(e['zh']) == normalize(example['zh']) for e in examples):
        return False
    examples.append(dict(example))
    added[kind] += 1
    return True

# An original sentence must have a full Russian sentence, not a gloss of one word.
originals = []
for w in words:
    z, ru = w['zh'], w.get('ru', '')
    if (12 <= len(z) <= 100 and re.search(r'[。！？!?]$', z) and
        not re.search(r'\.\.|。。|…|：|:', z) and
        len(re.findall(r'[А-Яа-яЁё]+', ru)) >= 5 and
        len(ru) >= len(z) * 1.3 and re.match(r'[А-ЯЁ]', ru) and
        not re.search(r'перевод|иероглиф|графема|граммати|означает|выражение', ru, re.I)):
        src = next((s for s in w['sources'] if s.get('url')), None)
        if src:
            originals.append(dict(zh=z, py=w['py'], ru=ru,
                                  origin='Пример из исходных материалов', source=src,
                                  pyOrigin=w.get('pyOrigin', 'Из таблицы'),
                                  translationOrigin=w.get('translationOrigin', 'Из учебной базы')))

# Shorter sentences first; at most two source examples per term in this pass.
originals.sort(key=lambda e: len(e['zh']))
per_term = collections.Counter({w['zh']: sum(e.get('origin') == 'Пример из исходных материалов'
                               for e in w['examples']) for w in words})
for ex in originals:
    present = {ex['zh'][start:start+length] for length in range(2,9)
               for start in range(len(ex['zh'])-length+1)}
    for term in present & terms.keys():
        w = terms[term]
        if per_term[term] < 2 and len(w['examples']) < 3 and add(w, ex, 'original'):
            per_term[term] += 1

authored = []
for file in ['context-examples.tsv', 'idioms-life.tsv', 'site-equipment.tsv', 'work-phase-2.tsv', 'life-phase-2.tsv']:
    for line in (ROOT / 'examples' / file).read_text().splitlines():
        keys, zh, ru = line.split('\t')
        authored.append((keys.split('|'), dict(zh=zh, py=' '.join(lazy_pinyin(zh, style=Style.TONE)),
                       ru=ru, origin='Добавлен для практики', pyOrigin='Автоматически')))
by_zh = {w['zh']: w for w in words}
for keys, ex in authored:
    for key in keys:
        if key in by_zh:
            add(by_zh[key], ex, 'authored')
    # The same real sentence can also illustrate other words it actually contains.
    present = {ex['zh'][start:start+length] for length in range(2,9)
               for start in range(len(ex['zh'])-length+1)}
    for term in present & terms.keys():
        if len(terms[term]['examples']) < 2:
            add(terms[term], ex, 'authored')

translation_fixes = {
    '我们采用了新系统，以便提高效率。': 'Мы внедрили новую систему, чтобы повысить эффективность.',
    '我帮你留意一下。希望能尽快找到。': 'Я постараюсь это для тебя поискать. Надеюсь, удастся найти как можно скорее.',
    '广州地铁日均客流量已超过千万，位居世界前列，充分体现了这座城市的交通发达程度。':
        'Среднесуточный пассажиропоток метро Гуанчжоу превысил десять миллионов и находится среди крупнейших в мире, что наглядно показывает развитость городской транспортной системы.',
    '去不去还要看天气怎么样。': 'Поедем или нет — ещё зависит от погоды.',
    '同学们七点半就来教室了。': 'Ученики пришли в класс уже в половине восьмого.',
    '这 件 衣服 有点儿 贵。': 'Эта вещь немного дороговата.',
}
for w in words:
    for e in w['examples']:
        if e.get('origin') == 'Добавлен для практики':
            e['py'] = ' '.join(lazy_pinyin(e['zh'], style=Style.TONE))
        if e.get('origin') in ['Пример из исходных материалов', 'Из исходной таблицы']:
            corrected = translation_fixes.get(e['zh'], re.split(r'(?<=[.!?])\s+\(', e['ru'])[0])
            if corrected != e['ru']:
                e.setdefault('originalRussian', e['ru'])
                e['ru'] = corrected
                e['translationOrigin'] = 'Перевод отредактирован'
    if w['examples']:
        first = w['examples'][0]
        w.update(ex=first['zh'], ep=first['py'], er=first['ru'])
previous = db.get('exampleAudit', {})
db['examplesRevision'] = 2
db['exampleAudit'] = dict(previous,
    originalLinksAdded=previous.get('originalLinksAdded',0)+added['original'],
    authoredLinksAdded=previous.get('authoredLinksAdded',0)+added['authored'],
    authoredSentences=len(authored),
    withExamples=sum(bool(w['examples']) for w in words),
    withoutExamples=sum(not w['examples'] for w in words),
    status='Перенос и дополнение продолжаются')
path.write_text(json.dumps(db, ensure_ascii=False, separators=(',', ':')))
print(json.dumps(dict(added=added, audit=db['exampleAudit']), ensure_ascii=False))

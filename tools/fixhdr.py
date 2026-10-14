import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json,re,collections,sys
qs=json.load(open(W+'/all_en.json'))
chs=collections.defaultdict(set)
for q in qs: chs[q['book']].add(q['ch'].replace('\xa0',' '))
def alt(b): return "|".join(re.escape(c).replace(r"\ ",r"[\s\xa0]+") for c in sorted(chs[b],key=len,reverse=True))
HOW_UP="|".join(re.escape(c.upper()).replace(r"\ ",r"\s+") for c in sorted(chs['how'],key=len,reverse=True))
P={'how':[re.compile(r"\s*\b\d{1,3}\. \(cont\.\)"), re.compile(rf"\s*\b(?:{HOW_UP}): (?:Questions|Answers) \d+\b"), re.compile(rf"(?<=[.?!)\s])\s*\b\d{{1,3}} (?:{HOW_UP})\b(?=\s)")],
   'mcg':[re.compile(r"\s*\b\d{1,2}\. (?:[A-Z][A-Za-z]*|a|nd|in|el|ic|ar|der|s|[A-Za-z]{1,3})(?:[ \-](?:[A-Za-z]+))*? • \d{1,3}\b")],
   'sou':[re.compile(rf"\s*\bCHAPTER \d+ (?:{alt('sou')})\b",re.I)],
   'ess':[re.compile(rf"(?<=[.?!)\s])\s*\b\d{{1,2}} (?:{alt('ess')})\b(?=\s)")]}
n=collections.Counter(); ex=collections.defaultdict(list)
for q in qs:
    for pat in P.get(q['book'],[]):
        for k in ('q','expl'):
            for m in pat.finditer(q[k]):
                n[q['book']]+=1
                if len(ex[q['book']])<4: ex[q['book']].append(q[k][max(0,m.start()-40):m.end()+30])
            q[k]=q[k].replace('Heliot rope','Heliotrope')
            q[k]=re.sub(r"  +"," ",pat.sub(" ",q[k])).strip()
        q['opts']=[re.sub(r"  +"," ",pat.sub(" ",o)).strip() for o in q['opts']]
print(n); [print(b,e) for b in ex for e in ex[b]]
if sys.argv[1:]==['w']: json.dump(qs,open(W+'/all_en.json','w'),ensure_ascii=False)

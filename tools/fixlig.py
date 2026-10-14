import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json,re,collections,sys
qs=json.load(open(W+'/all_en.json'))
txt=lambda q:' '.join([q['q']]+q['opts']+[q['expl']])
vocab=collections.Counter(w.lower() for q in qs for w in re.findall(r"[A-Za-z]+",txt(q)))
R=re.compile(r"\b([A-Za-z]*?(?:ffi|ffl|fi|fl|ff))\s+([a-z]+)\b")
STOP={'and','of','the','in','is','to','a','or','with','for','on','at','by','as','syndrome','disease','an'}
dec=collections.Counter()
def fix(t):
    def f(m):
        a,b=m.group(1),m.group(2); w=(a+b).lower()
        if b in STOP and vocab[w]==0: return m.group(0)
        al=a.lower()
        if b in STOP: return m.group(0)
        if (al.endswith(('fi','fl')) and al not in('afifi',)) or (vocab[w]>0 and al not in('off','stiff','staff','cuff')):
            dec[(m.group(0),'M')]+=1; return a+b
        dec[(m.group(0),'K')]+=1; return m.group(0)
    return R.sub(f,t)
if __name__=='__main__':
    for q in qs: fix(txt(q))
    for (s,d),n in sorted(dec.items(),key=lambda x:-x[1]):
        if d=='K' or n<3: print(d,n,s)
    if sys.argv[1:]==['w']:
        for q in qs:
            q['q']=fix(q['q']); q['expl']=fix(q['expl']); q['opts']=[fix(o) for o in q['opts']]
        json.dump(qs,open(W+'/all_en.json','w'),ensure_ascii=False); print('ligature fix applied')

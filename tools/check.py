import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json,re,collections
d=json.load(open(W+'/all_en.json'))
def toks(s): return set(w for w in re.findall(r"[a-z][a-z0-9-]{3,}",s.lower()) if w not in {"which","following","with","that","this","from","most","likely","patient","have","their","these","there","been","will","does","into","than","more"})
res=collections.defaultdict(lambda:[0,0,0])
bad=[]
for q in d:
    e=toks(q["expl"]); sc=[len(toks(o)&e) for o in q["opts"]]
    k=(q["book"],q["ch"]); res[k][0]+=1
    if max(sc)==0: res[k][2]+=1; continue
    if sc[q["ans"]]==max(sc): res[k][1]+=1
    else: bad.append(q)
for k,(n,ok,z) in sorted(res.items()):
    r=ok/max(1,n-z)
    flag="  <<<" if r<0.55 else ""
    print(f"{k[0]:5s} {r:4.2f} n={n:4d} z={z:3d} {k[1][:45]}{flag}")

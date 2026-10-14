import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import pymupdf,glob,sys,re
names={"Essential":"ess","Mayo Clinic Neurology":"mayo","Neurology Board Review - Q":"mcg","Illustrated":"mow","Souayah":"sou","Howard":"how","Self-Assessment":"bra"}
def page_text(p):
    W=p.rect.width
    bl=[b for b in p.get_text("blocks") if b[6]==0 and b[4].strip()]
    # column assignment: blocks that span > 60% width are 'full'
    out=[]
    def col(b):
        if b[2]-b[0]>0.6*W: return 0
        return 1 if b[0]<W*0.48 else 2
    # keep full-width blocks in y order relative: simple approach: header/full first by y, then col1, col2
    fulls=sorted([b for b in bl if col(b)==0],key=lambda b:b[1])
    c1=sorted([b for b in bl if col(b)==1],key=lambda b:(b[1],b[0]))
    c2=sorted([b for b in bl if col(b)==2],key=lambda b:(b[1],b[0]))
    # merge fulls by y position: those above columns' first block come first
    seq=[]
    top=min([b[1] for b in c1+c2],default=1e9)
    seq=[b for b in fulls if b[1]<=top]+c1+c2+[b for b in fulls if b[1]>top]
    return "\n".join(b[4].strip() for b in seq)
for f in glob.glob("*.pdf"):
    k=[v for kk,v in names.items() if kk in f][0]
    if len(sys.argv)>1 and k not in sys.argv[1:]: continue
    d=pymupdf.open(f)
    with open(f"{W}/txt2/{k}.txt","w") as o:
        for i,p in enumerate(d):
            o.write(f"\n<<<PAGE {i+1}>>>\n"+page_text(p)+"\n")
    print(k)

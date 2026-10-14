import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json, textwrap
from PIL import Image, ImageDraw, ImageFont
qs=[q for q in json.load(open("all_en.json")) if q.get("imgs")]
qs.sort(key=lambda q:(q["book"],q["pdfpage"]))
F=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",15)
FB=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",16)
TW,TH=500,560
idx=[]
for s in range(0,len(qs),9):
    sh=Image.new("RGB",(TW*3,TH*3),"white"); d=ImageDraw.Draw(sh)
    for k,q in enumerate(qs[s:s+9]):
        x=(k%3)*TW; y=(k//3)*TH
        d.rectangle([x,y,x+TW-1,y+TH-1],outline="#999")
        num=s+k; idx.append((num,q["id"]))
        d.text((x+8,y+6),f"#{num} {q['id']} [{q.get('imgsrc')}]",fill="#c00",font=FB)
        lines=textwrap.wrap(q["q"],60)[:6]
        for i,l in enumerate(lines): d.text((x+8,y+28+i*18),l,fill="black",font=F)
        top=y+28+len(lines)*18+6; area=(TW-16, TH-(top-y)-8)
        ims=[Image.open("site/img/"+n).convert("RGB") for n in q["imgs"]]
        w=area[0]//len(ims)
        for j,im in enumerate(ims):
            im.thumbnail((w-6,area[1])); sh.paste(im,(x+8+j*w,top))
    sh.save(f"{W}/review/s{s//9:02d}.jpg",quality=70)
json.dump(idx,open(W+"/review/index.json","w"))
print(len(qs), (len(qs)+8)//9)

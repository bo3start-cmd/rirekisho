import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_JP  = os.path.join(BASE_DIR, "fonts", "DroidSansFallbackFull.ttf")
FONT_LAT = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")
_reg = False

def _ensure_fonts():
    global _reg
    if _reg: return
    pdfmetrics.registerFont(TTFont("JA",  FONT_JP))
    pdfmetrics.registerFont(TTFont("LAT", FONT_LAT))
    _reg = True

PH,PW_MM=297,210; TM,BM,LM,RM=15,12,15,15
UW=PW_MM-LM-RM; x0=LM; THIN=0.5
CG=colors.HexColor("#7a8fbb")

def _ascii(c): return ord(c)<128
def _fn(c): return "LAT" if _ascii(c) else "JA"
def mw(cv,t,sz): return sum(cv.stringWidth(c,_fn(c),sz) for c in str(t))

def dm(cv,xp,yp,t,sz):
    x=xp
    for c in str(t):
        f=_fn(c); cv.setFont(f,sz); cv.drawString(x,yp,c)
        x+=cv.stringWidth(c,f,sz)

def T(cv,x,y,s,sz=13,al="left"):
    cv.setFillColor(colors.black); s=str(s)
    if al=="center": w=mw(cv,s,sz)/mm; dm(cv,(x-w/2)*mm,y*mm,s,sz)
    elif al=="right": w=mw(cv,s,sz)/mm; dm(cv,(x-w)*mm,y*mm,s,sz)
    else: dm(cv,x*mm,y*mm,s,sz)

def sol(cv,lw=THIN): cv.setDash([]); cv.setLineWidth(lw); cv.setStrokeColor(CG)
def das(cv): cv.setDash(4,3); cv.setLineWidth(0.5); cv.setStrokeColor(CG)
def hl(cv,x1,y,x2,d=False):
    das(cv) if d else sol(cv)
    cv.line(x1*mm,y*mm,x2*mm,y*mm); sol(cv)
def vl(cv,x,y1,y2): sol(cv); cv.line(x*mm,y1*mm,x*mm,y2*mm)
def bx(cv,x,y,w,h,lw=THIN): sol(cv,lw); cv.rect(x*mm,y*mm,w*mm,h*mm,fill=0,stroke=1)

def wl(cv,t,mw_mm,sz):
    if not str(t).strip(): return [""]
    lines,cur=[],""
    for c in str(t):
        test=cur+c
        if mw(cv,test,sz)>(mw_mm-4)*mm: lines.append(cur) if cur else None; cur=c
        else: cur=test
    if cur: lines.append(cur)
    return lines or [""]

def dtc(cv,x,y,w,h,t,mx=24,mn=8,al="left"):
    if not t: return
    sh=max(mn,int(h*0.60*2.835)); st=min(mx,sh)
    for sz in range(st,mn-1,-1):
        if mw(cv,t,sz)<=(w-4)*mm:
            my=y+h/2-sz*0.127
            if al=="center": T(cv,x+w/2,my,t,sz,"center")
            elif al=="right": T(cv,x+w-2,my,t,sz,"right")
            else: T(cv,x+3,my,t,sz)
            return
    sz=mn; ls=wl(cv,t,w,sz); lh=sz*1.5/mm
    sy=y+h/2+(len(ls)-1)*lh/2-sz*0.127
    for i,ln in enumerate(ls):
        if al=="center": T(cv,x+w/2,sy-i*lh,ln,sz,"center")
        elif al=="right": T(cv,x+w-2,sy-i*lh,ln,sz,"right")
        else: T(cv,x+3,sy-i*lh,ln,sz)

def dtb(cv,x,yt,w,h,lines,sz=12):
    lh=sz*1.55/mm; cy=yt-4
    for ln in lines:
        if cy-lh<yt-h+2: break
        if not ln: cy-=lh*0.5; continue
        for wln in wl(cv,ln,w,sz):
            if cy-lh<yt-h+2: break
            T(cv,x+3,cy-sz*0.127,wln,sz); cy-=lh

CY=20;CM=15;CE=UW-CY-CM

def dth(cv,x,y,lb="学歴・職歴"):
    RH=12; bx(cv,x,y-RH,CY,RH); bx(cv,x+CY,y-RH,CM,RH); bx(cv,x+CY+CM,y-RH,CE,RH)
    dtc(cv,x,y-RH,CY,RH,"年",al="center"); dtc(cv,x+CY,y-RH,CM,RH,"月",al="center")
    dtc(cv,x+CY+CM,y-RH,CE,RH,lb,al="center"); return y-RH

def dtr(cv,x,y,rh,yr="",mo="",ev="",sec=False,end=False):
    bx(cv,x,y-rh,CY,rh); sol(cv,THIN)
    cv.rect((x+CY)*mm,(y-rh)*mm,CM*mm,rh*mm,fill=0,stroke=1)
    bx(cv,x+CY+CM,y-rh,CE,rh)
    dtc(cv,x,y-rh,CY,rh,yr,al="center"); dtc(cv,x+CY,y-rh,CM,rh,mo,al="center")
    if sec: dtc(cv,x+CY+CM,y-rh,CE,rh,ev,al="center")
    elif end: dtc(cv,x+CY+CM,y-rh,CE,rh,ev,al="right")
    else: dtc(cv,x+CY+CM,y-rh,CE,rh,ev)
    return y-rh

def _bej(d):
    rows=[("","","学歴",True,False)]
    sn=d.get("school_name",""); sy=d.get("school_grad_year",""); sm=d.get("school_grad_month","")
    if sn:
        ey=str(int(sy)-3) if sy else ""
        rows+= [(ey,"4",f"{sn}　入学",False,False),(sy,sm,"同校　卒業",False,False)]
    cn=d.get("college_name",""); cy2=d.get("college_grad_year",""); cm2=d.get("college_grad_month","")
    if cn:
        ey2=str(int(cy2)-2) if cy2 else ""
        rows+=[(ey2,"4",f"{cn}　入学",False,False),(cy2,cm2,"同校　卒業",False,False)]
    rows+=[("","","",False,False),("","","職歴",True,False)]
    for j in d.get("jobs",[]):
        rows.append((j.get("start_year",""),j.get("start_month",""),
                     f'{j.get("company","")}　入社（{j.get("type","")}）',False,False))
        ey=j.get("end_year",""); em=j.get("end_month","")
        rows.append((ey,em,"同社　退社",False,False) if ey else ("","","現在に至る",False,False))
    return rows

def _p1(cv,d):
    T(cv,x0,297-TM-3,"履　歴　書",20); T(cv,x0+UW,297-TM-3,d.get("created_date",""),11,"right")
    PW_=28;PH_=36;PX=x0+UW-PW_;PT=297-TM-8
    ph=d.get("photo_path","")
    if ph and os.path.exists(ph):
        try:
            ir=ImageReader(ph); iw,ih=ir.getSize(); sc=min(PW_*mm/iw,PH_*mm/ih)
            dw,dh=iw*sc,ih*sc; ix=PX*mm+(PW_*mm-dw)/2; iy=(PT-PH_)*mm+(PH_*mm-dh)/2
            cv.drawImage(ph,ix,iy,width=dw,height=dh,preserveAspectRatio=True,mask='auto')
            bx(cv,PX,PT-PH_,PW_,PH_,THIN)
        except: _ph_box(cv,PX,PT,PW_,PH_)
    else: _ph_box(cv,PX,PT,PW_,PH_)
    IW=UW-PW_;LW=16;y=PT
    RH1=9;y-=RH1
    T(cv,x0+1,y+2,"ふりがな",8); dtc(cv,x0+LW,y,IW-LW,RH1,d.get("kana",""))
    hl(cv,x0,y,x0+IW,d=True); vl(cv,x0,y,y+RH1)
    RH2=16;y-=RH2
    T(cv,x0+1,y+4,"名前",9); dtc(cv,x0+LW,y,IW-LW,RH2,d.get("name",""),mx=20)
    hl(cv,x0,y,x0+IW); vl(cv,x0,y,y+RH2)
    RH3=11;y-=RH3
    T(cv,x0+3,y+3,f'{d.get("birth_date","")}生（満 {d.get("age","")} 歳）',14)
    GX=x0+IW-30;GY=y+RH3/2; cv.setFont("LAT",13); cv.setFillColor(colors.black)
    gn=d.get("gender","男"); cv.drawString(GX*mm,(GY-4.5)*mm,gn)
    cw=cv.stringWidth(gn,"JA",13)/mm; cx=GX+cw/2; cy_=GY-1.5
    if gn=="男":
        cv.setStrokeColor(colors.black); cv.setLineWidth(0.8)
        cv.ellipse((cx-4)*mm,(cy_-4)*mm,(cx+4)*mm,(cy_+4.5)*mm,fill=0,stroke=1); cv.setLineWidth(0.5)
    T(cv,GX+cw+1,GY-4.5,"・女" if gn=="男" else "・男",13)
    hl(cv,x0,y,x0+UW); vl(cv,x0,y,y+RH3)
    IL=115;IR=UW-IL
    RH4=8;y-=RH4
    dtc(cv,x0,y,LW,RH4,"ふりがな",mx=8); dtc(cv,x0+LW,y,IL-LW,RH4,d.get("address_kana",""))
    dtc(cv,x0+IL,y,IR,RH4,f'電話　{d.get("tel","")}')
    hl(cv,x0,y,x0+UW,d=True)
    vl(cv,x0,y,y+RH4); vl(cv,x0+IL,y,y+RH4); vl(cv,x0+UW,y,y+RH4)
    RH5=20;y-=RH5
    dtc(cv,x0,y,LW,RH5,"現住所",mx=11)
    T(cv,x0+LW+2,y+RH5-6,d.get("zip_code",""),13)
    addr=d.get("address",""); aw=IL-LW
    for sz in range(13,7,-1):
        if mw(cv,addr,sz)<=(aw-3)*mm: T(cv,x0+LW+2,y+4,addr,sz); break
    T(cv,x0+IL+2,y+RH5-6,"Email",12); T(cv,x0+IL+2,y+4,d.get("email",""),10)
    hl(cv,x0,y,x0+UW); vl(cv,x0,y,y+RH5); vl(cv,x0+IL,y,y+RH5); vl(cv,x0+UW,y,y+RH5)
    RH6=8;y-=RH6
    dtc(cv,x0,y,LW,RH6,"ふりがな",mx=8); dtc(cv,x0+IL,y,IR,RH6,"電話")
    hl(cv,x0,y,x0+UW,d=True); vl(cv,x0,y,y+RH6); vl(cv,x0+IL,y,y+RH6); vl(cv,x0+UW,y,y+RH6)
    RH7=16;y-=RH7
    dtc(cv,x0,y,LW,RH7,"連絡先",mx=11)
    dtc(cv,x0+LW,y,IL-LW,RH7,"〒　（現住所以外に連絡を希望する場合のみ入力）",mx=10)
    dtc(cv,x0+IL,y,IR,RH7,"Email",mx=12)
    hl(cv,x0,y,x0+UW); vl(cv,x0,y,y+RH7); vl(cv,x0+IL,y,y+RH7); vl(cv,x0+UW,y,y+RH7)
    hl(cv,x0,PT,x0+UW)
    GAP=5;ty=y-GAP;avail=ty-BM-12; rows=_bej(d); N=15; RH=avail/N
    ty=dth(cv,x0,ty)
    for i in range(N):
        r=rows[i] if i<len(rows) else ("","","",False,False)
        ty=dtr(cv,x0,ty,RH,*r)

def _ph_box(cv,PX,PT,PW_,PH_):
    bx(cv,PX,PT-PH_,PW_,PH_,THIN)
    T(cv,PX+PW_/2,PT-PH_/2+3,"写真貼付欄",8,"center")
    T(cv,PX+PW_/2,PT-PH_/2-2,"縦4cm×横3cm",7,"center")

def _p2(cv,d):
    BS=12;BH=8;HH=12;GS=3*3
    pl=[l for l in d.get("pr_text","").split("\n")][:12]
    wl2=[l for l in d.get("wish_text","").split("\n")][:6]
    def ch(lines,sz):
        lh=sz*1.55/mm; tot=BH+4
        for l in lines: tot+=lh*0.5 if not l else lh
        return tot+4
    PH=max(ch(pl,BS),55); WH=max(ch(wl2,BS),35)
    avt=(297-TM-BM)-(PH+WH+HH*2+GS); NE=max(3,int(avt/(11.5*2))); RH2=avt/(NE*2)
    y=297-TM; y=dth(cv,x0,y)
    for i in range(NE): y=dtr(cv,x0,y,RH2)
    y-=3
    lr=[(l.get("year",""),l.get("month",""),l.get("name",""),False,False) for l in d.get("licenses",[])]
    lr.append(("","","以上",False,True))
    y=dth(cv,x0,y,lb="免許・資格")
    for i in range(NE):
        r=lr[i] if i<len(lr) else ("","","",False,False)
        y=dtr(cv,x0,y,RH2,*r)
    y-=3
    bx(cv,x0,y-PH,UW,PH,THIN); T(cv,x0+2,y-BH+1,"志望動機・特技・アピールポイントなど",9)
    hl(cv,x0,y-BH,x0+UW); dtb(cv,x0,y-BH,UW,PH-BH,pl,BS); y-=PH+3
    bx(cv,x0,y-WH,UW,WH,THIN)
    T(cv,x0+2,y-BH+1,"本人希望欄（特に給料・職種・勤務時間・勤務地・その他について希望があれば記入）",9)
    hl(cv,x0,y-BH,x0+UW); dtb(cv,x0,y-BH,UW,WH-BH,wl2,BS)

def generate_resume(data,out_path):
    _ensure_fonts()
    cv=canvas.Canvas(out_path,pagesize=A4)
    _p1(cv,data); cv.showPage(); _p2(cv,data); cv.save()

"""履歴書PDF生成モジュール"""
import os, math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# ── フォント設定 ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_JP_PATH  = os.path.join(BASE_DIR, "fonts", "DroidSansFallbackFull.ttf")
FONT_LAT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")

_fonts_registered = False

def _ensure_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    if not os.path.exists(FONT_JP_PATH) or not os.path.exists(FONT_LAT_PATH):
        raise RuntimeError(
            "フォントが見つかりません。fonts/ フォルダに "
            "DroidSansFallbackFull.ttf と DejaVuSans.ttf を配置してください。"
        )
    pdfmetrics.registerFont(TTFont("JA",  FONT_JP_PATH))
    pdfmetrics.registerFont(TTFont("LAT", FONT_LAT_PATH))
    _fonts_registered = True

# ── レイアウト定数 ────────────────────────────────────────────────
PH, PW_MM = 297, 210
TM, BM, LM, RM = 15, 12, 15, 15
UW = PW_MM - LM - RM
x0 = LM
THIN = 0.5
C_GRID = colors.HexColor("#7a8fbb")

def _is_ascii(ch): return ord(ch) < 128
def _font_for(ch): return "LAT" if _is_ascii(ch) else "JA"

def mixed_width(cv, text, sz):
    return sum(cv.stringWidth(ch, _font_for(ch), sz) for ch in str(text))

def draw_mixed(cv, x_pt, y_pt, text, sz):
    x = x_pt
    for ch in str(text):
        f = _font_for(ch)
        cv.setFont(f, sz)
        cv.drawString(x, y_pt, ch)
        x += cv.stringWidth(ch, f, sz)

def T(cv, x, y, s, sz=13, al="left"):
    cv.setFillColor(colors.black)
    s = str(s)
    if al == "center":
        w = mixed_width(cv, s, sz) / mm
        draw_mixed(cv, (x - w/2)*mm, y*mm, s, sz)
    elif al == "right":
        w = mixed_width(cv, s, sz) / mm
        draw_mixed(cv, (x - w)*mm, y*mm, s, sz)
    else:
        draw_mixed(cv, x*mm, y*mm, s, sz)

def solid(cv, lw=THIN): cv.setDash([]); cv.setLineWidth(lw); cv.setStrokeColor(C_GRID)
def dashed(cv): cv.setDash(4,3); cv.setLineWidth(0.5); cv.setStrokeColor(C_GRID)
def hline(cv, x1, y, x2, dash=False):
    if dash: dashed(cv)
    else: solid(cv)
    cv.line(x1*mm, y*mm, x2*mm, y*mm); solid(cv)
def vline(cv, x, y1, y2): solid(cv); cv.line(x*mm, y1*mm, x*mm, y2*mm)
def box(cv, x, y, w, h, lw=THIN): solid(cv, lw); cv.rect(x*mm, y*mm, w*mm, h*mm, fill=0, stroke=1)

def wrap_lines(cv, text, max_w_mm, sz):
    if not str(text).strip(): return [""]
    lines, cur = [], ""
    for ch in str(text):
        test = cur + ch
        if mixed_width(cv, test, sz) > (max_w_mm - 4)*mm:
            if cur: lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur: lines.append(cur)
    return lines or [""]

def draw_text_in_cell(cv, x, y, w, h, text, max_sz=24, min_sz=8, align="left"):
    if not text: return
    PAD = 4
    sz_from_h = max(min_sz, int(h * 0.60 * 2.835))
    start_sz  = min(max_sz, sz_from_h)
    for sz in range(start_sz, min_sz-1, -1):
        if mixed_width(cv, text, sz) <= (w-PAD)*mm:
            mid_y = y + h/2 - sz*0.127
            if align=="center": T(cv, x+w/2, mid_y, text, sz, "center")
            elif align=="right": T(cv, x+w-2, mid_y, text, sz, "right")
            else: T(cv, x+3, mid_y, text, sz)
            return
    sz = min_sz
    lines = wrap_lines(cv, text, w, sz)
    lh = sz*1.5/mm
    start_y = y+h/2+(len(lines)-1)*lh/2-sz*0.127
    for i,ln in enumerate(lines):
        if align=="center": T(cv, x+w/2, start_y-i*lh, ln, sz, "center")
        elif align=="right": T(cv, x+w-2, start_y-i*lh, ln, sz, "right")
        else: T(cv, x+3, start_y-i*lh, ln, sz)

def draw_text_block(cv, x, y_top, w, h, lines, sz=12):
    lh = sz*1.55/mm
    cur_y = y_top - 4
    for line in lines:
        if cur_y - lh < y_top - h + 2: break
        if line == "": cur_y -= lh*0.5; continue
        for wl in wrap_lines(cv, line, w, sz):
            if cur_y - lh < y_top - h + 2: break
            T(cv, x+3, cur_y-sz*0.127, wl, sz)
            cur_y -= lh

CY=20; CM=15; CE=UW-CY-CM

def draw_table_header(cv, x, y, label="学歴・職歴"):
    RH=12; box(cv,x,y-RH,CY,RH); box(cv,x+CY,y-RH,CM,RH); box(cv,x+CY+CM,y-RH,CE,RH)
    draw_text_in_cell(cv,x,y-RH,CY,RH,"年",align="center")
    draw_text_in_cell(cv,x+CY,y-RH,CM,RH,"月",align="center")
    draw_text_in_cell(cv,x+CY+CM,y-RH,CE,RH,label,align="center")
    return y-RH

def draw_table_row(cv, x, y, rh, yr="", mo="", ev="", section=False, end=False):
    box(cv,x,y-rh,CY,rh); solid(cv,THIN)
    cv.rect((x+CY)*mm,(y-rh)*mm,CM*mm,rh*mm,fill=0,stroke=1)
    box(cv,x+CY+CM,y-rh,CE,rh)
    draw_text_in_cell(cv,x,y-rh,CY,rh,yr,align="center")
    draw_text_in_cell(cv,x+CY,y-rh,CM,rh,mo,align="center")
    if section:   draw_text_in_cell(cv,x+CY+CM,y-rh,CE,rh,ev,align="center")
    elif end:     draw_text_in_cell(cv,x+CY+CM,y-rh,CE,rh,ev,align="right")
    else:         draw_text_in_cell(cv,x+CY+CM,y-rh,CE,rh,ev)
    return y-rh

# ════════════════════════════════════════════════════════════════
def generate_resume(data: dict, out_path: str):
    """
    data キー:
      name, kana, birth_date, age, gender, zip_code, address,
      address_kana, tel, email,
      school_name, school_grad_year, school_grad_month,
      college_name, college_grad_year, college_grad_month,
      jobs: list of {company, type, start_year, start_month,
                     end_year, end_month, position}
      licenses: list of {year, month, name}
      pr_text, wish_text, photo_path (optional)
      created_date
    """
    _ensure_fonts()
    cv = canvas.Canvas(out_path, pagesize=A4)

    # ── PAGE 1 ──────────────────────────────────────────────────
    _draw_page1(cv, data)
    cv.showPage()
    _draw_page2(cv, data)
    cv.save()

def _draw_page1(cv, d):
    T(cv, x0, 297-TM-3, "履　歴　書", 20)
    T(cv, x0+UW, 297-TM-3, d.get("created_date",""), 11, "right")

    PW_=28; PH_=36; PX=x0+UW-PW_; PERS_TOP=297-TM-8

    # 写真
    photo = d.get("photo_path","")
    if photo and os.path.exists(photo):
        try:
            ir = ImageReader(photo)
            iw,ih = ir.getSize()
            scale = min(PW_*mm/iw, PH_*mm/ih)
            dw,dh = iw*scale, ih*scale
            ix = PX*mm+(PW_*mm-dw)/2
            iy = (PERS_TOP-PH_)*mm+(PH_*mm-dh)/2
            cv.drawImage(photo, ix, iy, width=dw, height=dh,
                         preserveAspectRatio=True, mask='auto')
            box(cv, PX, PERS_TOP-PH_, PW_, PH_, THIN)
        except:
            _draw_photo_placeholder(cv, PX, PERS_TOP, PW_, PH_)
    else:
        _draw_photo_placeholder(cv, PX, PERS_TOP, PW_, PH_)

    IW=UW-PW_; LW=16; y=PERS_TOP

    # ふりがな
    RH1=9; y-=RH1
    T(cv,x0+1,y+2,"ふりがな",8)
    draw_text_in_cell(cv,x0+LW,y,IW-LW,RH1,d.get("kana",""))
    hline(cv,x0,y,x0+IW,dash=True); vline(cv,x0,y,y+RH1)

    # 名前
    RH2=16; y-=RH2
    T(cv,x0+1,y+4,"名前",9)
    draw_text_in_cell(cv,x0+LW,y,IW-LW,RH2,d.get("name",""),max_sz=20)
    hline(cv,x0,y,x0+IW); vline(cv,x0,y,y+RH2)

    # 生年月日・性別
    RH3=11; y-=RH3
    birth=d.get("birth_date",""); age=d.get("age",""); gender=d.get("gender","男")
    T(cv,x0+3,y+3,f"{birth}生（満 {age} 歳）",14)
    GENDER_X=x0+IW-30; GENDER_Y=y+RH3/2
    cv.setFont("LAT",13); cv.setFillColor(colors.black)
    cv.drawString(GENDER_X*mm,(GENDER_Y-4.5)*mm,"男" if gender=="男" else "女")
    char_w=cv.stringWidth("男","JA",13)/mm
    cx=GENDER_X+char_w/2; cy_=GENDER_Y-1.5
    if gender=="男":
        cv.setStrokeColor(colors.black); cv.setLineWidth(0.8)
        cv.ellipse((cx-4)*mm,(cy_-4)*mm,(cx+4)*mm,(cy_+4.5)*mm,fill=0,stroke=1)
        cv.setLineWidth(0.5)
    T(cv,GENDER_X+char_w+1,GENDER_Y-4.5,"・女" if gender=="男" else "・男",13)
    hline(cv,x0,y,x0+UW); vline(cv,x0,y,y+RH3)

    # 住所ゾーン
    IW_L=115; IW_R=UW-IW_L

    RH4=8; y-=RH4
    draw_text_in_cell(cv,x0,y,LW,RH4,"ふりがな",max_sz=8)
    draw_text_in_cell(cv,x0+LW,y,IW_L-LW,RH4,d.get("address_kana",""))
    draw_text_in_cell(cv,x0+IW_L,y,IW_R,RH4,f'電話　{d.get("tel","")}')
    hline(cv,x0,y,x0+UW,dash=True)
    vline(cv,x0,y,y+RH4); vline(cv,x0+IW_L,y,y+RH4); vline(cv,x0+UW,y,y+RH4)

    RH5=20; y-=RH5
    draw_text_in_cell(cv,x0,y,LW,RH5,"現住所",max_sz=11)
    addr_w=IW_L-LW
    T(cv,x0+LW+2,y+RH5-6,d.get("zip_code",""),13)
    addr=d.get("address","")
    for sz in range(13,7,-1):
        if mixed_width(cv,addr,sz)<=(addr_w-3)*mm:
            T(cv,x0+LW+2,y+4,addr,sz); break
    T(cv,x0+IW_L+2,y+RH5-6,"Email",12)
    T(cv,x0+IW_L+2,y+4,d.get("email",""),10)
    hline(cv,x0,y,x0+UW)
    vline(cv,x0,y,y+RH5); vline(cv,x0+IW_L,y,y+RH5); vline(cv,x0+UW,y,y+RH5)

    RH6=8; y-=RH6
    draw_text_in_cell(cv,x0,y,LW,RH6,"ふりがな",max_sz=8)
    draw_text_in_cell(cv,x0+IW_L,y,IW_R,RH6,"電話")
    hline(cv,x0,y,x0+UW,dash=True)
    vline(cv,x0,y,y+RH6); vline(cv,x0+IW_L,y,y+RH6); vline(cv,x0+UW,y,y+RH6)

    RH7=16; y-=RH7
    draw_text_in_cell(cv,x0,y,LW,RH7,"連絡先",max_sz=11)
    draw_text_in_cell(cv,x0+LW,y,IW_L-LW,RH7,"〒　（現住所以外に連絡を希望する場合のみ入力）",max_sz=10)
    draw_text_in_cell(cv,x0+IW_L,y,IW_R,RH7,"Email",max_sz=12)
    hline(cv,x0,y,x0+UW)
    vline(cv,x0,y,y+RH7); vline(cv,x0+IW_L,y,y+RH7); vline(cv,x0+UW,y,y+RH7)
    hline(cv,x0,PERS_TOP,x0+UW)

    # 学歴・職歴テーブル
    GAP=5; ty=y-GAP; HDR_H=12; avail=ty-BM-HDR_H
    rows = _build_edu_job_rows(d)
    N=15; RH=avail/N
    ty=draw_table_header(cv,x0,ty)
    for i in range(N):
        if i<len(rows): yr,mo,ev,sec,end=rows[i]
        else: yr,mo,ev,sec,end="","","",False,False
        ty=draw_table_row(cv,x0,ty,RH,yr,mo,ev,sec,end)

def _draw_photo_placeholder(cv, PX, PERS_TOP, PW_, PH_):
    box(cv,PX,PERS_TOP-PH_,PW_,PH_,THIN)
    T(cv,PX+PW_/2,PERS_TOP-PH_/2+3,"写真貼付欄",8,"center")
    T(cv,PX+PW_/2,PERS_TOP-PH_/2-2,"縦4cm×横3cm",7,"center")

def _build_edu_job_rows(d):
    rows=[]
    rows.append(("","","学歴",True,False))
    sn=d.get("school_name",""); sy=d.get("school_grad_year",""); sm=d.get("school_grad_month","")
    if sn:
        enter_y=str(int(sy)-3) if sy else ""; rows.append((enter_y,"4",f"{sn}　入学",False,False))
        rows.append((sy,sm,f"同校　卒業",False,False))
    cn=d.get("college_name",""); cy2=d.get("college_grad_year",""); cm2=d.get("college_grad_month","")
    if cn:
        enter_y2=str(int(cy2)-2) if cy2 else ""; rows.append((enter_y2,"4",f"{cn}　入学",False,False))
        rows.append((cy2,cm2,"同校　卒業",False,False))
    rows.append(("","","",False,False))
    rows.append(("","","職歴",True,False))
    for j in d.get("jobs",[]):
        rows.append((j.get("start_year",""),j.get("start_month",""),
                     f'{j.get("company","")}　入社（{j.get("type","")}）',False,False))
        ey=j.get("end_year",""); em=j.get("end_month","")
        if ey: rows.append((ey,em,"同社　退社",False,False))
        else:  rows.append(("","","現在に至る",False,False))
    return rows

def _draw_page2(cv, d):
    BOX_SZ=12; BOX_HDR=8; HDR_H=12; GAPS=3*3
    pr_lines=[l for l in d.get("pr_text","").split("\n") if l or True][:12]
    wish_lines=[l for l in d.get("wish_text","").split("\n") if l or True][:6]

    def calc_h(lines,sz):
        lh=sz*1.55/mm; total=BOX_HDR+4
        for l in lines: total+=lh*0.5 if not l else lh
        return total+4

    PR_H=max(calc_h(pr_lines,BOX_SZ),55)
    WISH_H=max(calc_h(wish_lines,BOX_SZ),35)
    TARGET_RH=11.5
    avail_tables=(297-TM-BM)-(PR_H+WISH_H+HDR_H*2+GAPS)
    N_each=max(3,int(avail_tables/(TARGET_RH*2)))
    RH2=avail_tables/(N_each*2)

    y=297-TM
    y=draw_table_header(cv,x0,y)
    for i in range(N_each): y=draw_table_row(cv,x0,y,RH2)
    y-=3

    lic_rows=[]
    for lic in d.get("licenses",[]):
        lic_rows.append((lic.get("year",""),lic.get("month",""),lic.get("name",""),False,False))
    lic_rows.append(("","","以上",False,True))

    y=draw_table_header(cv,x0,y,label="免許・資格")
    for i in range(N_each):
        if i<len(lic_rows): yr,mo,ev,sec,end=lic_rows[i]
        else: yr,mo,ev,sec,end="","","",False,False
        y=draw_table_row(cv,x0,y,RH2,yr,mo,ev,sec,end)
    y-=3

    box(cv,x0,y-PR_H,UW,PR_H,THIN)
    T(cv,x0+2,y-BOX_HDR+1,"志望動機・特技・アピールポイントなど",9)
    hline(cv,x0,y-BOX_HDR,x0+UW)
    draw_text_block(cv,x0,y-BOX_HDR,UW,PR_H-BOX_HDR,pr_lines,BOX_SZ)
    y-=PR_H+3

    box(cv,x0,y-WISH_H,UW,WISH_H,THIN)
    T(cv,x0+2,y-BOX_HDR+1,"本人希望欄（特に給料・職種・勤務時間・勤務地・その他について希望があれば記入）",9)
    hline(cv,x0,y-BOX_HDR,x0+UW)
    draw_text_block(cv,x0,y-BOX_HDR,UW,WISH_H-BOX_HDR,wish_lines,BOX_SZ)

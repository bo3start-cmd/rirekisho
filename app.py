import os,uuid,datetime,json
from flask import Flask,render_template,request,redirect,url_for,session,send_file,abort,flash
from werkzeug.utils import secure_filename
from pdf_generator import generate_resume

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","change-me-in-production")
ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD","admin1234")
PDF_DIR=os.path.join(os.path.dirname(__file__),"pdfs")
UPLOAD_DIR=os.path.join(os.path.dirname(__file__),"uploads")
os.makedirs(PDF_DIR,exist_ok=True); os.makedirs(UPLOAD_DIR,exist_ok=True)
DB_FILE=os.path.join(os.path.dirname(__file__),"resumes.jsonl")

def db_append(r):
    with open(DB_FILE,"a",encoding="utf-8") as f: f.write(json.dumps(r,ensure_ascii=False)+"\n")

def db_all():
    if not os.path.exists(DB_FILE): return []
    rows=[]
    with open(DB_FILE,encoding="utf-8") as f:
        for line in f:
            try: rows.append(json.loads(line.strip()))
            except: pass
    return rows

def db_search(q):
    q=q.strip().lower()
    return [r for r in db_all() if q in r.get("name","").lower()]

@app.route("/",methods=["GET"])
def index(): return render_template("form.html")

@app.route("/submit",methods=["POST"])
def submit():
    f=request.form
    photo_path=""
    pf=request.files.get("photo")
    if pf and pf.filename:
        ext=os.path.splitext(secure_filename(pf.filename))[1]
        fn=f"{uuid.uuid4().hex}{ext}"; photo_path=os.path.join(UPLOAD_DIR,fn); pf.save(photo_path)
    jobs=[]
    for i in range(1,6):
        c=f.get(f"company_{i}","").strip()
        if not c: continue
        jobs.append({"company":c,"type":f.get(f"job_type_{i}",""),"start_year":f.get(f"start_year_{i}",""),
                     "start_month":f.get(f"start_month_{i}",""),"end_year":f.get(f"end_year_{i}",""),
                     "end_month":f.get(f"end_month_{i}",""),"position":f.get(f"position_{i}","")})
    licenses=[]
    for i in range(1,7):
        ln=f.get(f"lic_name_{i}","").strip()
        if not ln: continue
        licenses.append({"year":f.get(f"lic_year_{i}",""),"month":f.get(f"lic_month_{i}",""),"name":ln})
    created=datetime.date.today().strftime("%Y年 %m月 %d日 現在")
    data={"name":f.get("name",""),"kana":f.get("kana",""),"birth_date":f.get("birth_date",""),
          "age":f.get("age",""),"gender":f.get("gender","男"),"zip_code":f.get("zip_code",""),
          "address":f.get("address",""),"address_kana":f.get("address_kana",""),
          "tel":f.get("tel",""),"email":f.get("email",""),"school_name":f.get("school_name",""),
          "school_grad_year":f.get("school_grad_year",""),"school_grad_month":f.get("school_grad_month",""),
          "college_name":f.get("college_name",""),"college_grad_year":f.get("college_grad_year",""),
          "college_grad_month":f.get("college_grad_month",""),"jobs":jobs,"licenses":licenses,
          "pr_text":f.get("pr_text",""),"wish_text":f.get("wish_text",""),
          "photo_path":photo_path,"created_date":created}
    pid=uuid.uuid4().hex; pname=f'{data["name"]}_{pid[:8]}.pdf'; ppath=os.path.join(PDF_DIR,pname)
    try: generate_resume(data,ppath)
    except Exception as e: flash(f"PDF生成エラー: {e}"); return redirect(url_for("index"))
    db_append({"id":pid,"name":data["name"],"kana":data["kana"],"email":data["email"],
               "pdf_file":pname,"created":datetime.datetime.now().isoformat()})
    return render_template("success.html",name=data["name"],pdf_id=pid)

@app.route("/download/<pid>")
def download_public(pid):
    for r in db_all():
        if r["id"]==pid:
            p=os.path.join(PDF_DIR,r["pdf_file"])
            if os.path.exists(p): return send_file(p,as_attachment=True,download_name=f'履歴書_{r["name"]}.pdf')
    abort(404)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def dec(*a,**k):
        if not session.get("admin"): return redirect(url_for("admin_login"))
        return fn(*a,**k)
    return dec

@app.route("/admin",methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD: session["admin"]=True; return redirect(url_for("admin_dashboard"))
        flash("パスワードが違います")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout(): session.pop("admin",None); return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    q=request.args.get("q","").strip()
    recs=db_search(q) if q else db_all()
    recs=sorted(recs,key=lambda r:r.get("created",""),reverse=True)
    return render_template("admin_dashboard.html",records=recs,query=q)

@app.route("/admin/download/<pid>")
@admin_required
def admin_download(pid):
    for r in db_all():
        if r["id"]==pid:
            p=os.path.join(PDF_DIR,r["pdf_file"])
            if os.path.exists(p): return send_file(p,as_attachment=True,download_name=f'履歴書_{r["name"]}.pdf')
    abort(404)

if __name__=="__main__": app.run(debug=True,port=5000)

"""履歴書自動生成Webアプリ — Flask"""
import os, uuid, datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, session, send_file, abort, flash)
from werkzeug.utils import secure_filename
from pdf_generator import generate_resume

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin1234")
PDF_DIR    = os.path.join(os.path.dirname(__file__), "pdfs")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(PDF_DIR,    exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── 簡易DB（JSON行形式） ──────────────────────────────────────────
import json
DB_FILE = os.path.join(os.path.dirname(__file__), "resumes.jsonl")

def db_append(record: dict):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def db_all() -> list[dict]:
    if not os.path.exists(DB_FILE): return []
    records = []
    with open(DB_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: records.append(json.loads(line))
                except: pass
    return records

def db_search(query: str) -> list[dict]:
    q = query.strip().lower()
    return [r for r in db_all() if q in r.get("name","").lower()]

# ════════════════════════════════════════════════════════════════
#  候補者ルート
# ════════════════════════════════════════════════════════════════
@app.route("/", methods=["GET"])
def index():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    f = request.form

    # 写真アップロード
    photo_path = ""
    photo_file = request.files.get("photo")
    if photo_file and photo_file.filename:
        ext = os.path.splitext(secure_filename(photo_file.filename))[1]
        fname = f"{uuid.uuid4().hex}{ext}"
        photo_path = os.path.join(UPLOAD_DIR, fname)
        photo_file.save(photo_path)

    # 職歴リスト
    jobs = []
    for i in range(1, 6):
        company = f.get(f"company_{i}", "").strip()
        if not company: continue
        jobs.append({
            "company":     company,
            "type":        f.get(f"job_type_{i}", ""),
            "start_year":  f.get(f"start_year_{i}", ""),
            "start_month": f.get(f"start_month_{i}", ""),
            "end_year":    f.get(f"end_year_{i}", ""),
            "end_month":   f.get(f"end_month_{i}", ""),
            "position":    f.get(f"position_{i}", ""),
        })

    # 免許リスト
    licenses = []
    for i in range(1, 7):
        lic_name = f.get(f"lic_name_{i}", "").strip()
        if not lic_name: continue
        licenses.append({
            "year":  f.get(f"lic_year_{i}", ""),
            "month": f.get(f"lic_month_{i}", ""),
            "name":  lic_name,
        })

    created = datetime.date.today().strftime("%Y年 %m月 %d日 現在")
    data = {
        "name":               f.get("name",""),
        "kana":               f.get("kana",""),
        "birth_date":         f.get("birth_date",""),
        "age":                f.get("age",""),
        "gender":             f.get("gender","男"),
        "zip_code":           f.get("zip_code",""),
        "address":            f.get("address",""),
        "address_kana":       f.get("address_kana",""),
        "tel":                f.get("tel",""),
        "email":              f.get("email",""),
        "school_name":        f.get("school_name",""),
        "school_grad_year":   f.get("school_grad_year",""),
        "school_grad_month":  f.get("school_grad_month",""),
        "college_name":       f.get("college_name",""),
        "college_grad_year":  f.get("college_grad_year",""),
        "college_grad_month": f.get("college_grad_month",""),
        "jobs":               jobs,
        "licenses":           licenses,
        "pr_text":            f.get("pr_text",""),
        "wish_text":          f.get("wish_text",""),
        "photo_path":         photo_path,
        "created_date":       created,
    }

    # PDF生成
    pdf_id   = uuid.uuid4().hex
    pdf_name = f'{data["name"]}_{pdf_id[:8]}.pdf'
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    try:
        generate_resume(data, pdf_path)
    except Exception as e:
        flash(f"PDF生成エラー: {e}")
        return redirect(url_for("index"))

    # DB保存
    record = {
        "id":       pdf_id,
        "name":     data["name"],
        "kana":     data["kana"],
        "email":    data["email"],
        "pdf_file": pdf_name,
        "created":  datetime.datetime.now().isoformat(),
    }
    db_append(record)

    return render_template("success.html", name=data["name"], pdf_id=pdf_id)

@app.route("/download/<pdf_id>")
def download_public(pdf_id):
    """候補者用ダウンロード（提出直後のみ想定）"""
    for r in db_all():
        if r["id"] == pdf_id:
            path = os.path.join(PDF_DIR, r["pdf_file"])
            if os.path.exists(path):
                return send_file(path, as_attachment=True,
                                 download_name=f'履歴書_{r["name"]}.pdf')
    abort(404)

# ════════════════════════════════════════════════════════════════
#  管理者ルート
# ════════════════════════════════════════════════════════════════
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("パスワードが違います")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    q = request.args.get("q","").strip()
    records = db_search(q) if q else db_all()
    records = sorted(records, key=lambda r: r.get("created",""), reverse=True)
    return render_template("admin_dashboard.html", records=records, query=q)

@app.route("/admin/download/<pdf_id>")
@admin_required
def admin_download(pdf_id):
    for r in db_all():
        if r["id"] == pdf_id:
            path = os.path.join(PDF_DIR, r["pdf_file"])
            if os.path.exists(path):
                return send_file(path, as_attachment=True,
                                 download_name=f'履歴書_{r["name"]}.pdf')
    abort(404)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

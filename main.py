from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import shutil
import os
import csv, io
import models, crud, auth, utils
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ==========================
# Auth & Dashboard
# ==========================
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "login_url": auth.get_login_url("state-unesa")
    })


@app.get("/auth/callback")
def auth_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    token = auth.exchange_code(code)
    userinfo = auth.get_user_info(token)

    email = userinfo["email"]
    nama = userinfo.get("name", "")
    foto_profil = userinfo.get("picture", "")

    if not (email.endswith("@unesa.ac.id") or email.endswith("@mhs.unesa.ac.id")):
        return HTMLResponse("<h2>Akses ditolak</h2><p>Hanya email UNESA yang diperbolehkan.</p>", status_code=403)

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email, nama=nama, foto_profil=foto_profil)
        db.add(user)
    else:
        user.nama = nama
        user.foto_profil = foto_profil
    db.commit()
    db.refresh(user)

    response = RedirectResponse(url="/dashboard")
    response.set_cookie(key="session", value=auth.serializer.dumps({"email": email}))
    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session")
    if not token:
        return RedirectResponse("/")
    email = auth.serializer.loads(token)["email"]
    user = db.query(models.User).filter(models.User.email == email).first()
    kuisioners = crud.get_user_kuisioners(db, user.id)

    other_kuisioners = db.query(models.Kuisioner).filter(
        models.Kuisioner.owner_id != user.id
    ).join(models.User).limit(10).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "kuisioners": kuisioners,
        "other_kuisioners": other_kuisioners
    })


# ==========================
# Kuisioner CRUD
# ==========================
@app.post("/kuisioner/create")
def create_kuisioner(
    title: str = Form(...),
    description: str = Form(None),
    background: str = Form("white"),
    db: Session = Depends(get_db),
    request: Request = None
):
    email = auth.serializer.loads(request.cookies.get("session"))["email"]
    user = db.query(models.User).filter(models.User.email == email).first()
    crud.create_kuisioner(db, title, user.id, description, background)
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/kuisioner/{kid}", response_class=HTMLResponse)
def view_kuisioner(request: Request, kid: int, db: Session = Depends(get_db)):
    token = request.cookies.get("session")
    if not token:
        return RedirectResponse("/")
    email = auth.serializer.loads(token)["email"]
    user = db.query(models.User).filter(models.User.email == email).first()
    kuisioner = crud.get_kuisioner(db, kid)
    if not kuisioner or kuisioner.owner_id != user.id:
        return RedirectResponse("/")

    url = f"http://kuisnesa.nauval.site/survey/{kid}"
    qr_path = utils.generate_qr_base64(url)

    return templates.TemplateResponse("kuisioner.html", {
        "request": request,
        "kuisioner": kuisioner,
        "qr_path": qr_path,
        "share_url": url
    })


@app.post("/kuisioner/{kid}/delete")
def delete_kuisioner(kid: int, db: Session = Depends(get_db)):
    question_ids = [q.id for q in db.query(models.Question).filter(models.Question.kuisioner_id == kid).all()]
    if question_ids:
        db.query(models.Response).filter(models.Response.question_id.in_(question_ids)).delete(synchronize_session=False)

    db.query(models.Question).filter(models.Question.kuisioner_id == kid).delete()
    db.query(models.Kuisioner).filter(models.Kuisioner.id == kid).delete()
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/kuisioner/{kid}/edit")
async def update_kuisioner(
    kid: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    background: str = Form(None),
    theme: str = Form(None),
    access: str = Form("public"),
    header_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("session")
    email = auth.serializer.loads(token)["email"]
    user = db.query(models.User).filter_by(email=email).first()
    kuisioner = db.query(models.Kuisioner).get(kid)
    if not kuisioner or kuisioner.owner_id != user.id:
        return RedirectResponse("/")

    kuisioner.title = title
    kuisioner.description = description
    kuisioner.background = background
    kuisioner.theme = theme
    kuisioner.access = access

    if header_image:
        file_path = f"static/uploads/header_{kid}.png"
        with open(file_path, "wb") as f:
            f.write(await header_image.read())
        kuisioner.header_image = f"/{file_path}"

    db.commit()
    return RedirectResponse(f"/kuisioner/{kid}", status_code=303)


# ==========================
# Pertanyaan
# ==========================
@app.post("/kuisioner/{kid}/add_question")
async def add_question(
    kid: int,
    text: str = Form(...),
    qtype: str = Form("short_text"),
    options: list[str] = Form([]),  # bisa multi field "options"
    is_required: str = Form(None),
    media: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    import json
    media_url = None

    if media and media.filename:
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"q_{kid}_{media.filename}")
        with open(file_path, "wb") as buffer:
            buffer.write(await media.read())
        media_url = f"/{file_path}"

    crud.add_question(
        db,
        kid,
        text,
        qtype,
        json.dumps(options) if options else None,  # simpan sebagai JSON
        media_url,
        bool(is_required)
    )

    return RedirectResponse(f"/kuisioner/{kid}", status_code=303)


@app.post("/question/{question_id}/edit")
def edit_question(
    question_id: int,
    text: str = Form(...),
    qtype: str = Form(...),
    options: str = Form(None),
    media: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan")

    question.text = text
    question.qtype = qtype
    question.options = options

    if media:
        filename = f"q{question_id}_{media.filename}"
        filepath = os.path.join("static/uploads", filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(media.file, buffer)
        question.media_url = f"/static/uploads/{filename}"

    db.commit()
    db.refresh(question)
    return RedirectResponse(url=f"/kuisioner/{question.kuisioner_id}", status_code=303)


@app.post("/question/{question_id}/delete")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan")

    kid = question.kuisioner_id
    db.query(models.Response).filter(models.Response.question_id == question_id).delete()
    db.delete(question)
    db.commit()

    return RedirectResponse(url=f"/kuisioner/{kid}", status_code=303)


# ==========================
# Survey (Publik)
# ==========================
@app.get("/survey/{kid}", response_class=HTMLResponse)
def survey_page(request: Request, kid: int, db: Session = Depends(get_db)):
    kuisioner = crud.get_kuisioner(db, kid)
    if not kuisioner:
        raise HTTPException(status_code=404, detail="Kuisioner tidak ditemukan")

    # parsing opsi
    for q in kuisioner.questions:
        if q.options:
            try:
                import json
                q.options = json.loads(q.options)
            except:
                q.options = [o.strip() for o in q.options.split(",") if o.strip()]

    return templates.TemplateResponse("survey.html", {
        "request": request,
        "kuisioner": kuisioner
    })


@app.post("/survey/{kid}")
async def submit_survey(
    request: Request,
    kid: int,
    nama: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    form = await request.form()
    user = crud.get_or_create_user(db, email=email, nama=nama, role="public")
    kuisioner = crud.get_kuisioner(db, kid)

    try:
        for q in kuisioner.questions:
            ans = form.get(f"q_{q.id}")
            if ans:
                crud.create_response(db, user.id, q.id, ans)
    except HTTPException as e:
        if e.status_code == 400:
            return HTMLResponse("<h2>❌ Maaf</h2><p>Anda sudah pernah mengisi kuisioner ini.</p>", status_code=400)
        raise

    return RedirectResponse("/thanks", status_code=303)


@app.get("/thanks", response_class=HTMLResponse)
def thanks(request: Request):
    return HTMLResponse("<h2>Terima kasih sudah mengisi kuisioner 🎉</h2>")


# ==========================
# Export & Stats
# ==========================
@app.get("/kuisioner/{kid}/export")
def export_kuisioner_csv(kid: int, db: Session = Depends(get_db)):
    kuisioner = db.query(models.Kuisioner).filter(models.Kuisioner.id == kid).first()
    if not kuisioner:
        raise HTTPException(status_code=404, detail="Kuisioner tidak ditemukan")

    responses = (
        db.query(
            models.Response.answer,
            models.User.nama,
            models.User.email,
            models.Question.text.label("question")
        )
        .join(models.User, models.User.id == models.Response.user_id)
        .join(models.Question, models.Question.id == models.Response.question_id)
        .filter(models.Question.kuisioner_id == kid)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nama", "Email", "Pertanyaan", "Jawaban"])
    for r in responses:
        writer.writerow([r.nama or "", r.email, r.question, r.answer])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=kuisioner_{kid}_responses.csv"}
    )


@app.get("/kuisioner/{kid}/stats", response_class=HTMLResponse)
def kuisioner_stats(request: Request, kid: int, db: Session = Depends(get_db)):
    kuisioner = db.query(models.Kuisioner).get(kid)
    if not kuisioner:
        return HTMLResponse("Kuisioner tidak ditemukan", status_code=404)

    # ambil responses dengan join ke User & Question
    raw_stats = (
        db.query(
            models.Response.id,
            models.Response.answer,
            models.Response.question_id,
            models.User.nama,
            models.User.email,
            models.Question.text.label("question_text")
        )
        .join(models.User, models.Response.user_id == models.User.id)
        .join(models.Question, models.Response.question_id == models.Question.id)
        .filter(models.Question.kuisioner_id == kid)
        .all()
    )

    response_stats = [
        {
            "id": r.id,
            "question_id": r.question_id,
            "text": r.question_text,
            "answer": r.answer,
            "nama": r.nama,
            "email": r.email
        }
        for r in raw_stats
    ]

    total_responses = (
        db.query(models.Response.user_id)
        .join(models.Question, models.Response.question_id == models.Question.id)
        .filter(models.Question.kuisioner_id == kid)
        .distinct()
        .count()
    )

    # ubah kuisioner.questions → list of dict
    questions_data = [
        {
            "id": q.id,
            "text": q.text,
            "qtype": q.qtype,
            "options": q.options,
            "required": q.required
        }
        for q in kuisioner.questions
    ]

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "kuisioner": kuisioner,
        "questions": questions_data,   # ⬅️ ini yang dipakai di template
        "response_stats": response_stats,
        "total_responses": total_responses,
        "share_url": f"/survey/{kuisioner.id}"
    })
    res = crud.get_responses_by_kuisioner(db, kid)

    if not res:
        return {"error": "No responses found for this kuisioner"}

    # Perform all text analytics
    topics = utils.lda_topic_modeling(res, n_topics=3, n_words=5)
    keywords = utils.extract_keywords(res, top_n=10)
    sentiment = utils.analyze_sentiment(res)
    stats = utils.text_statistics(res)

    return {
        "kuisioner_id": kid,
        "lda_topics": topics,
        "keywords": keywords,
        "sentiment_analysis": sentiment,
        "text_stats": stats
    }

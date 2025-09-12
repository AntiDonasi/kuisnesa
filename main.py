from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, crud, auth, utils
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kuisioner UNESA")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "login_url": auth.get_login_url("state")})

@app.get("/auth/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    info = await auth.get_user_info(code)
    role = auth.determine_role(info["email"])
    user = crud.get_or_create_user(db, email=info["email"], nama=info["name"], role=role)
    token = auth.serializer.dumps({"email": info["email"]})
    resp = RedirectResponse("/dashboard")
    resp.set_cookie("session", token, httponly=True)
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session")
    if not token: return RedirectResponse("/")
    email = auth.serializer.loads(token)["email"]
    user = db.query(models.User).filter(models.User.email == email).first()
    kuisioners = crud.get_user_kuisioners(db, user.id)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "kuisioners": kuisioners})

@app.post("/kuisioner/create")
def create_kuisioner(title: str = Form(...), description: str = Form(None), background: str = Form("white"), db: Session = Depends(get_db), request: Request = None):
    email = auth.serializer.loads(request.cookies.get("session"))["email"]
    user = db.query(models.User).filter(models.User.email == email).first()
    crud.create_kuisioner(db, title, user.id, description, background)
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/kuisioner/{kid}", response_class=HTMLResponse)
def view_kuisioner(request: Request, kid: int, db: Session = Depends(get_db)):
    k = crud.get_kuisioner(db, kid)
    return templates.TemplateResponse("kuisioner.html", {"request": request, "kuisioner": k})

@app.post("/kuisioner/{kid}/add_question")
def add_question(kid: int, text: str = Form(...), qtype: str = Form("short_text"), options: str = Form(None), media: str = Form(None), db: Session = Depends(get_db)):
    opts = options.split(",") if options else None
    crud.add_question(db, kid, text, qtype, opts, media)
    return RedirectResponse(f"/kuisioner/{kid}", status_code=303)

@app.get("/survey/{kid}", response_class=HTMLResponse)
def survey(request: Request, kid: int, db: Session = Depends(get_db)):
    k = crud.get_kuisioner(db, kid)
    return templates.TemplateResponse("survey.html", {"request": request, "kuisioner": k})

@app.post("/survey/{kid}")
async def submit_survey(request: Request, kid: int, nama: str = Form(...), email: str = Form(...), db: Session = Depends(get_db)):
    form = await request.form()
    user = crud.get_or_create_user(db, email=email, nama=nama, role="public")
    k = crud.get_kuisioner(db, kid)
    for q in k.questions:
        ans = form.get(f"q_{q.id}")
        if ans:
            crud.create_response(db, user.id, q.id, ans)
    return RedirectResponse("/thanks", status_code=303)

@app.get("/thanks", response_class=HTMLResponse)
def thanks(request: Request):
    return HTMLResponse("<h2>Terima kasih sudah mengisi kuisioner 🎉</h2>")

@app.get("/kuisioner/{kid}/export")
def export_csv(kid: int, db: Session = Depends(get_db)):
    res = crud.get_responses_by_kuisioner(db, kid)
    path = utils.export_responses(res, f"kuisioner_{kid}.csv")
    return FileResponse(path, filename=f"kuisioner_{kid}.csv")

@app.get("/kuisioner/{kid}/stats", response_class=HTMLResponse)
def stats(request: Request, kid: int, db: Session = Depends(get_db)):
    res = crud.get_responses_by_kuisioner(db, kid)
    chart = utils.chart_distribution(res, f"chart_{kid}.png")
    wc = utils.generate_wordcloud(res, f"wc_{kid}.png")
    return templates.TemplateResponse("stats.html", {"request": request, "chart": "/" + chart, "wc": "/" + wc})

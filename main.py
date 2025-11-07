from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import models, crud, auth, utils, os
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kuisioner UNESA")
templates = Jinja2Templates(directory="templates")

# Mount static files
os.makedirs("static/charts", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("indeks.html", {"request": request, "login_url": auth.get_login_url("state-unesa")})

@app.get("/auth/callback")
async def callback(code: str, state: str = None, db: Session = Depends(get_db)):
    info = await auth.get_user_info(code)
    user = crud.get_or_create_user(
        db,
        email=info["email"],
        nama=info.get("name", info["email"]),
        role="user",
        photo_url=info.get("picture")
    )
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
    user = crud.get_or_create_user(db, email=email, nama=nama, role="user", photo_url=None)
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
    k = crud.get_kuisioner(db, kid)
    res = crud.get_responses_by_kuisioner(db, kid)

    # Generate all visualizations
    chart = utils.chart_distribution(res, f"chart_{kid}.png")
    pie = utils.create_pie_chart(res, f"pie_{kid}.png")
    wc = utils.generate_wordcloud(res, f"wc_{kid}.png")
    sentiment_chart = utils.create_sentiment_chart(res, f"sentiment_{kid}.png")
    word_freq = utils.create_word_frequency_chart(res, f"word_freq_{kid}.png")
    response_length = utils.create_response_length_chart(res, f"response_length_{kid}.png")
    top_contributors = utils.create_top_contributors_chart(res, f"contributors_{kid}.png")
    keyword_chart = utils.create_keyword_comparison_chart(res, f"keyword_chart_{kid}.png")
    stats_dashboard = utils.create_comprehensive_stats_chart(res, f"stats_dashboard_{kid}.png")

    # Get text analytics
    topics = utils.lda_topic_modeling(res, n_topics=3, n_words=5) if len(res) >= 3 else None
    keywords = utils.extract_keywords(res, top_n=10)
    sentiment = utils.analyze_sentiment(res)
    text_stats = utils.text_statistics(res)

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "kuisioner": k,
        "chart": "/" + chart,
        "pie": "/" + pie,
        "wc": "/" + wc,
        "sentiment_chart": "/" + sentiment_chart,
        "word_freq": "/" + word_freq,
        "response_length": "/" + response_length,
        "top_contributors": "/" + top_contributors,
        "keyword_chart": "/" + keyword_chart,
        "stats_dashboard": "/" + stats_dashboard,
        "topics": topics,
        "keywords": keywords,
        "sentiment": sentiment,
        "text_stats": text_stats
    })

@app.get("/kuisioner/{kid}/analytics")
def text_analytics(kid: int, db: Session = Depends(get_db)):
    """
    Comprehensive text analytics endpoint
    Returns: LDA topics, keywords, sentiment analysis, and text statistics
    """
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

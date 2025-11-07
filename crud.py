import models, json
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
from typing import Optional
from fastapi import HTTPException

def get_or_create_user(db: Session, email: str, nama: str, role: str = "user", photo_url: str = None):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        if nama:
            user.nama = nama
        if photo_url:
            user.photo_url = photo_url
        db.commit()
        db.refresh(user)
        return user
    u = models.User(email=email, nama=nama, role=role, photo_url=photo_url)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def create_kuisioner(db: Session, title: str, owner_id: int, desc: str = None, bg: str = "white"):
    k = models.Kuisioner(title=title, owner_id=owner_id, description=desc, background=bg)
    db.add(k)
    db.commit()
    db.refresh(k)
    return k

def add_question(db, kuisioner_id, text, qtype, options=None, media_url=None, required=False):
    question = models.Question(
        kuisioner_id=kuisioner_id,
        text=text,
        qtype=qtype,
        options=json.dumps(options) if options else None,
        media_url=media_url,
        required=required
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

def get_kuisioner(db: Session, kid: int):
    return db.query(models.Kuisioner).filter(models.Kuisioner.id == kid).first()

def get_user_kuisioners(db: Session, uid: int):
    return db.query(models.Kuisioner).filter(models.Kuisioner.owner_id == uid).all()

def get_response_statistics(db: Session, kid: int):
    results = db.query(
        models.Response.answer,
        models.User.nama,
        models.User.email,
        models.Question.text
    ).join(
        models.Question, models.Response.question_id == models.Question.id
    ).join(
        models.User, models.Response.user_id == models.User.id
    ).filter(
        models.Question.kuisioner_id == kid
    ).all()
    return results

def create_response(db: Session, user_id: int, question_id: int, answer: str):
    existing = db.query(models.Response).filter_by(user_id=user_id, question_id=question_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Maaf, Anda sudah mengisi kuisioner ini sebelumnya."
        )
    
    db_response = models.Response(
        answer=answer,
        user_id=user_id,
        question_id=question_id
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def get_responses_by_kuisioner(db: Session, kid: int):
    return db.query(models.Response).join(models.Question).filter(models.Question.kuisioner_id == kid).all()

def update_kuisioner(
    db: Session,
    kuisioner_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    background: Optional[str] = None,
    theme: Optional[str] = None,
    access: Optional[str] = None,
    end_date: Optional[datetime.datetime] = None
):
    k = db.query(models.Kuisioner).filter(models.Kuisioner.id == kuisioner_id).first()
    if not k:
        return None

    if title is not None:
        k.title = title
    if description is not None:
        k.description = description
    if background is not None:
        k.background = background
    if theme is not None:
        k.theme = theme
    if access is not None:
        k.access = access
    if end_date is not None:
        if isinstance(end_date, str):
            try:
                k.end_date = datetime.datetime.fromisoformat(end_date)
            except:
                pass
        else:
            k.end_date = end_date

    db.commit()
    db.refresh(k)
    return k

def update_question(
    db: Session,
    question_id: int,
    text: Optional[str] = None,
    qtype: Optional[str] = None,
    options: Optional[list] = None,
    media: Optional[str] = None
):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        return None

    if text is not None:
        q.text = text
    if qtype is not None:
        q.qtype = qtype
    if options is not None:
        q.options = json.dumps(options) if isinstance(options, list) else options
    if media is not None:
        q.media = media

    db.commit()
    db.refresh(q)
    return q

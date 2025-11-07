import models, json
from sqlalchemy.orm import Session

def get_or_create_user(db: Session, email: str, nama: str, role: str = "mahasiswa", photo_url: str = None):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        # Update existing user's name and photo if provided
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

def add_question(db: Session, kid: int, text: str, qtype: str, options=None, media=None, required=False):
    q = models.Question(
        text=text,
        qtype=qtype,
        options=json.dumps(options) if options else None,
        media_url=media,
        required=required,
        kuisioner_id=kid
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

def get_kuisioner(db: Session, kid: int):
    return db.query(models.Kuisioner).filter(models.Kuisioner.id == kid).first()

def get_user_kuisioners(db: Session, uid: int):
    return db.query(models.Kuisioner).filter(models.Kuisioner.owner_id == uid).all()

def create_response(db: Session, user_id: int, qid: int, ans: str):
    r = models.Response(user_id=user_id, question_id=qid, answer=ans)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

def get_responses_by_kuisioner(db: Session, kid: int):
    return db.query(models.Response).join(models.Question).filter(models.Question.kuisioner_id == kid).all()

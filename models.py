from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100))
    email = Column(String(120), unique=True, index=True)
    role = Column(String(20), default="user")  # Unified user role
    photo_url = Column(String(500), nullable=True)  # Google profile photo

    kuisioners = relationship("Kuisioner", back_populates="owner")
    responses = relationship("Response", back_populates="user")


class Kuisioner(Base):
    __tablename__ = "kuisioners"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    background = Column(String(200), default="white")
    theme = Column(String(50), default="light")
    header_image = Column(String(300))  # Header image
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    access = Column(String(20), default="public")  # public / unesa_only
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="kuisioners")
    questions = relationship("Question", back_populates="kuisioner")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    kuisioner_id = Column(Integer, ForeignKey("kuisioners.id"))
    text = Column(Text, nullable=False)
    qtype = Column(String(50), default="short_text")
    options = Column(Text)  # JSON string
    media_url = Column(String(300))
    required = Column(Boolean, default=False)

    kuisioner = relationship("Kuisioner", back_populates="questions")
    responses = relationship("Response", back_populates="question")


class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    answer = Column(Text, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    user = relationship("User", back_populates="responses")
    question = relationship("Question", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="unique_user_response"),
    )

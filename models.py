from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100))
    email = Column(String(120), unique=True, index=True)
    role = Column(String(20), default="mahasiswa")  # mahasiswa/dosen/public

    kuisioners = relationship("Kuisioner", back_populates="owner")
    responses = relationship("Response", back_populates="user")

class Kuisioner(Base):
    __tablename__ = "kuisioners"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    background = Column(String(200), default="white")
    theme = Column(String(50), default="light")
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    access = Column(String(20), default="public")  # public, unesa_only
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="kuisioners")
    questions = relationship("Question", back_populates="kuisioner")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    qtype = Column(String(50), default="short_text")  # short_text, paragraph, single_choice, multi_choice, rating
    options = Column(Text, nullable=True)  # simpan JSON string
    required = Column(Boolean, default=False)
    media_url = Column(String(255), nullable=True)
    kuisioner_id = Column(Integer, ForeignKey("kuisioners.id"))

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

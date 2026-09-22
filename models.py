from sqlalchemy import Column, BigInteger, String, Date, Integer, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base
import enum

class CefrLevel(str, enum.Enum):
    A1 = 'A1'
    A2 = 'A2'
    B1 = 'B1'
    B2 = 'B2'
    C1 = 'C1'
    C2 = 'C2'

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    current_level = Column(Enum(CefrLevel), default=CefrLevel.A2, nullable=False)
    target_level = Column(Enum(CefrLevel), default=CefrLevel.C1, nullable=False)
    deadline_date = Column(Date, nullable=True)
    streak_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_date = Column(Date, nullable=False)
    item_type = Column(String(50), nullable=False)
    item_id = Column(BigInteger, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(255), nullable=False)
    example_sentence = Column(Text, nullable=True)
    level = Column(String(10), nullable=False)
    topic = Column(String(100), nullable=True)
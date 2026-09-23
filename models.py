from sqlalchemy import Column, String, Date, Integer, Boolean, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

# --- ENUMLAR ---
class CefrLevel(str, enum.Enum):
    A1 = 'A1'
    A2 = 'A2'
    B1 = 'B1'
    B2 = 'B2'
    C1 = 'C1'
    C2 = 'C2'

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"

class ItemTypeEnum(str, enum.Enum):
    hair = "hair"
    clothes = "clothes"
    shoes = "shoes"
    accessory = "accessory"
    hint = "hint"            
    freeze = "freeze"        

# --- ASOSIY JADVALLAR ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    current_level = Column(Enum(CefrLevel), default=CefrLevel.A1, nullable=False)
    target_level = Column(Enum(CefrLevel), default=CefrLevel.C1, nullable=False)
    deadline_date = Column(Date, nullable=True)
    
    balance = Column(Integer, default=300000, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=True)
    avatar_state = Column(JSON, default={}) 
    
    streak_count = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    has_freeze = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tasks = relationship("DailyTask", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("WalletHistory", back_populates="user", cascade="all, delete-orphan")


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_date = Column(Date, nullable=False)
    item_type = Column(String(50), nullable=False)
    item_id = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tasks")


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(255), nullable=False)
    example_sentence = Column(Text, nullable=True)
    level = Column(String(10), nullable=False)
    topic = Column(String(100), nullable=True)


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(Enum(CefrLevel), nullable=False)
    order_num = Column(Integer, nullable=False) 
    title = Column(String(255), nullable=False)
    youtube_id = Column(String(50), nullable=False) 
    
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    
    video_watched = Column(Boolean, default=False, nullable=False) 
    test_score = Column(Integer, default=0, nullable=False)        
    writing_score = Column(Integer, default=0, nullable=False)     
    
    is_completed = Column(Boolean, default=False, nullable=False)  
    is_flawless = Column(Boolean, default=False, nullable=False)   
    earned_amount = Column(Integer, default=0, nullable=False)     

    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    item_type = Column(Enum(ItemTypeEnum), nullable=False)
    price = Column(Integer, nullable=False)
    model_url = Column(String(255), nullable=True) 
    is_rare = Column(Boolean, default=False, nullable=False)

    inventory = relationship("Inventory", back_populates="item", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventory" # <--- bu yerdagi pastki chiziq xatosi to'g'irlandi (__tablename__)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("shop_items.id", ondelete="CASCADE"), nullable=False)
    is_equipped = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="inventory")
    item = relationship("ShopItem", back_populates="inventory")


class WalletHistory(Base):
    __tablename__ = "wallet_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False) 
    reason = Column(String(255), nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="transactions")

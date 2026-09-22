from sqlalchemy import Column, BigInteger, String, Date, Integer, Boolean, DateTime, Enum, ForeignKey, Text, JSON
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
    hint = "hint"            # Qiyin testlar uchun yordam
    freeze = "freeze"        # Streak uzilmasligi uchun muzlatgich

# --- ASOSIY JADVALLAR ---

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # O'quv Rejasi
    current_level = Column(Enum(CefrLevel), default=CefrLevel.A1, nullable=False)
    target_level = Column(Enum(CefrLevel), default=CefrLevel.C1, nullable=False)
    deadline_date = Column(Date, nullable=True)
    
    # Iqtisodiyot va 3D Avatar
    balance = Column(Integer, default=300000, nullable=False) # Boshlang'ich kapital
    gender = Column(Enum(GenderEnum), nullable=True)
    avatar_state = Column(JSON, default={}) # Kiyilgan buyumlar holati
    
    # Kunlik Zanjir (Daily Streak)
    streak_count = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    has_freeze = Column(Boolean, default=False, nullable=False) # Streak kuyib ketmasligi uchun
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Bog'lanishlar (Relationships)
    tasks = relationship("DailyTask", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("WalletHistory", back_populates="user", cascade="all, delete-orphan")


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_date = Column(Date, nullable=False)
    item_type = Column(String(50), nullable=False)
    item_id = Column(BigInteger, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tasks")


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(255), nullable=False)
    example_sentence = Column(Text, nullable=True)
    level = Column(String(10), nullable=False)
    topic = Column(String(100), nullable=True)


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    level = Column(Enum(CefrLevel), nullable=False)
    order_num = Column(Integer, nullable=False) # Darsning ketma-ketlik raqami
    title = Column(String(255), nullable=False)
    youtube_id = Column(String(50), nullable=False) # Masalan: "n-uTwzzVnsg"
    
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(BigInteger, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    
    # Moliyaviy va O'quv ko'rsatkichlari
    video_watched = Column(Boolean, default=False, nullable=False) # 20,000 so'm sharti
    test_score = Column(Integer, default=0, nullable=False)        # Max: 20,000 so'm
    writing_score = Column(Integer, default=0, nullable=False)     # Max: 10,000 so'm
    
    is_completed = Column(Boolean, default=False, nullable=False)  # Keyingi darsni ochish uchun
    is_flawless = Column(Boolean, default=False, nullable=False)   # 100% to'g'ri (Combo)
    earned_amount = Column(Integer, default=0, nullable=False)     # Qayta ishlashda (Retry) ortiqcha pul bermaslik uchun

    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    item_type = Column(Enum(ItemTypeEnum), nullable=False)
    price = Column(Integer, nullable=False)
    model_url = Column(String(255), nullable=True) # 3D element havolasi
    is_rare = Column(Boolean, default=False, nullable=False)

    inventory = relationship("Inventory", back_populates="item", cascade="all, delete-orphan")


class Inventory(Base):
    """Foydalanuvchi sotib olgan kiyim va buyumlar (Avatar uchun)"""
    __tablename__ = "inventory"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(BigInteger, ForeignKey("shop_items.id", ondelete="CASCADE"), nullable=False)
    is_equipped = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="inventory")
    item = relationship("ShopItem", back_populates="inventory")


class WalletHistory(Base):
    """Pullarning kirim va chiqim tarixi (Adrenalin, Darslar, Do'kon)"""
    __tablename__ = "wallet_history"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False) # Musbat (+) yoki Manfiy (-) qiymatlar
    reason = Column(String(255), nullable=False) # "Adrenalin yutug'i", "Kurtka xaridi", "A1 -> A2 to'lovi"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="transactions")

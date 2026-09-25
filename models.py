import enum
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum, Date, DateTime
from sqlalchemy.orm import relationship
from database import Base

# --- ENUM TURLARI ---

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"

class CefrLevel(str, enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class ItemTypeEnum(str, enum.Enum):
    hair = "hair"
    clothes = "clothes"
    accessory = "accessory"


# --- JADVALLAR (MODELLAR) ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    gender = Column(String, default="male")
    balance = Column(Integer, default=300000)
    current_level = Column(String, default="A1")

    inventory = relationship("Inventory", back_populates="user")
    wallet_history = relationship("WalletHistory", back_populates="user")
    tasks = relationship("DailyTask", back_populates="user")


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    item_type = Column(Enum(ItemTypeEnum), default=ItemTypeEnum.hair)
    price = Column(Integer, default=0)
    model_url = Column(String, nullable=True)
    is_rare = Column(Boolean, default=False)


class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("shop_items.id"))
    is_equipped = Column(Boolean, default=False)

    user = relationship("User", back_populates="inventory")
    item = relationship("ShopItem")


class WalletHistory(Base):
    __tablename__ = "wallet_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wallet_history")


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_date = Column(Date, default=date.today)
    item_type = Column(String, nullable=False)
    item_id = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, index=True, nullable=False)
    translation = Column(String, nullable=False)
    example_sentence = Column(Text, nullable=True)
    level = Column(String, default="A1")
    topic = Column(String, nullable=True)


class VocabWord(Base):
    __tablename__ = "vocab_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, index=True, nullable=False)
    translation = Column(String, nullable=False)
    example_sentence = Column(Text, nullable=True)
    example_translation = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    set_number = Column(Integer, default=1)
    lesson_number = Column(Integer, default=1)
    level = Column(String, default="A1")

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from datetime import date
from database import engine, get_db
import models, schemas, security

# Jadvallarni bazada avtomatik yaratish
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IELTS & AI Learning Platform API", version="1.0")

# HTML fayllar turgan papkani ulash
templates = Jinja2Templates(directory="templates")

# --- PYDANTIC SXEMALARI ---
class VocabCreate(BaseModel):
    word: str
    translation: str
    example_sentence: str | None = None
    level: str
    topic: str | None = None

class TaskDoneUpdate(BaseModel):
    user_id: int
    item_type: str 
    item_id: int

class ForgotPasswordSchema(BaseModel):
    email: EmailStr
    new_password: str


# --- STARTUP: REAL YUZLAR BILAN DO'KONNI TO'LDIRISH ---
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    if db.query(models.ShopItem).count() == 0:
        default_items = [
            # --- ERKAKLAR YUZLARI ---
            models.ShopItem(
                name="Alex (Klassik yuz)", 
                item_type=models.ItemTypeEnum.hair, 
                price=25000, 
                model_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", 
                is_rare=False
            ),
            models.ShopItem(
                name="David (Stilist yuz)", 
                item_type=models.ItemTypeEnum.hair, 
                price=45000, 
                model_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", 
                is_rare=True
            ),
            models.ShopItem(
                name="Marcus (Jiddiy qiyofa)", 
                item_type=models.ItemTypeEnum.hair, 
                price=60000, 
                model_url="https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150", 
                is_rare=True
            ),

            # --- QIZLAR YUZLARI ---
            models.ShopItem(
                name="Sophia (Elegant yuz)", 
                item_type=models.ItemTypeEnum.hair, 
                price=25000, 
                model_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150", 
                is_rare=False
            ),
            models.ShopItem(
                name="Emma (Modulli qiyofa)", 
                item_type=models.ItemTypeEnum.hair, 
                price=50000, 
                model_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", 
                is_rare=True
            ),
            models.ShopItem(
                name="Olivia (Nodir yuz)", 
                item_type=models.ItemTypeEnum.hair, 
                price=80000, 
                model_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150", 
                is_rare=True
            ),
        ]
        db.add_all(default_items)
        db.commit()
    db.close()


# --- 1. FRONTEND SAHIFALARNI OCHISH ---
@app.get("/", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/vocabulary", response_class=HTMLResponse)
def read_vocabulary_page(request: Request):
    return templates.TemplateResponse(request, "vocabulary.html")

@app.get("/grammar", response_class=HTMLResponse)
def read_grammar(request: Request):
    return templates.TemplateResponse(request, "grammar.html")

@app.get("/listening", response_class=HTMLResponse)
def read_listening(request: Request):
    return templates.TemplateResponse(request, "listening.html")

@app.get("/speaking", response_class=HTMLResponse)
def read_speaking(request: Request):
    return templates.TemplateResponse(request, "speaking.html")

@app.get("/reading", response_class=HTMLResponse)
def read_reading(request: Request):
    return templates.TemplateResponse(request, "reading.html")

@app.get("/writing", response_class=HTMLResponse)
def read_writing(request: Request):
    return templates.TemplateResponse(request, "writing.html")

@app.get("/exam", response_class=HTMLResponse)
def read_exam(request: Request):
    return templates.TemplateResponse(request, "exam.html")


# --- 2. API ENDPOINTLAR (AUTH & USERS) ---

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Bu Username yoki Email allaqachon mavjud!"
        )

    hashed_pwd = security.get_password_hash(user.password)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_pwd,
        gender=user.gender,
        balance=300000,
        current_level=models.CefrLevel.A1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    welcome_bonus = models.WalletHistory(
        user_id=new_user.id,
        amount=300000,
        reason="Xush kelibsiz bonusi"
    )
    db.add(welcome_bonus)
    db.commit()

    return new_user

@app.post("/login")
def login_user(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == login_data.username).first()
    
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Username yoki parol noto'g'ri!")
    
    return {
        "message": "Muvaffaqiyatli kirdingiz!", 
        "username": user.username, 
        "balance": user.balance, 
        "user_id": user.id
    }

@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Bu email bilan ro'yxatdan o'tgan foydalanuvchi topilmadi!")
    
    user.password_hash = security.get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "Parolingiz muvaffaqiyatli o'zgartirildi! Yangi parol bilan kirishingiz mumkin."}


# --- 3. DO'KON VA PERSONAJ ENDPOINTLARI ---

@app.get("/shop-items")
def get_shop_items(db: Session = Depends(get_db)):
    return db.query(models.ShopItem).all()

@app.post("/buy-item/{item_id}")
def buy_item(item_id: int, user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi! Iltimos tizimga qayta kiring.")

    item = db.query(models.ShopItem).filter(models.ShopItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Buyum topilmadi!")
    
    existing_inv = db.query(models.Inventory).filter(
        models.Inventory.user_id == user.id,
        models.Inventory.item_id == item_id
    ).first()
    
    if existing_inv:
        return {"message": f"Bu yuz sizda bor. Muvaffaqiyatli kiyildi!", "new_balance": user.balance}
    
    if user.balance < item.price:
        raise HTTPException(status_code=400, detail="Balansingizda yetarli mablag' yo'q!")
    
    user.balance -= item.price
    wallet_history = models.WalletHistory(
        user_id=user.id,
        amount=-item.price,
        reason=f"Sotib olindi: {item.name}"
    )
    db.add(wallet_history)
    
    new_inventory = models.Inventory(
        user_id=user.id,
        item_id=item_id,
        is_equipped=True
    )
    db.add(new_inventory)
    db.commit()
    
    return {"message": f"{item.name} muvaffaqiyatli sotib olindi va kiyildi!", "new_balance": user.balance}


# --- 4. LUG'AT VA BOSHQA API ENDPOINTLAR ---

@app.get("/api/words/")
def get_vocabulary_words(level: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.VocabularyWord)
    if level:
        query = query.filter(models.VocabularyWord.level == level)
    return query.all()

@app.get("/seed-vocab")
def seed_vocabulary(db: Session = Depends(get_db)):
    if db.query(models.VocabularyWord).count() > 0:
        return {"message": "Lug'at bazasi allaqachon to'ldirilgan! ✅"}

    words_to_seed = [
        {"word": "Always", "translation": "Har doim", "example_sentence": "I always wake up early.", "level": "A1", "topic": "Adverb"},
        {"word": "Environment", "translation": "Atrof-muhit", "example_sentence": "We must protect the environment.", "level": "A1", "topic": "Noun"},
        {"word": "Important", "translation": "Muhim", "example_sentence": "This exam is very important.", "level": "A1", "topic": "Adjective"},
        {"word": "Beautiful", "translation": "Chiroyli", "example_sentence": "She is a beautiful girl.", "level": "A1", "topic": "Adjective"},
        {"word": "Achievement", "translation": "Yutuq", "example_sentence": "Winning the race was a great achievement.", "level": "A2", "topic": "Noun"},
        {"word": "Determine", "translation": "Aniqlamoq / Qaror qilmoq", "example_sentence": "They need to determine the cause of the problem.", "level": "A2", "topic": "Verb"},
        {"word": "Go - Went - Gone", "translation": "Bormoq", "example_sentence": "I went to the store yesterday.", "level": "Irregular", "topic": "Verb (V1-V2-V3)"},
        {"word": "See - Saw - Seen", "translation": "Ko'rmoq", "example_sentence": "Have you seen my keys?", "level": "Irregular", "topic": "Verb (V1-V2-V3)"},
        {"word": "Take - Took - Taken", "translation": "Olmoq", "example_sentence": "He took my book.", "level": "Irregular", "topic": "Verb (V1-V2-V3)"}
    ]

    for item in words_to_seed:
        new_word = models.VocabularyWord(**item)
        db.add(new_word)
    
    db.commit()
    return {"message": "So'zlar bazaga muvaffaqiyatli yuklandi! 🎉"}

@app.get("/api/status")
def api_status():
    return {"message": "IELTS Platform API ishga tushdi! May oyigacha to'xtamaymiz 🚀"}

@app.get("/users/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user

@app.post("/vocabulary/")
def create_vocab(vocab: VocabCreate, db: Session = Depends(get_db)):
    db_vocab = models.VocabularyWord(**vocab.dict())
    db.add(db_vocab)
    db.commit()
    db.refresh(db_vocab)
    return db_vocab

@app.post("/tasks/done")
def mark_task_done(task: TaskDoneUpdate, db: Session = Depends(get_db)):
    existing_task = db.query(models.DailyTask).filter(
        models.DailyTask.user_id == task.user_id,
        models.DailyTask.item_type == task.item_type,
        models.DailyTask.item_id == task.item_id
    ).first()
    
    if existing_task:
        existing_task.is_completed = True
        existing_task.completed_at = func.now()
    else:
        new_task = models.DailyTask(
            user_id=task.user_id,
            task_date=date.today(),
            item_type=task.item_type,
            item_id=task.item_id,
            is_completed=True,
            completed_at=func.now()
        )
        db.add(new_task)
    
    db.commit()
    return {"status": "success", "message": "Vazifa [Done] qilindi va bazaga saqlandi! ✅"}

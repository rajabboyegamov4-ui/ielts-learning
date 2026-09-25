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


# --- STARTUP: DO'KON UCHUN ASOSIY MODELLARNI YUKLASH ---

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


# --- 1. FRONTEND SAHIFALARNI OCHISH YO'LLARI ---

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


# --- 2. FOYDALANUVCHILAR VA AVTORIZATSIYA (AUTH) ---

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

@app.get("/users/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user


# --- 3. DO'KON VA PERSONAJ KIYINTIRISH ---

@app.get("/shop-items")
def get_shop_items(db: Session = Depends(get_db)):
    return db.query(models.ShopItem).all()

@app.post("/buy-item/{item_id}")
def buy_item(item_id: int, user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi! Iltimos, tizimga qayta kiring.")

    item = db.query(models.ShopItem).filter(models.ShopItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Buyum topilmadi!")
    
    existing_inv = db.query(models.Inventory).filter(
        models.Inventory.user_id == user.id,
        models.Inventory.item_id == item_id
    ).first()
    
    # Allaqachon xarid qilingan bo'lsa, qayta pul yechmasdan kiyiladi
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


# --- 4. OSON STUDIO USLUBIDAGI LUG'AT TIZIMI (VIDEO + TO'PLAMLAR) ---

@app.get("/api/vocab/sets")
def get_vocab_sets():
    """Oson Studio kabi 6 ta to'plam ro'yxati"""
    return [
        {"set": 1, "title": "1-To'plam (A1 Boshlang'ich)", "words_count": 600, "lessons": 30, "is_locked": False, "badge": "Boshlash"},
        {"set": 2, "title": "2-To'plam (A2 Davomi)", "words_count": 600, "lessons": 30, "is_locked": True, "badge": "Qulflangan"},
        {"set": 3, "title": "3-To'plam (B1 O'rta)", "words_count": 600, "lessons": 30, "is_locked": True, "badge": "Qulflangan"},
        {"set": 4, "title": "4-To'plam (B2 Yuqori)", "words_count": 600, "lessons": 30, "is_locked": True, "badge": "Qulflangan"},
        {"set": 5, "title": "5-To'plam (C1 Professional)", "words_count": 600, "lessons": 30, "is_locked": True, "badge": "Qulflangan"},
        {"set": 6, "title": "6-To'plam (Oxford 5000)", "words_count": 600, "lessons": 30, "is_locked": True, "badge": "Qulflangan"},
    ]

@app.get("/api/vocab/lesson/{set_id}/{lesson_id}")
def get_lesson_words(set_id: int, lesson_id: int, db: Session = Depends(get_db)):
    """Tanlangan darsning so'zlari (video lavhalari bilan birga)"""
    words = db.query(models.VocabWord).filter(
        models.VocabWord.set_number == set_id,
        models.VocabWord.lesson_number == lesson_id
    ).all()
    
    # Agar bazada hali so'zlar bo'lmasa, dastur to'xtab qolmasligi uchun namunaviy video so'zlar qaytariladi
    if not words:
        return [
            {
                "id": 1, 
                "word": "Environment", 
                "translation": "Atrof-muhit", 
                "example": "We must protect the natural environment.", 
                "video_url": "https://assets.mixkit.co/videos/preview/mixkit-forest-stream-in-the-sunlight-529-large.mp4"
            },
            {
                "id": 2, 
                "word": "Challenge", 
                "translation": "Qiyinchilik / Sinov", 
                "example": "Learning English is a big challenge.", 
                "video_url": "https://assets.mixkit.co/videos/preview/mixkit-hands-holding-a-mountain-compass-41584-large.mp4"
            },
            {
                "id": 3, 
                "word": "Success", 
                "translation": "Muvaffaqiyat", 
                "example": "Hard work always leads to success.", 
                "video_url": "https://assets.mixkit.co/videos/preview/mixkit-excited-girl-celebrating-a-victory-42021-large.mp4"
            },
            {
                "id": 4, 
                "word": "Opportunity", 
                "translation": "Imkoniyat", 
                "example": "This is a great opportunity for you.", 
                "video_url": "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-city-traffic-at-night-42173-large.mp4"
            }
        ]
    
    result = []
    for w in words:
        result.append({
            "id": w.id,
            "word": w.word,
            "translation": w.translation,
            "example": w.example_sentence or "Misol gap mavjud emas",
            "video_url": w.video_url or "https://assets.mixkit.co/videos/preview/mixkit-forest-stream-in-the-sunlight-529-large.mp4"
        })
    return result

@app.get("/seed-vocab")
def seed_vocabulary(db: Session = Depends(get_db)):
    """Yangi VocabWord jadvaliga boshlang'ich video so'zlarni yuklash"""
    if db.query(models.VocabWord).count() > 0:
        return {"message": "Lug'at bazasi allaqachon to'ldirilgan! ✅"}

    words_to_seed = [
        models.VocabWord(
            word="Environment",
            translation="Atrof-muhit",
            example_sentence="We must protect the natural environment.",
            example_translation="Biz tabiiy atrof-muhitni asrashimiz kerak.",
            video_url="https://assets.mixkit.co/videos/preview/mixkit-forest-stream-in-the-sunlight-529-large.mp4",
            set_number=1,
            lesson_number=1,
            level="A1"
        ),
        models.VocabWord(
            word="Challenge",
            translation="Qiyinchilik / Sinov",
            example_sentence="Learning English is an exciting challenge.",
            example_translation="Ingliz tilini o'rganish hayajonli sinovdir.",
            video_url="https://assets.mixkit.co/videos/preview/mixkit-hands-holding-a-mountain-compass-41584-large.mp4",
            set_number=1,
            lesson_number=1,
            level="A1"
        ),
        models.VocabWord(
            word="Success",
            translation="Muvaffaqiyat",
            example_sentence="Hard work always leads to success.",
            example_translation="Mehnat doimo muvaffaqiyatga olib boradi.",
            video_url="https://assets.mixkit.co/videos/preview/mixkit-excited-girl-celebrating-a-victory-42021-large.mp4",
            set_number=1,
            lesson_number=1,
            level="A1"
        ),
        models.VocabWord(
            word="Opportunity",
            translation="Imkoniyat",
            example_sentence="Education gives you a great opportunity.",
            example_translation="Ta'lim sizga ajoyib imkoniyat beradi.",
            video_url="https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-city-traffic-at-night-42173-large.mp4",
            set_number=1,
            lesson_number=1,
            level="A1"
        )
    ]

    db.add_all(words_to_seed)
    db.commit()
    return {"message": "VocabWord jadvaliga namunaviy video so'zlar yuklandi! 🎉"}


# --- 5. DARSLAR VA TOPSHIRIQLARNI BAJARISH (TASKS) ---

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
    return {"status": "success", "message": "Vazifa bajarildi va bazaga saqlandi! ✅"}

@app.get("/api/status")
def api_status():
    return {"message": "IELTS Platform API ishga tushdi! May oyigacha to'xtamaymiz 🚀"}

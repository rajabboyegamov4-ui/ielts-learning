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


# --- STARTUP: DO'KON UCHUN BOSHLANG'ICH BUYUMLarni QO'SHISH ---
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    if db.query(models.ShopItem).count() == 0:
        default_items = [
            # Erkaklar uchun yuz va kiyimlar
            models.ShopItem(name="Klassik Yuz (Erkak)", item_type=models.ItemTypeEnum.hair, price=15000, is_rare=False),
            models.ShopItem(name="Stilist Soch & Yuz (Erkak)", item_type=models.ItemTypeEnum.hair, price=45000, is_rare=True),
            models.ShopItem(name="Qora Kostyum (Erkak)", item_type=models.ItemTypeEnum.clothes, price=50000, is_rare=False),
            models.ShopItem(name="Smoking (Erkak)", item_type=models.ItemTypeEnum.clothes, price=120000, is_rare=True),
            
            # Qizlar uchun yuz va kiyimlar
            models.ShopItem(name="Elegant Yuz (Qiz)", item_type=models.ItemTypeEnum.hair, price=15000, is_rare=False),
            models.ShopItem(name="Modulli Soch (Qiz)", item_type=models.ItemTypeEnum.hair, price=50000, is_rare=True),
            models.ShopItem(name="Kechki ko'ylak (Qiz)", item_type=models.ItemTypeEnum.clothes, price=60000, is_rare=False),
            models.ShopItem(name="Brend Ko'ylak (Qiz)", item_type=models.ItemTypeEnum.clothes, price=130000, is_rare=True),
            
            # Aksessuarlar
            models.ShopItem(name="Quyosh ko'zoynagi", item_type=models.ItemTypeEnum.accessory, price=25000, is_rare=False),
            models.ShopItem(name="Zargarlik taqinchog'i", item_type=models.ItemTypeEnum.accessory, price=80000, is_rare=True),
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

@app.get("/grammar", response_class=HTMLResponse)
def read_grammar(request: Request):
    return templates.TemplateResponse(request, "grammar.html")

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
    
    return {"message": "Muvaffaqiyatli kirdingiz!", "username": user.username, "balance": user.balance, "user_id": user.id}

# Parolni unutdim (Forgot Password) endpointi
@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Bu email bilan ro'yxatdan o'tgan foydalanuvchi topilmadi!")
    
    user.password_hash = security.get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "Parolingiz muvaffaqiyatli o'zgartirildi! Yangi parol bilan kirishingiz mumkin."}


# --- 3. DO'KON VA PERSONAJ (MARKET & WARDROBE) ENDPOINTLARI ---

@app.get("/shop-items")
def get_shop_items(db: Session = Depends(get_db)):
    return db.query(models.ShopItem).all()

@app.post("/buy-item/{item_id}")
def buy_item(item_id: int, user_id: int, db: Session = Depends(get_db)):
    # Hozirgi foydalanuvchini id orqali topamiz (Frontenddan user_id keladi yoki session orqali)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi!")

    item = db.query(models.ShopItem).filter(models.ShopItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Buyum topilmadi!")
    
    # Allaqachon sotib olinganligini tekshirish
    existing_inv = db.query(models.Inventory).filter(
        models.Inventory.user_id == user.id,
        models.Inventory.item_id == item_id
    ).first()
    
    if existing_inv:
        raise HTTPException(status_code=400, detail="Bu buyum allaqachon sotib olingan!")
    
    # Balans yetarliligini tekshirish
    if user.balance < item.price:
        raise HTTPException(status_code=400, detail="Balansingizda yetarli mablag' yo'q!")
    
    # Balansdan ayirish
    user.balance -= item.price
    
    # Tarixga yozish
    wallet_history = models.WalletHistory(
        user_id=user.id,
        amount=-item.price,
        reason=f"Sotib olindi: {item.name}"
    )
    db.add(wallet_history)
    
    # Omborga qo'shish
    new_inventory = models.Inventory(
        user_id=user.id,
        item_id=item_id,
        is_equipped=False
    )
    db.add(new_inventory)
    db.commit()
    
    return {"message": "Muvaffaqiyatli sotib olindi!", "new_balance": user.balance}


# --- 4. QOLGAN API ENDPOINTLAR ---

@app.get("/api/status")
def api_status():
    return {"message": "IELTS Platform API ishga tushdi! May oyigacha to'xtamaymiz 🚀"}

@app.get("/users/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user

@app.get("/vocabulary/")
def get_vocabulary(level: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.VocabularyWord)
    if level:
        query = query.filter(models.VocabularyWord.level == level)
    return query.all()

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

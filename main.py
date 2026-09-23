from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import date
from database import engine, get_db
import models, schemas, security

# Jadvallarni bazada avtomatik yaratish
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IELTS & AI Learning Platform API", version="1.0")

# HTML fayllar turgan papkani ulash
templates = Jinja2Templates(directory="templates")

# --- PYDANTIC SXEMALARI (Lug'at va Vazifalar uchun) ---
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


# --- 1. FRONTEND SAHIFALARNI OCHISH (Jinja2 orqali) ---

# Saytga kirganda birinchi chiqadigan sahifa - LOGIN / REGISTER
@app.get("/", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Tizimga kirgandan keyingi asosiy o'yin va o'qish paneli
@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/listening", response_class=HTMLResponse)
def read_listening(request: Request):
    return templates.TemplateResponse("listening.html", {"request": request})

@app.get("/speaking", response_class=HTMLResponse)
def read_speaking(request: Request):
    return templates.TemplateResponse("speaking.html", {"request": request})

@app.get("/reading", response_class=HTMLResponse)
def read_reading(request: Request):
    return templates.TemplateResponse("reading.html", {"request": request})

@app.get("/writing", response_class=HTMLResponse)
def read_writing(request: Request):
    return templates.TemplateResponse("writing.html", {"request": request})

@app.get("/grammar", response_class=HTMLResponse)
def read_grammar(request: Request):
    return templates.TemplateResponse("grammar.html", {"request": request})

@app.get("/exam", response_class=HTMLResponse)
def read_exam(request: Request):
    return templates.TemplateResponse("exam.html", {"request": request})


# --- 2. API ENDPOINTLAR (AUTH: Ro'yxatdan o'tish va Kirish) ---

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
    
    return {"message": "Muvaffaqiyatli kirdingiz!", "username": user.username, "balance": user.balance}


# --- 3. API ENDPOINTLAR (O'yin va Mashqlar) ---

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
def mark_task_done(task: TaskDoneUpdate, db:Session = Depends(get_db)):
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

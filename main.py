from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database import engine, get_db
import models
from pydantic import BaseModel
from datetime import date
import os

# Jadvallarni bazada avtomatik yaratish
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IELTS & AI Learning Platform API", version="1.0")

# --- PYDANTIC SXEMALARI (Ma'lumotlarni qabul qilish uchun) ---
class VocabCreate(BaseModel):
    word: str
    translation: str
    example_sentence: str | None = None
    level: str
    topic: str | None = None

class TaskDoneUpdate(BaseModel):
    user_id: int
    item_type: str # 'vocab', 'lesson', 'grammar' va h.k.
    item_id: int


# --- FRONTEND (HTML) SAHIFALARNI UZATISH UCHUN YORDAMCHI FUNKSIYA ---
def get_html_template(filename: str):
    file_path = f"templates/{filename}"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"<h1>{filename} sahifasi topilmadi! templates papkasini tekshiring.</h1>"


# --- 1. ASOSIY SAHIFALAR UCHUN ENDPOINTLAR ---

@app.get("/", response_class=HTMLResponse)
def read_frontend():
    return get_html_template("index.html")

@app.get("/listening", response_class=HTMLResponse)
def read_listening():
    return get_html_template("listening.html")

@app.get("/speaking", response_class=HTMLResponse)
def read_speaking():
    return get_html_template("speaking.html")

@app.get("/reading", response_class=HTMLResponse)
def read_reading():
    return get_html_template("reading.html")

@app.get("/writing", response_class=HTMLResponse)
def read_writing():
    return get_html_template("writing.html")

@app.get("/grammar", response_class=HTMLResponse)
def read_grammar():
    return get_html_template("grammar.html")

@app.get("/exam", response_class=HTMLResponse)
def read_exam():
    return get_html_template("exam.html")


# --- 2. API ENDPOINTLAR (Backend logikasi va ma'lumotlar bazasi) ---

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
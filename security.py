from passlib.context import CryptContext

# Parolni shifrlash uchun bcrypt konteksti
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    # Bcrypt cheklovi (72 bayt) uchun parolni qirqib olamiz
    password_truncated = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password_truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_truncated = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(password_truncated, hashed_password)

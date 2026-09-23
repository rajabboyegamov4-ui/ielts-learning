from passlib.context import CryptContext

# Bcrypt o'rniga xavfsiz va xatolarsiz pbkdf2_sha256 kontekstiga o'tamiz
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

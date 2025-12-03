from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    hash = pwd_context.hash("password123")
    print(f"Hash created successfully: {hash}")
except Exception as e:
    print(f"Error hashing: {e}")

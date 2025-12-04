"""Initialize database directly without config module"""
from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import uuid

# Create engine directly
engine = create_engine('sqlite:///./dev.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define User model
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

# Create tables
Base.metadata.create_all(bind=engine)
print("✓ Database tables created")

# Create test user
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()
try:
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == 'testuser').first()
    if existing_user:
        print("✓ Test user 'testuser' already exists")
    else:
        user = User(
            id=str(uuid.uuid4()),
            username='testuser',
            email='testuser@example.com',
            hashed_password=pwd_context.hash('password123'),
            is_active=True
        )
        db.add(user)
        db.commit()
        print("✓ Test user created: testuser / password123")
finally:
    db.close()

print("\n✓ Database initialization complete!")
print("You can now login with: testuser / password123")

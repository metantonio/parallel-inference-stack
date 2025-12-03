from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.username == "testuser").first()
        if user:
            print("User 'testuser' already exists.")
            return

        hashed_password = get_password_hash("password123")
        new_user = User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        print("User 'testuser' created successfully.")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()

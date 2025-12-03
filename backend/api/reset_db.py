import asyncio
import logging
from sqlalchemy import text
from app.database import engine, Base
from app.config import settings
import alembic.config
import os
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_alembic_setup():
    """
    Ensures that Alembic configuration and migrations directory exist.
    Creates them if they don't exist.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_cfg_path = os.path.join(current_dir, "alembic.ini")
    migrations_dir = os.path.join(current_dir, "migrations")
    versions_dir = os.path.join(migrations_dir, "versions")
    
    # Check if alembic.ini exists
    if not os.path.exists(alembic_cfg_path):
        logger.warning("alembic.ini not found. Initializing Alembic...")
        try:
            # Initialize Alembic
            subprocess.run(["alembic", "init", "migrations"], cwd=current_dir, check=True)
            logger.info("Alembic initialized successfully.")
            
            # Update alembic.ini with correct database URL
            with open(alembic_cfg_path, 'r') as f:
                content = f.read()
            
            # Replace the sqlalchemy.url line
            content = content.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                f"sqlalchemy.url = {settings.DATABASE_URL}"
            )
            
            with open(alembic_cfg_path, 'w') as f:
                f.write(content)
            
            logger.info("Updated alembic.ini with database URL.")
        except Exception as e:
            logger.error(f"Error initializing Alembic: {e}")
            raise
    
    # Check if migrations/versions directory exists
    if not os.path.exists(versions_dir):
        logger.warning("migrations/versions directory not found. Creating it...")
        os.makedirs(versions_dir, exist_ok=True)
        logger.info("Created migrations/versions directory.")
    
    return alembic_cfg_path

def reset_database():
    """
    Resets the database by dropping all tables and running migrations.
    WARNING: This will delete all data!
    """
    logger.warning("Starting database reset. ALL DATA WILL BE LOST.")
    
    # 0. Ensure Alembic is set up
    try:
        alembic_cfg_path = ensure_alembic_setup()
    except Exception as e:
        logger.error(f"Failed to set up Alembic: {e}")
        return
    
    # 1. Drop all tables
    logger.info("Dropping all tables...")
    try:
        # Reflect all tables
        Base.metadata.reflect(bind=engine)
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Also drop alembic_version table to ensure clean slate
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.commit()
            
        logger.info("All tables dropped successfully.")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return

    # 2. Run Migrations
    logger.info("Running migrations...")
    try:
        alembic_args = [
            "-c", alembic_cfg_path,
            "upgrade", "head"
        ]
        
        alembic.config.main(argv=alembic_args)
        logger.info("Migrations applied successfully.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")

if __name__ == "__main__":
    # Confirm with user
    print("WARNING: This will DELETE ALL DATA in the database.")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() == "yes":
        reset_database()
        print("Database reset complete.")
    else:
        print("Operation cancelled.")

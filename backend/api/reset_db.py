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
    env_py_path = os.path.join(migrations_dir, "env.py")
    script_mako_path = os.path.join(migrations_dir, "script.py.mako")
    
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
    
    # Check if migrations directory exists
    if not os.path.exists(migrations_dir):
        logger.warning("migrations directory not found. Creating it...")
        os.makedirs(migrations_dir, exist_ok=True)
        logger.info("Created migrations directory.")
    
    # Check if migrations/versions directory exists
    if not os.path.exists(versions_dir):
        logger.warning("migrations/versions directory not found. Creating it...")
        os.makedirs(versions_dir, exist_ok=True)
        logger.info("Created migrations/versions directory.")
    
    # Check if env.py exists
    if not os.path.exists(env_py_path):
        logger.warning("migrations/env.py not found. Creating it...")
        env_py_content = '''from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.database import Base
from app.models import *  # Import all models to register them
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
from app.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        with open(env_py_path, 'w') as f:
            f.write(env_py_content)
        logger.info("Created migrations/env.py")
    
    # Check if script.py.mako exists
    if not os.path.exists(script_mako_path):
        logger.warning("migrations/script.py.mako not found. Creating it...")
        script_mako_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
        with open(script_mako_path, 'w') as f:
            f.write(script_mako_content)
        logger.info("Created migrations/script.py.mako")
    
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

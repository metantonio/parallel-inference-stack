# Database Operations Guide

This guide explains how to manage the database for the AI Inference System.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Running Migrations](#running-migrations)
- [Creating New Migrations](#creating-new-migrations)
- [Resetting the Database](#resetting-the-database)
- [Managing Users](#managing-users)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)

## Initial Setup

### 1. Create the Database

The database is automatically created when you run `docker-compose up`. PostgreSQL will be available at:
- **Host**: `postgres` (inside Docker network) or `localhost` (from host machine)
- **Port**: `5432`
- **Database**: `inference`
- **User**: `postgres`
- **Password**: `postgres` (change in production!)

### 2. Run Initial Migrations

After starting the containers, run migrations to create the database schema:

```bash
# Enter the API container
docker exec -it ai-inference-api-1 bash

# Run migrations
alembic upgrade head
```

This will create the `users` and `inference_requests` tables.

## Running Migrations

### Apply All Pending Migrations

```bash
docker exec -it ai-inference-api-1 bash
alembic upgrade head
```

### Apply Specific Migration

```bash
docker exec -it ai-inference-api-1 bash
alembic upgrade <revision_id>
```

### Rollback One Migration

```bash
docker exec -it ai-inference-api-1 bash
alembic downgrade -1
```

### Rollback to Specific Revision

```bash
docker exec -it ai-inference-api-1 bash
alembic downgrade <revision_id>
```

### Check Current Migration Status

```bash
docker exec -it ai-inference-api-1 bash
alembic current
```

### View Migration History

```bash
docker exec -it ai-inference-api-1 bash
alembic history
```

## Creating New Migrations

### Auto-generate Migration from Model Changes

1. **Modify your models** in `backend/api/app/models.py`

2. **Generate migration**:
```bash
docker exec -it ai-inference-api-1 bash
alembic revision --autogenerate -m "description of changes"
```

3. **Review the generated file** in `backend/api/migrations/versions/`

4. **Apply the migration**:
```bash
alembic upgrade head
```

5. **Commit the migration file** to git:
```bash
git add backend/api/migrations/versions/<new_file>.py
git commit -m "Add migration: description of changes"
```

### Create Empty Migration (Manual)

```bash
docker exec -it ai-inference-api-1 bash
alembic revision -m "description"
```

Then edit the generated file in `migrations/versions/` to add your custom SQL or operations.

## Resetting the Database

### Complete Reset (Deletes All Data!)

Use the provided reset script:

```bash
docker exec -it ai-inference-api-1 bash
python reset_db.py
```

This will:
1. Drop all tables
2. Drop the `alembic_version` table
3. Re-run all migrations from scratch
4. Create a clean database schema

**⚠️ WARNING**: This deletes ALL data including users and inference history!

### Manual Reset

If you prefer to do it manually:

```bash
docker exec -it ai-inference-api-1 bash

# Drop all tables
psql -h postgres -U postgres -d inference -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
alembic upgrade head
```

## Managing Users

### Create Initial Admin User

Since we don't have a registration endpoint yet, you can create users directly in the database:

```bash
docker exec -it ai-inference-api-1 bash
python -c "
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash
import uuid

db = SessionLocal()
user = User(
    id=str(uuid.uuid4()),
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('your-secure-password'),
    is_active=True
)
db.add(user)
db.commit()
print(f'User created: {user.username}')
"
```

### List All Users

```bash
docker exec -it ai-inference-api-1 bash
python -c "
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
users = db.query(User).all()
for user in users:
    print(f'ID: {user.id}, Username: {user.username}, Email: {user.email}, Active: {user.is_active}')
"
```

### Delete a User

```bash
docker exec -it ai-inference-api-1 bash
python -c "
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.username == 'username_to_delete').first()
if user:
    db.delete(user)
    db.commit()
    print('User deleted')
else:
    print('User not found')
"
```

## Common Operations

### Connect to PostgreSQL Directly

```bash
docker exec -it ai-inference-postgres psql -U postgres -d inference
```

Useful SQL commands:
```sql
-- List all tables
\dt

-- Describe a table
\d users

-- Count users
SELECT COUNT(*) FROM users;

-- View all users
SELECT id, username, email, is_active FROM users;

-- View migration history
SELECT * FROM alembic_version;

-- Exit
\q
```

### Backup Database

```bash
# Backup to file
docker exec ai-inference-postgres pg_dump -U postgres inference > backup.sql

# Backup with compression
docker exec ai-inference-postgres pg_dump -U postgres inference | gzip > backup.sql.gz
```

### Restore Database

```bash
# From SQL file
docker exec -i ai-inference-postgres psql -U postgres inference < backup.sql

# From compressed file
gunzip -c backup.sql.gz | docker exec -i ai-inference-postgres psql -U postgres inference
```

### View Database Size

```bash
docker exec -it ai-inference-postgres psql -U postgres -d inference -c "
SELECT 
    pg_size_pretty(pg_database_size('inference')) as db_size,
    pg_size_pretty(pg_total_relation_size('users')) as users_table_size,
    pg_size_pretty(pg_total_relation_size('inference_requests')) as requests_table_size;
"
```

## Troubleshooting

### Migration Conflicts

If you get "target database is not up to date":

```bash
docker exec -it ai-inference-api-1 bash
alembic stamp head
```

### Alembic Configuration Missing

If `alembic.ini` or migration files are missing, run:

```bash
docker exec -it ai-inference-api-1 bash
python reset_db.py
```

This will recreate all necessary Alembic configuration files.

### Database Connection Issues

Check if PostgreSQL is running:

```bash
docker ps | grep postgres
```

Test connection:

```bash
docker exec -it ai-inference-api-1 bash
python -c "from app.database import engine; print(engine.connect())"
```

### Reset Alembic Version Table

If migrations are out of sync:

```bash
docker exec -it ai-inference-postgres psql -U postgres -d inference -c "DROP TABLE alembic_version;"
docker exec -it ai-inference-api-1 bash
alembic stamp head
```

## Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Test migrations on a development database** before production
3. **Backup production database** before running migrations
4. **Commit migration files to git** immediately after creating them
5. **Never edit applied migrations** - create a new migration instead
6. **Use descriptive migration messages** for easy tracking
7. **Keep migrations small and focused** - one logical change per migration

## Production Considerations

For production deployments:

1. **Change default passwords** in `.env`:
   ```bash
   DATABASE_URL=postgresql://secure_user:secure_password@postgres:5432/inference
   ```

2. **Run migrations as part of deployment**:
   ```bash
   alembic upgrade head
   ```

3. **Use database backups** before migrations:
   ```bash
   pg_dump -U postgres inference > pre_migration_backup.sql
   ```

4. **Monitor migration execution** for long-running operations

5. **Consider downtime** for breaking schema changes

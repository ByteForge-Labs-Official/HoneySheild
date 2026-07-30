"""
seed_admin.py — Create the admin user directly in the database.
Run from the backend/ folder:
    python seed_admin.py
"""
import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Load settings from .env ──────────────────────────────────────────────────
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import Base

ADMIN_EMAIL    = "admin@honeynet.local"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@1234!"
ADMIN_FULLNAME = "Admin"

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)

    # Ensure all tables exist (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as session:
        from sqlalchemy import text

        # Check if admin already exists
        result = await session.execute(
            text("SELECT id FROM users WHERE username = :u"),
            {"u": ADMIN_USERNAME},
        )
        row = result.fetchone()
        if row:
            print(f"[SKIP] User '{ADMIN_USERNAME}' already exists (id={row[0]})")
            await engine.dispose()
            return

        # Insert admin user
        await session.execute(
            text("""
                INSERT INTO users
                    (id, email, username, full_name, hashed_password,
                     is_active, is_superuser, roles, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :email, :username, :full_name, :hashed_password,
                     true, true, ARRAY['admin','analyst'], now(), now())
            """),
            {
                "email":           ADMIN_EMAIL,
                "username":        ADMIN_USERNAME,
                "full_name":       ADMIN_FULLNAME,
                "hashed_password": hash_password(ADMIN_PASSWORD),
            },
        )
        await session.commit()
        print("=" * 50)
        print("[OK] Admin user created!")
        print(f"     Username : {ADMIN_USERNAME}")
        print(f"     Password : {ADMIN_PASSWORD}")
        print(f"     Email    : {ADMIN_EMAIL}")
        print("=" * 50)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())

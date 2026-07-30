"""Bootstrap script — runs migrations, creates the initial admin, imports dashboards."""
from __future__ import annotations

import asyncio
import secrets

import structlog

from app.core.security.hashing import hash_password
from app.core.config.settings import get_settings
from app.db.session import async_session, engine
from app.models.user import User
from app.services.grafana.client import import_dashboards
from app.services.elk.bootstrap import create_ilm_policy, create_index_template

logger = structlog.get_logger()


async def bootstrap_async() -> None:
    s = get_settings()
    logger.info("bootstrap.start", env=s.app_env)

    # 1. Migrations (delegated to alembic CLI in the deployment pipeline too)
    from alembic import command
    from alembic.config import Config
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    # 2. Seed an initial admin if not present
    async with async_session() as db:
        admin_email = "admin@honeynet.local"
        user = await db.get(User, admin_email)
        if not user:
            user = User(
                email=admin_email,
                username="admin",
                password_hash=hash_password(secrets.token_urlsafe(24)),
                is_admin=True,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            logger.info("bootstrap.admin.created", email=admin_email,
                        initial_password="<printed-once>")
            print(f"ADMIN initial password (rotate now): {user.password_hash}")
        else:
            logger.info("bootstrap.admin.exists", email=admin_email)

    # 3. Grafana / Kibana — best-effort; they may not be reachable yet
    try:
        await import_dashboards("observability/grafana/dashboards")
    except Exception as e:        # noqa: BLE001
        logger.warning("bootstrap.grafana.deferred", error=str(e))
    try:
        await create_ilm_policy()
        await create_index_template()
    except Exception as e:        # noqa: BLE001
        logger.warning("bootstrap.elk.deferred", error=str(e))

    await engine.dispose()
    logger.info("bootstrap.done")

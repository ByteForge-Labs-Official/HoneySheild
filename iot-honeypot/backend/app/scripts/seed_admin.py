"""Seed an initial admin user."""
from __future__ import annotations

import asyncio

import typer
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import SessionMaker

cli = typer.Typer()


@cli.command()
def seed_admin(
    email: str = typer.Option(...),
    username: str = typer.Option(...),
    password: str = typer.Option(...),
    full_name: str = typer.Option("Honeynet Admin"),
) -> None:
    """Idempotently create or update the admin user."""
    asyncio.run(_seed(email, username, password, full_name))


async def _seed(email: str, username: str, password: str, full_name: str) -> None:
    s = get_settings()
    async with SessionMaker() as session:
        stmt = select(User).where(User.email == email.lower())
        user = (await session.execute(stmt)).scalar_one_or_none()
        if user is None:
            user = User(
                email=email.lower(),
                username=username,
                full_name=full_name,
                hashed_password=hash_password(password),
                roles=["admin", "analyst"],
                is_superuser=True,
            )
            session.add(user)
        else:
            user.hashed_password = hash_password(password)
            user.roles = ["admin", "analyst"]
            user.is_superuser = True
        await session.commit()
    typer.echo(f"admin user '{username}' ({email}) ensured.")


if __name__ == "__main__":
    cli()
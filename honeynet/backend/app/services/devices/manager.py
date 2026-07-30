"""Device management service — CRUD + MQTT control commands."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.sanitize import clean_value
from app.integrations.mqtt.publisher import publish
from app.models.device import Device
from app.schemas.devices import DeviceCreate, DeviceUpdate


async def list_devices(db: AsyncSession) -> Sequence[Device]:
    res = await db.execute(select(Device).order_by(Device.created_at.desc()))
    return res.scalars().all()


async def get_device(db: AsyncSession, device_id: UUID) -> Device | None:
    return await db.get(Device, device_id)


async def create_device(db: AsyncSession, payload: DeviceCreate) -> Device:
    device = Device(
        kind=payload.kind,
        vendor=payload.vendor,
        model=payload.model,
        firmware_version=payload.firmware_version,
        bait_ports=payload.bait_ports,
        status="online",
        metadata_json=payload.metadata,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def update_device(db: AsyncSession, device: Device, payload: DeviceUpdate) -> Device:
    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "metadata":
            device.metadata_json = value
        elif hasattr(device, field):
            setattr(device, field, value)
    await db.commit()
    await db.refresh(device)
    return device


async def send_control(device: Device, topic: str, body: dict, retain: bool = False) -> None:
    """Push an MQTT command to the bait device (operator action, not attacker)."""
    safe_topic = clean_value(topic, cap=255)
    await publish(safe_topic, body, qos=1, retain=retain, username="operator")
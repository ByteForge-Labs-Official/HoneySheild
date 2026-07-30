"""Device management — list/create/update + MQTT control."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DBSession
from app.models.device import Device
from app.schemas.devices import (
    DeviceControl, DeviceCreate, DeviceOut, DeviceUpdate,
)
from app.services.devices.manager import (
    create_device, get_device, list_devices, send_control, update_device,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=list[DeviceOut])
async def _list(_: CurrentUser, db: DBSession):
    return await list_devices(db)


@router.post("/", response_model=DeviceOut, status_code=201)
async def _create(body: DeviceCreate, _: CurrentUser, db: DBSession):
    return await create_device(db, body)


@router.get("/{device_id}", response_model=DeviceOut)
async def _get(device_id: UUID, _: CurrentUser, db: DBSession):
    d = await get_device(db, device_id)
    if not d:
        raise HTTPException(404, "Not found")
    return d


@router.patch("/{device_id}", response_model=DeviceOut)
async def _update(device_id: UUID, body: DeviceUpdate, _: CurrentUser, db: DBSession):
    d = await get_device(db, device_id)
    if not d:
        raise HTTPException(404, "Not found")
    return await update_device(db, d, body)


@router.post("/{device_id}/control", status_code=202)
async def _control(device_id: UUID, body: DeviceControl, _: CurrentUser, db: DBSession):
    d = await get_device(db, device_id)
    if not d:
        raise HTTPException(404, "Not found")
    await send_control(d, body.topic, body.payload, retain=body.retain)
    return {"queued": True}
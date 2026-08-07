# DEPLOYMENT.md — Deployment & Operations Specification

This document provides step-by-step instructions for deploying, configuring, and operating the Smart State Power Distribution Board (KSPDB) from scratch.

---

## 1. System Requirements & Prerequisites

Ensure the deployment machine meets the following version specifications:

| Component | Minimum Required Version | Recommended Version |
| :--- | :--- | :--- |
| **Docker Engine** | `v20.10.0` | `v24.0+` |
| **Docker Compose** | `v2.0.0` | `v2.20+` |
| **Python** (for manual setup) | `v3.11.0` | `v3.12.2` |
| **Node.js** (for manual setup) | `v18.0.0` | `v20.11.0` |

---

## 2. One-Command Setup (Docker Compose)

Execute these copy-pasteable commands in order:

```bash
# Step 1: Clone the repository
git clone https://github.com/MuhammedFarhanSyed/smart-State-Power-Distribution-Board.git
cd smart-State-Power-Distribution-Board

# Step 2: Copy the environment configuration file
cp .env.example .env

# Step 3: Launch containerized services
docker compose up --build
```

---

## 3. Environment Variables Reference (`.env`)

| Variable Name | Description | Required? | Safe Default |
| :--- | :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Django settings module path | Yes | `config.settings` |
| `SECRET_KEY` | Cryptographic key for Django sessions | Yes | `development-only-secret-key` |
| `DEBUG` | Django debug mode boolean | Yes | `True` (Development) / `False` (Prod) |
| `ALLOWED_HOSTS` | Allowed hostnames for HTTP request header | Yes | `*` |
| `PORT` | Backend HTTP binding port | No | `8000` |
| `DATABASE_ENGINE` | Database backend engine | Yes | `django.db.backends.sqlite3` |
| `DATABASE_NAME` | Database filename or DB name | Yes | `db.sqlite3` |
| `CONTROL_ROOM_POLL_INTERVAL` | Frontend UI refresh interval (seconds) | No | `4` |

---

## 4. Verifying Deployment Success

After launching `docker compose up --build`, verify the deployment:

1. **Backend Health Endpoint**:
   ```bash
   curl -I http://localhost:8000/api/health/
   ```
   *Expected Response*: `HTTP/1.1 200 OK`, JSON body: `{"status": "ok"}`.

2. **Database Seeding Verification**:
   ```bash
   curl http://localhost:8000/api/incidents/
   ```
   *Expected Response*: `HTTP/200 OK`, JSON array `[]` or active seeded tickets.

3. **Frontend Control Room Console**:
   Open [`http://localhost:5173`](http://localhost:5173) in your browser. You should see the **Karnataka Distribution Console** header with active tab navigation.

---

## 5. Troubleshooting & Failure Modes Matrix

This section documents actual failure modes encountered during development and containerization, including symptoms and exact fixes.

### **Failure Mode 1: Port 8000 or 5173 Conflict**
- **Symptom**: `Error response from daemon: driver failed programming external connectivity on endpoint: Bind for 0.0.0.0:8000 failed: port is already allocated`.
- **Root Cause**: A local instance of Django, Vite, or another service is occupying port 8000 or 5173.
- **Fix**:
  ```bash
  # Windows PowerShell:
  Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
  Stop-Process -Id (Get-NetTCPConnection -LocalPort 5173).OwningProcess -Force

  # Linux/macOS:
  sudo kill -9 $(lsof -t -i:8000)
  sudo kill -9 $(lsof -t -i:5173)
  ```

### **Failure Mode 2: Database Migrations Racing Startup**
- **Symptom**: Backend container crashes with `sqlite3.OperationalError: no such table: network_pole`.
- **Root Cause**: Backend application launched before Django migrations finished executing.
- **Fix**: The `Dockerfile` CMD chain explicitly sequences migrations before server startup:
  ```dockerfile
  CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_network && python manage.py runserver 0.0.0.0:8000"]
  ```

### **Failure Mode 3: ARM64 (Apple Silicon M1/M2/M3) vs x86_64 Compatibility**
- **Symptom**: `WARNING: The requested image's platform (linux/amd64) does not match the detected host platform`.
- **Root Cause**: Docker base image specified an explicit architecture binary.
- **Fix**: Using `python:3.12-slim` and `node:20-alpine` without explicit platform flags allows Docker to pull native multi-arch images automatically.

### **Failure Mode 4: Free-Tier Container Memory Limits (OOM Kills)**
- **Symptom**: Container exits abruptly with `Out of memory: Kill process` (Exit code 137).
- **Root Cause**: In-memory telemetry processing or excessive logging exceeding 512 MB RAM limits.
- **Fix**: Added `--no-cache-dir` to `pip install` in `Dockerfile`, optimized `select_related()` query caching in Django to reduce memory allocation per request under 64 MB.

### **Failure Mode 5: CORS Headers Blocking Direct API Access**
- **Symptom**: Browser console logs `Access to fetch at 'http://localhost:8000/api/' from origin 'http://localhost:5173' has been blocked by CORS policy`.
- **Root Cause**: Accessing backend port directly from different origin port without CORS headers.
- **Fix**: All frontend requests are routed through Nginx / Vite reverse proxy (`/api` $\rightarrow$ `http://backend:8000/api`), bypassing cross-origin restrictions entirely.

### **Failure Mode 6: Cold-Start SQLite Lock Timeouts**
- **Symptom**: `django.db.utils.OperationalError: database is locked`.
- **Root Cause**: Concurrent telemetry requests writing to SQLite simultaneously.
- **Fix**: Wrapped telemetry ingestion and localization inside atomic database transactions (`@transaction.atomic`), reducing lock write duration to $< 4\text{ ms}$.

---

## 6. How to Reset to a Clean State

To reset the database, purge active incidents, and re-energize all 1,200 network poles:

```bash
# Option A: Reset via Django Management Command
python -c "import os, django; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup(); from incidents.models import Incident, IncidentPole, TelemetryEvent; from network.models import Pole, Device; Pole.objects.all().update(is_energized=True); Device.objects.all().update(is_online=True); IncidentPole.objects.all().delete(); Incident.objects.all().delete(); TelemetryEvent.objects.all().delete(); print('Clean database ready!')"

# Option B: Complete Docker Volume Wipe
docker compose down -v
docker compose up --build
```

# KSPDB Deployment & Operations Guide

This guide describes how to deploy, configure, and troubleshoot the Smart State Power Distribution Board (KSPDB) stack locally and in production containerized environments.

---

## 1. System Requirements & Prerequisites

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Ports Required**:
  - Port `8000`: Backend Django REST API
  - Port `5173` (or `80`): Frontend React Control Room UI

---

## 2. One-Command Setup (Docker Compose)

Clone the repository and launch the containerized stack:

```bash
# 1. Clone repository
git clone <repository-url>
cd smart-State-Power-Distribution-Board

# 2. Start services (Backend + Database Seed + Frontend)
docker compose up --build
```

### **Startup Sequence Executed Automatically:**
1. Docker builds the Python 3.12 container for `backend` and installs dependencies.
2. Django applies database migrations (`python manage.py migrate`).
3. Management command `seed_network` populates 1,200 poles, 15 transformers, and 3 feeders.
4. Django REST server starts listening on `0.0.0.0:8000`.
5. Multi-stage Docker build compiles the Vite React bundle and starts Nginx on port `5173`.

---

## 3. Verifying the Deployment

- **Control Room UI**: Open `http://localhost:5173` in your browser.
- **Backend Health Check**:
  ```bash
  curl http://localhost:8000/api/health/
  # Expected Response: {"status": "ok"}
  ```
- **Incidents Feed API**:
  ```bash
  curl http://localhost:8000/api/incidents/
  ```

---

## 4. Manual Local Development (Without Docker)

### **Backend Setup (Python 3.11/3.12)**

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_network
python manage.py runserver 8000
```

### **Frontend Setup (Node.js 20+)**

```bash
cd frontend
npm install
npm run dev
```

---

## 5. Troubleshooting Common Production Issues

### **Issue 1: Port 8000 or 5173 already in use**
- **Symptom**: `bind: address already in use` error on startup.
- **Fix**: Stop existing local Python or Vite dev server instances:
  ```bash
  # Windows PowerShell:
  Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
  ```

### **Issue 2: Database Locked / SQLite Permissions**
- **Symptom**: `sqlite3.OperationalError: attempt to write a readonly database`.
- **Fix**: Ensure the container user has write permissions to the `./backend` volume folder, or reset `db.sqlite3`.

### **Issue 3: CORS or Proxy Connection Failures**
- **Symptom**: Browser console logs `Failed to fetch` or `Proxy error`.
- **Fix**: Ensure `vite.config.js` or `nginx.conf` proxies `/api` requests to `http://backend:8000`.

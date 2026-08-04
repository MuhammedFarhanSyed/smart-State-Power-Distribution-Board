# Deployment & Troubleshooting Guide

## 1. Prerequisites
- Docker Engine $\ge 24.0$ & Docker Compose $\ge 2.20$
- Python $\ge 3.11$ (for local non-containerized testing)
- Node.js $\ge 20$ (for local frontend development)

---

## 2. One-Command Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd smart-State-Power-Distribution-Board

# 2. Start complete containerized stack
docker compose up --build
```

---

## 3. Environment Variables (`.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `django-insecure-kspdb...` | Django secret key |
| `DEBUG` | `True` | Debug flag |
| `DB_ENGINE` | `django.db.backends.mysql` | Database engine |
| `DB_NAME` | `kspdb_fault_db` | MySQL database name |
| `DB_USER` | `kspdb_user` | MySQL username |
| `DB_PASSWORD` | `kspdb_password` | MySQL password |
| `DB_HOST` | `db` | Database host container |
| `DB_PORT` | `3306` | Database port |
| `AI_PROVIDER` | `mock` | AI provider (`mock`, `openai`, `groq`, `ollama`) |
| `AI_API_KEY` | `""` | API key for external LLM provider |

---

## 4. Deployment Troubleshooting Matrix

| Symptom | Cause | Solution / Fix |
| :--- | :--- | :--- |
| **Port Conflict (`3306` or `8000` in use)** | Local MySQL/Django already running on host | Stop local MySQL service (`sudo service mysql stop`) or change port mapping in `docker-compose.yml`. |
| **Database Connection Refused on boot** | MySQL container taking longer to initialize | `entrypoint.sh` includes `netcat` wait loop checking `db:3306` health status before executing migrations. |
| **ARM64 (Apple Silicon) image build error** | Native MySQL 8.0 architecture mismatch | `docker-compose.yml` uses official `mysql:8.0` multi-arch image compatible with ARM64 & x86_64. |
| **Free-Tier Cold Start Delay** | Public hosting (Render/Railway) spinning up from sleep | Documented cold start delay (~30s). Retry request after initial wake-up. |
| **CORS Error on API Call** | Frontend requesting different origin | Django includes CORS headers configuration for production domains. |

---

## 5. Clean System Reset

To reset the database, purge synthetic data, and re-seed from scratch:

```bash
docker compose down -v
docker compose up --build
```

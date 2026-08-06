# Smart State Power Distribution Board (KSPDB) — Power Outage Console

An intelligent, real-time power outage detection, fault localization, and operator control-room system built for Karnataka distribution board networks.

---

## Overview

KSPDB converts noisy telemetry signals from utility pole IoT sensors into single, high-confidence, actionable outage tickets. Instead of overwhelming control-room staff with hundreds of individual pole failure alerts, the deterministic localization engine pinpoints line breaks (spans), transformer failures, or feeder outages, tracks field crew assignments, and automatically verifies physical restoration via incoming telemetry.

---

## Key Features

- **Telemetry Ingestion & Deduplication**: High-throughput REST API endpoint (`POST /api/telemetry/`) accepting sensor events (`power_lost`, `power_restored`, `heartbeat`, `boot`). Uses per-device sequence numbers (`seq`) to ignore duplicates and retries.
- **Deterministic Fault Localization**:
  - **Span Fault (Line Break)**: Identifies live-to-dark boundaries on radial tree graphs (High Confidence).
  - **Transformer Fault**: Triggered when 100% of telemetry-monitored poles under a DT lose power (Medium Confidence).
  - **Feeder Outage**: Triggered when all poles across a feeder go dark (Medium Confidence).
  - **60% Missing Topology Degradation**: Gracefully falls back to a DT-level ticket (Low Confidence) when pole parent links are unavailable, avoiding false guesses.
- **Strict Ticket State Machine**:
  `DETECTED` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `CREW_ASSIGNED` $\rightarrow$ `REPAIR_REPORTED` $\rightarrow$ `VERIFIED` $\rightarrow$ `CLOSED`.
- **Telemetry-Driven Verification**: Closing tickets requires physical restoration telemetry confirming affected poles are energized again.
- **Operator Dashboard & Fault Simulator UI**: Interactive React dashboard providing real-time feed updates, crew workflow controls, and an interactive fault injection panel.

---

## Repository Documentation Index

| File | Description |
| :--- | :--- |
| **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** | System architecture, schemas, localization algorithms, missing topology strategy, and noise handling. |
| **[`DEPLOYMENT.md`](./DEPLOYMENT.md)** | Prerequisites, local Docker setup commands, environment variables, Nginx proxying, and troubleshooting guide. |
| **[`DECISIONS.md`](./DECISIONS.md)** | Key technical choices, rejected alternatives (e.g. Polling vs WebSockets), known trade-offs, and future roadmap. |
| **[`AI-WORKFLOW.md`](./AI-WORKFLOW.md)** | Transparent documentation of AI tool usage, code percentages, verified outputs, and corrections made. |

---

## Quick Start (Docker Compose)

Launch the entire stack (Backend + Database Seeding + Frontend) with a single command:

```bash
docker compose up --build
```

- **Control Room Dashboard**: Open `http://localhost:5173`
- **Backend API Health Check**: `http://localhost:8000/api/health/`

---

## System Architecture

```
                       ┌─────────────────────────┐
                       │   Control Room UI       │
                       │   React + Tailwind      │
                       └────────────┬────────────┘
                                    │
                       HTTP Polling / REST API
                                    │
                       ┌────────────▼────────────┐
                       │   Django REST Backend   │
                       │  Ingestion & Engine     │
                       └────────────┬────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │   SQLite Database       │
                       │   Seeded Network Data   │
                       └─────────────────────────┘
```

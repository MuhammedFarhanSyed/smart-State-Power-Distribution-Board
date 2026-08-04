# Karnataka ESCOM — Intelligent LT Fault Localization Platform

> **AI Product Engineer Internship Assignment Submission**  
> **Karnataka State Power Distribution Board (Fictional ESCOM Model)**

An automated, real-time outage detection and fault localization platform designed for low-tension (LT) radial electrical distribution networks. It ingests noisy IoT telemetry from ~34,900 pole sensors, deterministically localizes snapped wire spans ($P_{\text{live}} \to P_{\text{dark}}$), suppresses false alarms (load shedding & dead sensors), auto-verifies ticket resolution via telemetry, and provides a 2 a.m. non-engineer operator console with LLM decision support.

---

## 🚀 Quick Start (One Command)

Bring up the entire production stack (MySQL 8.0, Django REST Backend, React Operator Dashboard, auto-migrations, and synthetic network seeding):

```bash
git clone <repository-url>
cd smart-State-Power-Distribution-Board
docker compose up
```

- **React Operator Dashboard**: `http://localhost:3000`
- **Django REST API**: `http://localhost:8000/api/`
- **Live Demo Video**: `[Demo Video Link]`
- **Live Public Deployment**: `[Live Public URL]`

---

## 🎬 5-Step Live Demo Walkthrough Scenario

You can evaluate the complete end-to-end fault detection, localization, ticketing, repair, auto-verification, and AI summary workflow using the built-in simulator:

1. **Load Electrical Network**:
   - Open `http://localhost:3000` and click the **Fault Simulator** tab.
   - Click **Load Network Tree** (loads DT `D-0112` and its 70 LT poles).

2. **Inject Wire Span Break**:
   - In the Simulator Panel under **Inject Span Wire Break**, select From Pole `P-024431` and To Pole `P-024432`.
   - Click **Inject Wire Span Break**.
   - *Under the hood*: Telemetry packets flow through `POST /api/telemetry/`, sequence deduplication evaluates the packets, and `BoundaryDetector` pinpoints span `P-024431 -> P-024432`.

3. **Verify Incident Creation & Localization**:
   - Switch to the **Dashboard** tab.
   - Observe **1 single incident ticket** created (not 40 alerts!) with **100% confidence audit** and exact GPS navigation coordinates. The broken span is highlighted in pulsing red on the Leaflet Map.

4. **Operator Workflow & AI Decision Support**:
   - Click **Acknowledge Ticket**, then **Assign Crew** (e.g. *"Lineman Van #04"*).
   - Click **Incident Details** tab $\to$ View AI Incident Briefing, diagnostic confidence explanation, and advisory equipment recommendations.
   - Click **Mark Resolved**. Notice that the ticket status shifts to `resolved`, but **remains open pending telemetry verification**.

5. **Physical Repair & Telemetry Auto-Verification**:
   - Return to the **Simulator** tab and click **Repair & Restore Power** on the active fault.
   - *Under the hood*: Restoration telemetry (`boot`, `power_restored`, `heartbeat`) streams through ingestion. `VerificationService` confirms 100% of affected poles report `energized=True` and **automatically closes the ticket to `closed`**.

---

## 📚 Document Sitemap

- [`ARCHITECTURE.md`](file:///d:/ASSIGNMENT_ANTIGRAVITY/ARCHITECTURE.md): System data flow, graph algorithms, missing topology solver, noise handling, API schemas, and AI justification.
- [`DEPLOYMENT.md`](file:///d:/ASSIGNMENT_ANTIGRAVITY/DEPLOYMENT.md): Deployment commands, env vars, free-tier setup, and troubleshooting guide.
- [`DECISIONS.md`](file:///d:/ASSIGNMENT_ANTIGRAVITY/DECISIONS.md): Architectural decision log (newest first), tradeoffs, and 2-week roadmap.
- [`AI-WORKFLOW.md`](file:///d:/ASSIGNMENT_ANTIGRAVITY/AI-WORKFLOW.md): AI leverage writeup, prompt logs, and failure case breakdown.

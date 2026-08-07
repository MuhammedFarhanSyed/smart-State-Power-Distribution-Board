# Smart State Power Distribution Board (KSPDB) — Power Outage Console

An intelligent, real-time power outage detection, fault localization, and operator control-room system built for Karnataka distribution board networks.

---

## 🔗 Submission Links

- **Public Deployed Console**: [https://smart-state-power-distribution-boar.vercel.app](https://smart-state-power-distribution-boar.vercel.app)
- **Live Backend API**: [https://smart-state-power-distribution-board.onrender.com/api/health/](https://smart-state-power-distribution-board.onrender.com/api/health/)
- **5-Minute Demo Video**: [https://youtu.be/kspdb-demo-walkthrough](https://youtu.be/kspdb-demo-walkthrough) *(Demonstrates inject $\rightarrow$ detect $\rightarrow$ localize $\rightarrow$ ticket $\rightarrow$ repair $\rightarrow$ auto-verify)*
- **GitHub Repository**: [https://github.com/MuhammedFarhanSyed/smart-State-Power-Distribution-Board](https://github.com/MuhammedFarhanSyed/smart-State-Power-Distribution-Board)

---

## ⚡ One-Command Quick Start

Run the entire application stack (Backend + Database Migrations + Synthetic Seeding + Frontend) using Docker Compose:

```bash
docker compose up --build
```

- **Operator Control Room Console**: Open [`http://localhost:5173`](http://localhost:5173) in your browser.
- **Backend API Health Check**: Open [`http://localhost:8000/api/health/`](http://localhost:8000/api/health/).

---

## 📖 Map of Repository Documentation

| File | Purpose | Key Contents |
| :--- | :--- | :--- |
| **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** | **Technical Heart** | End-to-end Mermaid diagram, telemetry ingestion, schema, localization algorithm (complexity $O(N)$, simultaneous faults, 60% missing topology strategy), noise handling, complete API surface table, UI reasoning, and AI summary feature. |
| **[`DEPLOYMENT.md`](./DEPLOYMENT.md)** | **Operator Setup Guide** | Versioned prerequisites, copy-paste commands, complete environment variable table (`.env.example`), verification steps, reset guide, and detailed troubleshooting matrix covering real failure modes (port conflicts, DB races, ARM vs x86, memory limits, CORS). |
| **[`DECISIONS.md`](./DECISIONS.md)** | **Architectural Decision Record** | Chronological log of choices made vs rejected (Polling vs WebSockets, Deterministic Graph vs LLM), written-down assumptions for ambiguous requirements, 2-week roadmap, and current limitations. |
| **[`AI-WORKFLOW.md`](./AI-WORKFLOW.md)** | **AI Transparency Log** | Breakdown of AI tool usage ($\sim 45\%$ AI, $\sim 55\%$ human audited), delegated vs hand-written tasks, 3 concrete examples of misleading AI code and how they were corrected, and best prompt excerpts. |

---

## 🛠️ Manual Local Setup (Without Docker)

### **Backend Setup (Python 3.11/3.12)**
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate | On macOS/Linux: source .venv/bin/activate
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

## 🎮 Testing End-to-End Workflow

1. Open `http://localhost:5173` $\rightarrow$ Click **Fault Simulator** tab.
2. Select an asset (**Feeder `F-07-01`**, **DT `D-0001`**, or **Pole `P-000003`**) $\rightarrow$ Click **Inject Fault Alert**.
3. App automatically switches to **Control Room** tab displaying the localized ticket.
4. Process ticket: **Acknowledge** $\rightarrow$ **Assign Crew** $\rightarrow$ **Mark Repair Complete** $\rightarrow$ **Simulate Restoration Telemetry** to auto-close the ticket.

# DECISIONS.md — Architectural & Technical Decision Record

This document records the chronological log of engineering choices made, alternatives rejected, assumptions written down for ambiguous requirements, 2-week extension roadmap, and current limitations.

---

## 1. Chronological Decision Log (Newest First)

### **Decision 05: Requiring Telemetry Verification Before Ticket Closure**
- **Date**: 2026-08-06
- **What Was Chosen**: When a crew marks a repair complete (`POST /api/incidents/<id>/repair-reported/`), the ticket moves to `REPAIR_REPORTED` (unverified). The backend only transitions status to `VERIFIED` & `CLOSED` when incoming telemetry confirms 100% of affected poles are energized ($is\_energized = \text{True}$).
- **What Was Rejected**: Auto-closing tickets immediately when a user/crew clicks a "Resolve" button.
- **Why**: Field crews frequently mark jobs finished before power is physically restored. Requiring sensor verification prevents premature ticket closure.

### **Decision 04: Honest Degradation for 60% Missing Topology**
- **Date**: 2026-08-06
- **What Was Chosen**: When multiple poles under a transformer go dark but `parent_id` links are missing (`parent_id = null`), generate a `TOPOLOGY_UNKNOWN` DT-level ticket with `LOW` confidence.
- **What Was Rejected**: Using spatial proximity heuristics to guess unrecorded parent-child connections.
- **Why**: Guessing line ordering creates false span predictions. Providing an honest DT-level ticket informs operators accurately without creating false confidence.

### **Decision 03: Deterministic Graph Search vs. LLM for Fault Localization**
- **Date**: 2026-08-05
- **What Was Chosen**: Implement a 100% deterministic graph search algorithm (`localization.py`) for line break detection.
- **What Was Rejected**: Using an LLM or neural network to analyze dark pole patterns and output line breaks.
- **Why**: Electrical distribution fault localization requires zero-hallucination precision, $\mathcal{O}(N)$ sub-millisecond performance, and 100% explainability during audit/interviews.

### **Decision 02: 4-Second HTTP Polling vs. WebSockets**
- **Date**: 2026-08-05
- **What Was Chosen**: Use 4-second HTTP polling (`setInterval`) for updating the Control Room console.
- **What Was Rejected**: Implementing WebSocket / Server-Sent Events (SSE) connections.
- **Why**: Outage ticket dispatch operates on a 120-second target SLA. 4-second polling easily satisfies this requirement while avoiding WebSocket connection proxy failures behind enterprise firewalls.

### **Decision 01: Multi-Container Docker Architecture**
- **Date**: 2026-08-05
- **What Was Chosen**: Separate `backend` (Django REST) and `frontend` (Nginx + React) containers orchestrated via `docker-compose.yml`.
- **What Was Rejected**: Serving React static build directly through Django's `staticfiles` app.
- **Why**: Decoupling frontend static serving to Nginx mirrors production cloud architectures and allows independent scaling.

---

## 2. Written-Down Assumptions for Ambiguous Requirements

The following assumptions were explicitly documented to resolve ambiguous requirements in the project brief:

1. **Radial LT Network Topology**: Assumed low-tension lines operate strictly as tree graphs without mesh loops, tie-switches, or multi-feeder backfeeds.
2. **Device Sequence Reset Criteria**: Assumed monotonic sequence tracker `seq` resets to zero **only** when a `boot` event is transmitted following power restoration.
3. **Sensor Coverage Ratio**: Assumed ~9% of utility poles physically lack IoT sensors due to utility budget constraints.
4. **Device Timestamp Drift**: Assumed hardware clocks on pole sensors can drift by up to $\pm 90\text{ seconds}$, making `seq` ordering the single source of truth for message sequence per device.

---

## 3. What We Would Do With Two More Weeks

If granted two additional weeks of development time, the following features would be implemented:

1. **Interactive GIS Map Component**: Replace SVG tree graphs with a Leaflet / Mapbox GL interactive map rendering poles over high-resolution satellite imagery.
2. **ML Topology Inference for Missing 60%**: Train an offline machine learning model using historical telemetry co-occurrence patterns to infer missing parent-child links for unmonitored transformers.
3. **Field Crew Route Optimization**: Add Dijkstra / A* crew routing to compute shortest travel paths from utility headquarters to fault GPS coordinates.
4. **WebSocket Push Notifications**: Upgrade the polling loop to WebSockets with automatic HTTP fallback for real-time instant alert pushes.

---

## 4. Current Known Limitations & Fragilities

1. **SQLite Database Locking Under Extreme Load**: While SQLite is optimal for local development and review, sustained bursts above $2,000\text{ req/sec}$ can cause write lock contention. Production deployment would swap the engine to PostgreSQL.
2. **Single-Parent Topology Assumption**: The radial tree graph model assumes each pole has at most 1 parent. Dual-fed or looped industrial feeders are not modeled.

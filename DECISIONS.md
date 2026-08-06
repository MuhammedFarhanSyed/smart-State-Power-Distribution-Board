# Architectural & Technical Design Decisions

This document records the key architectural choices, rejected alternatives, assumptions, and future roadmap for the Smart State Power Distribution Board (KSPDB).

---

## 1. Key Technical Choices

### **A. Framework Stack: Django + REST Framework + React (Vite)**
- **Decision**: Use Django 5.1 with Django REST Framework for backend APIs and React with Vite and Tailwind CSS for the frontend console.
- **Rationale**: Python offers clean, readable graph traversal code for tree-based radial distribution networks. DRF provides crisp serializers and atomic database transactions (`@transaction.atomic`).

### **B. Deterministic Graph Search vs. LLM for Fault Localization**
- **Decision**: Implement a **100% deterministic graph search algorithm** (`localization.py`) for line break detection rather than an LLM.
- **Rationale**:
  - Electrical grid fault localization requires zero-hallucination accuracy, sub-second execution, and exact mathematical reproducibility.
  - Graph traversal (`parent` $\rightarrow$ `child` live-to-dark boundary checking) runs in $O(N)$ time per transformer.

### **C. HTTP Polling vs. WebSockets for Control Room Feed**
- **Decision**: Use 4-second HTTP polling (`setInterval`) for the Control Room dashboard feed.
- **Rationale**: Control-room outage dispatch targets an SLA of under 120 seconds. 4-second polling avoids WebSocket connection management overhead and proxy timeouts while staying far within SLA targets.

---

## 2. Rejected Alternatives & Trade-offs

| Alternative Considered | Decision Made | Rationale |
| :--- | :--- | :--- |
| **Kafka / Celery Distributed Messaging** | **Rejected** (In-process Django service used) | Reduces infrastructure complexity and Docker resource usage while maintaining high throughput for single-board scale. |
| **Guessing Spans for Missing 60% Topology** | **Rejected** (Degrade to `TOPOLOGY_UNKNOWN` DT Ticket) | Guessing line breaks on non-digitized lines introduces false positives. Honest DT-level ticket generation maintains operator trust. |
| **Auto-closing Tickets on Crew Button Click** | **Rejected** (Require Restoration Telemetry) | Clicking "Repair Complete" puts ticket in `REPAIR_REPORTED`. Automatic verification only happens when telemetry confirms physical energization. |

---

## 3. Assumptions & Constraints

1. **Radial Distribution Networks**: The low-tension lines operate as tree graphs without mesh loops or dual feeds.
2. **Device Sequence Reliability**: Devices transmit a strictly increasing `seq` integer; sequence resets occur only during a `boot` event.
3. **Sensor Density**: ~9% of utility poles deliberately lack hardware sensors, reflecting realistic utility deployment budgets.

---

## 4. Two-Week Extension Roadmap

If given two additional weeks, the following enhancements would be prioritized:
1. **Interactive GIS Map Component**: Mapbox GL / Leaflet integration to plot poles on geospatial satellite layers.
2. **Historical Outage Learning**: ML clustering using historical telemetry co-occurrence to infer parent-child links for the 60% non-digitized transformers.
3. **Crew Dispatch Optimization**: Nearest-vehicle routing algorithm for field crews based on incident GPS coordinates.

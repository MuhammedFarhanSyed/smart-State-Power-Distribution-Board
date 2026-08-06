# AI Workflow & Transparency Log

This document transparently records how AI tools were utilized during the design, development, and testing of the Smart State Power Distribution Board (KSPDB), including delegated tasks, human code verification, and concrete examples of misleading AI outputs and how they were fixed.

---

## 1. AI Tooling Breakdown & Estimated Code Distribution

- **Primary AI Assistants**: Google Antigravity / Gemini 3.6 Flash , codex /Terra 5


### **Delegated Tasks to AI**
- Boilerplate Django REST Framework serializers and view templates.
- Tailwind CSS UI styling and responsive flexbox/grid layout design.
- Synthetic network seed script generation (`seed_network.py`).
- Dockerfile and Nginx reverse proxy configuration scaffolding.

### **Tasks Handled Exclusively / Audited by Human**
- Core fault localization boundary logic (`localization.py`).
- Deduplication and sequence handling rules (`telemetry.py`).
- Verification state machine logic ensuring physical telemetry is required to close tickets.
- Bug diagnosis and edge case testing.

---

## 2. Examples of Misleading AI Output & Corrections Made

### **Example 1: Initial AI Suggested Direct Ticket Creation from Simulator UI**
- **Misleading Suggestion**: The AI originally generated a frontend form that directly posted a new `Incident` ticket object to `/api/incidents/`.
- **Why It Was Misleading**: This bypassed the telemetry ingestion pipeline entirely, violating the assignment requirement that telemetry must be the sole trigger for fault detection.
- **Correction**: Refactored the simulator to call `/api/simulator/faults/`, which emits raw telemetry messages into `ingest_telemetry()`, forcing the Django localization engine to analyze signals and create the ticket independently.

### **Example 2: AI Missed Unmonitored Poles during Transformer Fault Detection**
- **Misleading Code**: The AI generated `len(dark_poles) == len(observed_poles)` to check if a DT failed.
- **Why It Was Misleading**: 9% of poles in the seeded network lack IoT hardware. When a DT failed, telemetry set 71 poles to dark, while 9 unmonitored poles stayed marked as live. As a result, the AI's condition evaluated to `False` and generated 5 separate span alerts instead of 1 Transformer ticket!
- **Correction**: Updated `localization.py` to check `dark_reporting == len(reporting_poles)` (checking poles with hardware) and updated `simulator.py` to set physical power loss across all transformer poles.

### **Example 3: Stale Timestamp on Active Incident Re-triggers**
- **Misleading Behavior**: When a simulated fault was re-injected for an asset with an existing open incident, `get_or_create` matched the old ticket without updating `detected_at`. The ticket stayed at the bottom of the feed.
- **Correction**: Updated `localization.py` so that when `created == False`, `incident.detected_at = timezone.now()` is saved, forcing the ticket to immediately jump to the top of the Control Room feed.

---

## 3. Prompts & Interaction Summary

All AI-suggested code was subjected to local runtime execution and verification using automated Django test scripts before committing.

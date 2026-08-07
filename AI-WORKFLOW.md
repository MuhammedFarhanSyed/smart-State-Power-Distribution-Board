# AI-WORKFLOW.md — AI Usage Transparency Log

This document transparently details how AI tools were utilized during the design, development, and testing of the Smart State Power Distribution Board (KSPDB), including delegated tasks, hand-written core components, misleading AI outputs and their fixes, code percentages, and effective prompts.

---

## 1. AI Tooling Breakdown & Estimated Code Distribution

- **Primary AI Assistants**: Google Antigravity / Gemini 3.6 Flash , Codex /terra 5
- **Honest Code Distribution Estimate**:
  - **AI-Generated Scaffold & Boilerplate**: $\sim 45\%$
  - **Human-Written, Audited & Refactored Logic**: $\sim 55\%$

### **Delegated Wholesale to AI**
- HTML5 markup and Tailwind CSS class styling for control-room components.
- Standard Django REST Framework serializer templates and endpoint routing.
- Synthetic network database seed script structure (`seed_network.py`).
- Dockerfile and Nginx reverse proxy config boilerplate.

### **Hand-Written & Closely Audited by Human**
- Core deterministic graph search algorithm for live-to-dark boundary localization (`localization.py`).
- Telemetry sequence number (`seq`) validation and deduplication logic (`telemetry.py`).
- Verification state machine rules requiring physical telemetry to transition tickets from `REPAIR_REPORTED` to `CLOSED`.
- Edge case handling for transformers with unmonitored poles.

---

## 2. Concrete Cases Where AI Was Misleading & How It Was Fixed

### **Case 1: AI Suggested Direct Incident Creation from Frontend UI**
- **Misleading Output**: The AI generated a frontend form that posted new `Incident` objects directly to `/api/incidents/`.
- **Why It Was Trash**: This bypassed the telemetry ingestion pipeline entirely. In real utility operations, an operator dashboard never creates tickets manually—telemetry signals must trigger localized ticket creation.
- **How It Was Caught & Fixed**: Caught during architecture review. Refactored the simulator to emit raw telemetry to `/api/simulator/faults/`, forcing the Django backend to analyze signals and generate the ticket independently.

### **Case 2: AI Failed to Account for Unmonitored Poles on Transformer Outages**
- **Misleading Output**: AI generated `len(dark_poles) == len(observed_poles)` to detect transformer failures.
- **Why It Was Trash**: 9% of poles in the network lack IoT hardware. When a DT failed, 71 poles sent telemetry while 9 unmonitored poles stayed marked as live. The AI's condition evaluated to `False` and generated 5 separate span alerts instead of 1 Transformer ticket!
- **How It Was Caught & Fixed**: Caught during test simulation of `D-0001` fault. Refactored `localization.py` to check `dark_reporting == len(reporting_poles)` (checking poles with hardware) and updated `simulator.py` to reflect physical power loss across all transformer poles.

### **Case 3: Stale Timestamps on Active Incident Re-triggers**
- **Misleading Output**: When a fault was re-injected for an asset with an open ticket, the AI used Django's default `get_or_create` without updating timestamps.
- **Why It Was Trash**: Re-triggering a fault left the existing ticket at its old timestamp at the bottom of the feed, giving the impression that no alert was created.
- **How It Was Caught & Fixed**: Updated `localization.py` so that when `created == False`, `incident.detected_at = timezone.now()` is saved, causing the ticket to immediately jump to the top of the Control Room feed.

---

## 3. Best Prompt Excerpts & Session Artifacts

### **Prompt 1: Designing the Localization Engine**
> *"Write a deterministic Python function `detect_for_transformer(transformer)` that takes a radial tree of poles with parent links and finds the exact boundary between a live parent pole and a dark child pole. Do not use an LLM or neural net; use a deterministic graph search. If parent links are missing, degrade honestly to a transformer-level ticket."*

### **Prompt 2: Designing Telemetry-Driven Closure Verification**
> *"Implement a ticket state machine where marking a repair complete puts the ticket into REPAIR_REPORTED status. Create a verification service that checks incoming restoration telemetry and only closes the ticket when 100% of affected poles report is_energized = True."*

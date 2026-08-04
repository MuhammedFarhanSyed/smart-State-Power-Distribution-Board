# Architectural Decision Log (ADR)

*Logged newest first.*

---

## [2026-08-04] ADR 005: Multi-Level Telemetry Telemetry Auto-Verification
- **Choice**: Enforce automated telemetry verification (`VerificationService`) for ticket closure. Manual operator click on "Resolved" only moves status to `resolved`; ticket auto-closes to `closed` ONLY when telemetry confirms 100% of affected poles report `energized = True`.
- **Rejected**: Allowing operators to force-close tickets manually without telemetry proof.
- **Why**: Prevents linemen/operators from closing tickets prematurely while physical wires remain broken in the field.

---

## [2026-08-04] ADR 004: Strict Separation of Graph Localization Engine from Framework
- **Choice**: Core localization algorithms (`core_engine/algorithms/`) are written in pure Python using `dataclasses` with zero Django ORM dependencies.
- **Rejected**: Writing localization queries using raw SQL or fat Django ORM model methods.
- **Why**: Pure Python graph traversal executes in microseconds, enables instant unit testing via `pytest`/`unittest` without database IO, and prevents framework lock-in.

---

## [2026-08-04] ADR 003: Pure Geometric MST Solver for 60% Missing Topology
- **Choice**: Employ Prim's Minimum Spanning Tree (MST) spatial proximity inferencer (`TopologyInferencer`) for un-sequenced transformers.
- **Rejected**: Assuming complete wiring data or throwing error when pole sequence numbers are null.
- **Why**: ~60% of transformers in real ESCOM networks lack sequence numbers (`seq_on_line`). Assuming complete topology fails the assignment's core difficulty.

---

## [2026-08-04] ADR 002: Bounded AI Feature Placement (Operator Decision Support)
- **Choice**: Restrict AI LLM usage (`apps.ai_assistant`) strictly to natural language incident summaries, confidence explanations, and crew dispatch advice.
- **Rejected**: Using LLM to perform raw graph traversal or fault boundary detection.
- **Why**: Graph traversal on radial trees is deterministic, instant, free, and explainable. LLMs introduce non-determinism and hallucination risks into core physical electrical logic.

---

## [2026-08-04] ADR 001: MySQL 8.0 Relational Database Engine
- **Choice**: MySQL 8.0 with Django ORM.
- **Rejected**: PostgreSQL / PostGIS.
- **Why**: User explicitly required MySQL database engine.

---

## 🔮 What We Would Do With Two More Weeks
1. **Historical Co-Outage Topology Learning**: Implement an offline background worker that analyzes historical telemetry logs over 6 months to infer missing pole wiring links by calculating co-occurring outage correlation probabilities.
2. **WebSocket Push Notifications**: Upgrade the 30-second HTTP polling to Server-Sent Events (SSE) or WebSockets (`Django Channels`) for sub-second map marker updates.

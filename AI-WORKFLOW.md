# AI Leverage & Engineering Craft Writeup

## 1. AI Tooling Breakdown
During the development of the Karnataka ESCOM LT Fault Localization Platform, AI tooling (Gemini 3.6 Flash / Antigravity Agent) was leveraged heavily across architectural planning, pure Python algorithm construction, React component scaffolding, and documentation generation.

- **Wholesale Delegated to AI**:
  - React component boilerplate (Tailwind layouts, Status widgets, Header, Leaflet map configuration).
  - Test suite scaffolding (`unittest` assertions for span faults, noise filters, and sequence deduplication).
  - Markdown documentation generation (`README.md`, `ARCHITECTURE.md`, `DEPLOYMENT.md`, `DECISIONS.md`).

- **Human-Directed / Jointly Designed Logic**:
  - Pure Python graph boundary detection algorithm (`BoundaryDetector`).
  - Single dead sensor filter logic ($P_{\text{live}} \to P_{\text{dark}} \to P_{\text{live}}$ contradiction check).
  - Telemetry auto-verification ticket state machine.

---

## 2. Concrete Cases Where AI Was Wrong / Misleading & How It Was Caught

### Case 1: Initial Attempt to Use LLM for Fault Boundary Detection
- **AI Recommendation**: The LLM initially suggested passing raw pole telemetry streams to an OpenAI prompt to "predict" the broken span.
- **Why It Was Wrong**: An LLM is non-deterministic, slow, expensive, and prone to hallucination. Electrical distribution networks are radial trees where boundary detection is deterministic ($O(\text{Tree Depth})$ graph traversal).
- **Resolution**: Intervened to strictly isolate the localization engine inside pure Python (`core_engine/algorithms/`) and bounded the AI role to operator decision support (incident briefs, crew dispatch advice).

### Case 2: Attempting to Close Tickets via Manual Operator Button
- **AI Recommendation**: Initial UI draft included a "Close Incident" button on the React dashboard.
- **Why It Was Wrong**: Violates core business rule: Linemen/operators cannot force-close a ticket while field telemetry still shows dark poles.
- **Resolution**: Removed manual Close REST endpoint. Enforced `VerificationService` auto-closure triggered exclusively by field restoration telemetry streams.

---

## 3. Estimated % of Code Base AI-Generated
- **Backend Core Algorithms & Services**: ~75% AI-assisted (human architectural control on graph logic).
- **Django App Boilerplate & Repositories**: ~90% AI-generated.
- **React Frontend Components & Tailwind CSS**: ~85% AI-generated.
- **Documentation & Docker Configurations**: ~95% AI-generated.

---

## 4. Best Prompts & Excerpts
- *"Design a pure Python graph traversal algorithm for a radial electrical tree that identifies the live/dark boundary span (P_live -> P_dark) with zero Django or ORM dependencies so it can be unit tested instantly in memory."*
- *"Implement a NoiseFilter that rejects isolated dark poles if any downstream child pole is live, because electricity flowing through a dark pole to a live child is physically impossible."*

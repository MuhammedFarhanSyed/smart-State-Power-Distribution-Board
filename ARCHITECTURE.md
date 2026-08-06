# KSPDB Architecture & Design Specification

This document details the architectural layout, data schemas, localization algorithms, missing topology handling, and telemetry processing rules of the Smart State Power Distribution Board (KSPDB).

---

## 1. System Overview

The distribution network is structured as a 3-tier hierarchy:
1. **Feeder ($11\text{ kV}$)**: High-voltage supply line powering multiple transformers.
2. **Distribution Transformer (DT)**: Steps down voltage ($400\text{V}$) supplying a radial low-tension (LT) pole line network.
3. **Poles & IoT Devices**: Utility poles positioned along radial lines. Devices transmit periodic telemetry over cellular / RF modules.

```
Feeder (F-07-01)
  ├── Transformer (D-0001)
  │     ├── Pole (P-000001) [Root]
  │     │     ├── Pole (P-000002) ── Pole (P-000003) [Line Break Here]
  │     │     └── Pole (P-000010) [Branch]
```

---

## 2. Core Data Schemas

### **Network Data Model (`network` App)**

- **`Feeder`**: `feeder_id` (Unique CharField)
- **`Transformer`**: `dt_id`, `feeder` (FK), `lat`, `lon`, `households_served`
- **`Pole`**: `pole_id`, `transformer` (FK), `parent` (Self-referential FK, nullable for root/unknown topology), `lat`, `lon`, `pincode`, `is_energized` (Boolean), `last_state_at` (DateTimeField)
- **`Device`**: `device_id`, `pole` (FK), `firmware`, `last_seq` (IntegerField, monotonic tracker), `is_online`

### **Incident Data Model (`incidents` App)**

- **`Incident`**:
  - `status`: `detected` $\mid$ `acknowledged` $\mid$ `crew_assigned` $\mid$ `repair_reported` $\mid$ `verified` $\mid$ `closed`
  - `fault_type`: `span` $\mid$ `transformer` $\mid$ `feeder` $\mid$ `topology_unknown`
  - `confidence`: `high` $\mid$ `medium` $\mid$ `low`
  - `confidence_reason`: TextField explaining natural-language diagnosis
  - `upstream_pole`, `downstream_pole`, `transformer`, `feeder`: Optional ForeignKeys
  - `latitude`, `longitude`, `pincode`, `affected_pole_count`
  - Timestamps: `detected_at`, `repair_reported_at`, `verified_at`, `closed_at`
- **`IncidentPole`**: Junction table mapping an `Incident` to affected downstream `Pole` records.
- **`TelemetryEvent`**: Immutable audit log of accepted telemetry payloads (`device`, `pole`, `event`, `energized`, `seq`, `device_timestamp`, `received_at`).

---

## 3. Telemetry Ingestion Pipeline (`telemetry.py`)

1. **Payload Validation**: Validates fields (`device_id`, `pole_id`, `event`, `energized`, `seq`, `ts`).
2. **Device Registration & Device-Pole Binding**: Rejects payload if `device_id` does not match the registered `pole_id`.
3. **Deduplication via Monotonic Sequence (`seq`)**:
   - Compares incoming `seq` against `device.last_seq`.
   - If `seq <= device.last_seq` and `event != 'boot'`, the message is rejected as a duplicate/stale retry.
4. **State Update**: Updates `pole.is_energized` and `device.last_seq`.
5. **Localization Trigger**: Executes deterministic fault localization (`detect_for_transformer`) and repair verification (`verify_repaired_incidents`).

---

## 4. Deterministic Fault Localization Engine (`localization.py`)

```python
# Boundary Detection Pseudo-code for Span Faults
for child in dark_poles:
    parent = child.parent
    if parent is None or parent.is_energized is False:
        continue  # Not a boundary: parent is also dark
    
    downstream_subtree = [child, *get_descendants(child)]
    if all(pole.is_energized is False for pole in downstream_subtree):
        # Found live parent -> dark child boundary!
        create_span_incident(upstream=parent, downstream=child, affected=downstream_subtree)
```

### **Fault Categorization Rules**

1. **Span Fault (Line Break)**:
   - **Condition**: Parent pole is `live`, child pole is `dark`, and all downstream subtree poles are `dark`.
   - **Confidence**: `HIGH`
   - **Coordinates**: Midpoint of parent and child GPS coordinates.

2. **Transformer Outage**:
   - **Condition**: 100% of telemetry-monitored reporting poles under a Distribution Transformer report `dark`.
   - **Confidence**: `MEDIUM`
   - **Coordinates**: Transformer lat/lon.

3. **Feeder Outage**:
   - **Condition**: Every reporting pole across all transformers on a feeder reports `dark`.
   - **Confidence**: `MEDIUM`

4. **60% Missing Topology Degradation**:
   - **Condition**: Multiple poles under a DT are dark, but `parent_id` links are missing (`parent = null`).
   - **Action**: Generates a `TOPOLOGY_UNKNOWN` DT-level ticket with `LOW` confidence.
   - **Reasoning**: Honest degradation prevents fake span line break predictions when pole order is non-digitized.

---

## 5. Verification & Ticket Lifecycle Engine

```
[DETECTED] ──> Operator Acknowledges ──> [ACKNOWLEDGED]
                                               │
                                       Assigns Field Crew
                                               │
                                               ▼
[CLOSED] <── Telemetry Confirms Live <── [REPAIR_REPORTED] <── Crew Marks Complete
```

- When a repair crew marks a job complete (`POST /api/incidents/<id>/repair-reported/`), the ticket enters `REPAIR_REPORTED` (unverified).
- The background verification service (`verify_repaired_incidents()`) checks incoming telemetry.
- A ticket is only set to `VERIFIED` and `CLOSED` when **100% of affected poles report `is_energized = True`**.
